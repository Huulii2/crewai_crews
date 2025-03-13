import chromadb
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import hashlib
import random
import concurrent.futures
import logging
import threading
import urllib.robotparser as robotparser
import requests_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CyberThreatCrawler:
    def __init__(self, start_url, db_path="./db/cyberthreat_reports", max_pages=7, max_workers=10):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.connect_timeout = 10
        self.read_timeout = 20
        self.retries = 5
        self.backoff_factor = 2
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        ]
        self.proxies = []
        self.use_selenium = False
        self.robot_user_agents = "CyberBlogCrawler"
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="reports")
        self.existing = self.collection.get()
        self.add_lock = threading.Lock()
        self.added_ids = set(self.existing["ids"]) if "ids" in self.existing else set()
        self.session = requests.Session()
        self.robot_parsers = {}
        requests_cache.install_cache('cache/crawler_cache', expire_after=3600)
        
    def get_headers_and_proxy(self):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/"
        }
        proxies = None
        if self.proxies != []:
            proxy = random.choice(self.proxies)
            proxies = {"http": proxy, "https": proxy}
        return headers, proxies
    
    def canonicalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed._replace(fragment="").geturl()
    
    def generate_id(self, url: str) -> str:
        canonical = self.canonicalize_url(url)
        return hashlib.md5(canonical.encode('utf-8')).hexdigest()
    
    def allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if base_url not in self.robot_parsers:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base_url, "/robots.txt"))
            try:
                rp.read()
            except Exception as e:
                logging.warning(f"Could not read robots.txt for {base_url}: {e}")
                rp = None
            self.robot_parsers[base_url] = rp
        rp = self.robot_parsers.get(base_url)
        if rp:
            return rp.can_fetch(self.robot_user_agents, url)
        return True
    
    def is_new_report(self, url: str) -> bool:
        report_id = self.generate_id(url)
        return report_id not in self.added_ids
    
    def is_article_link(self, url: str) -> bool:
        canonical = self.canonicalize_url(url)
        parsed = urlparse(canonical)
        path = parsed.path.lower()
        date_pattern = re.compile(r"/\d{4}/\d{2}/")
        excluded_keywords = ["/category/", "/tag/", "/author/", "/about", "/contact", "/faq", "/page/"]
        if not date_pattern.search(path):
            return False
        if any(kw in path for kw in excluded_keywords):
            return False
        return True
    
    def fetch_article_title(self, url: str, retries=None, backoff_factor=None) -> str:
        """
        Fallback function to fetch a better article title from the article page's <title> tag.
        """
        retries = retries if retries is not None else self.retries
        backoff_factor = backoff_factor if backoff_factor is not None else self.backoff_factor
        attempt = 0
        while attempt < retries:
            try:
                headers, proxies = self.get_headers_and_proxy()
                response = self.session.get(url, headers=headers, proxies=proxies,
                                    timeout=(self.connect_timeout, self.read_timeout))
                if response.status_code != 200:
                    return ""
                soup = BeautifulSoup(response.text, "html.parser")
                if soup.title:
                    return soup.title.get_text(strip=True)
                return ""
            except Exception as e:
                logging.error(f"Exception fetching title from {url}: {e}")
                attempt += 1
                time.sleep(backoff_factor ** attempt)
        return ""
    
    def fetch_article_content(self, url: str, retries=None, backoff_factor=None) -> str:
        """
        Fetch the article's main content with retry mechanism.
        Uses a tuple timeout and respects robots.txt.
        """
        if not self.allowed_by_robots(url):
            logging.info(f"Blocked by robots.txt: {url}")
            return ""
        retries = retries if retries is not None else self.retries
        backoff_factor = backoff_factor if backoff_factor is not None else self.backoff_factor
        if self.use_selenium:
            # Selenium integration not included in this final version
            return ""
        attempt = 0
        while attempt < retries:
            try:
                headers, proxies = self.get_headers_and_proxy()
                response = self.session.get(url, headers=headers, proxies=proxies,
                                    timeout=(self.connect_timeout, self.read_timeout))
                if response.status_code != 200:
                    logging.warning(f"Error fetching content from {url}: HTTP {response.status_code}")
                    return ""
                soup = BeautifulSoup(response.text, "html.parser")
                article = soup.find("article") or soup.find("div", class_="blog-content")
                if article:
                    paragraphs = article.find_all("p")
                    content = "\n".join(p.get_text(strip=True) for p in paragraphs)
                    return content
                return ""
            except Exception as e:
                logging.error(f"Exception fetching article content from {url}: {e}")
                attempt += 1
                sleep_time = backoff_factor ** attempt
                logging.info(f"Retrying {url} in {sleep_time} seconds (attempt {attempt}/{retries})...")
                time.sleep(sleep_time)
        return ""
    
    def store_report(self, title: str, url: str, content: str):
        """
        Store the blog post in ChromaDB with metadata.
        Uses a lock and a global duplicate set to prevent duplicate entries.
        """
        canonical = self.canonicalize_url(url)
        report_id = self.generate_id(canonical)
        with self.add_lock:
            if report_id in self.added_ids:
                return
            self.added_ids.add(report_id)
            try:
                self.collection.add(
                    ids=[report_id],
                    documents=[content],
                    metadatas=[{"title": title, "url": canonical, "processed": False}]
                )
                logging.info(f"Stored: {title} → {canonical}")
            except Exception as e:
                logging.error(f"Error storing report {title} from {canonical}: {e}")
                
    def process_article_link(self, link, base_url):
        """
        Process a single article link:
        - Constructs the full URL.
        - Uses the link text as the initial title.
        - If the link text is generic (e.g. too short, or starts with 'comment'/'read more'),
            fetch a better title from the article page.
        - If the link qualifies as an article and is new, fetch its content and store it.
        Returns True if the article was stored.
        """
        full_link = urljoin(base_url, link.get("href"))
        link_title = link.get_text(strip=True)
        title = link_title
        # If the link text is generic, attempt to fetch a better title
        if len(link_title) < 15 or re.search(r"^(comment|read more)", link_title, re.IGNORECASE):
            fetched_title = self.fetch_article_title(full_link)
            if fetched_title:
                title = fetched_title
        try:
            if title and self.is_article_link(full_link) and self.is_new_report(full_link):
                content = self.fetch_article_content(full_link) or title
                self.store_report(title, full_link, content)
                return True
        except Exception as e:
            logging.error(f"Error processing link {full_link}: {e}")
        return False
    
    def scrape_page_and_get_next(self, url):
        """
        Scrapes a page:
        - Processes article links concurrently.
        - Dynamically extracts the next page link.
        Returns the next page URL (or None if not found).
        """
        if not self.allowed_by_robots(url):
            logging.info(f"Disallowed by robots.txt: {url}")
            return None
        try:
            logging.info(f"Scraping: {url}")
            headers, proxies = self.get_headers_and_proxy()
            response = self.session.get(url, headers=headers, proxies=proxies,
                                timeout=(self.connect_timeout, self.read_timeout))
            if response.status_code != 200:
                logging.warning(f"Skipping {url} (HTTP {response.status_code})")
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            posts_found = 0
            links = soup.find_all("a", href=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.process_article_link, link, url) for link in links]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        if future.result():
                            posts_found += 1
                    except Exception as e:
                        logging.error(f"Error in processing future: {e}")
            logging.info(f"Found {posts_found} posts on page: {url}")
            # Dynamically extract the next page link using candidate texts
            candidate_texts = re.compile(r"(next|older posts|›)", re.IGNORECASE)
            current_domain = urlparse(url).netloc
            next_page = None
            for link in soup.find_all("a", text=candidate_texts):
                href = link.get("href")
                if href:
                    potential = urljoin(url, href)
                    if urlparse(potential).netloc == current_domain and "/page/" in potential:
                        next_page = potential
                        break
            if next_page:
                logging.info(f"Next page found: {next_page}")
            else:
                logging.info("No next page found.")
            return next_page
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None
        
    def scrape_all_pages_dynamic(self, start_url=None, max_pages=None):
        """
        Dynamically scrapes pages by following 'next page' links.
        Processes pages concurrently in batches until no new page is found or max_pages is reached.
        """
        max_pages = max_pages if max_pages is not None else self.max_pages
        pages_to_scrape = [start_url] if max_pages is not None else [self.start_url]
        scraped_pages = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while pages_to_scrape and len(scraped_pages) < max_pages:
                futures = {executor.submit(self.scrape_page_and_get_next, url): url for url in pages_to_scrape if url not in scraped_pages}
                pages_to_scrape = []
                for future in concurrent.futures.as_completed(futures):
                    current_url = futures[future]
                    scraped_pages.add(current_url)
                    try:
                        next_page = future.result()
                        if next_page and next_page not in scraped_pages:
                            pages_to_scrape.append(next_page)
                    except Exception as e:
                        logging.error(f"Error scraping page {current_url}: {e}")
        logging.info(f"Finished dynamic pagination scraping of {len(scraped_pages)} pages.")
        
    def get_unprocessed_articles(self):
        """
        Retrieves all articles from the collection where metadata 'processed' is False.
        Returns a list of dictionaries with article id, content, and metadata.
        """
        result = self.collection.get(where={"processed": False})
        articles = []
        if result and "ids" in result:
            for idx, article_id in enumerate(result["ids"]):
                articles.append({
                    "id": article_id,
                    "content": result["documents"][idx],
                    "metadata": result["metadatas"][idx]
                })
        return articles
    
    def mark_article_as_processed(self, article_id):
        """
        Updates the 'processed' field of an article to True in ChromaDB.
        
        :param article_id: The ID of the article to update.
        """
        # Retrieve the current document
        result = self.collection.get(ids=[article_id])

        if not result or "ids" not in result or not result["ids"]:
            print(f"Article {article_id} not found.")
            return

        # Extract existing content and metadata
        idx = result["ids"].index(article_id)
        updated_metadata = result["metadatas"][idx]
        updated_metadata["processed"] = True

        # Re-insert the document with updated metadata
        self.collection.upsert(
            ids=[article_id],
            documents=[result["documents"][idx]],
            metadatas=[updated_metadata]
        )
        print(f"✅ Article {article_id} marked as processed.")

    def get_processed_articles(self):
        """
        Retrieves all articles where metadata 'processed' is True.
        Returns a list of dictionaries with article id, content, and metadata.
        """
        result = self.collection.get(where={"processed": True})  # Query for processed=True

        articles = []
        if result and "ids" in result:
            for idx, article_id in enumerate(result["ids"]):
                articles.append({
                    "id": article_id,
                    "content": result["documents"][idx],
                    "metadata": result["metadatas"][idx]
                })

        return articles  # Return the list of processed articles
