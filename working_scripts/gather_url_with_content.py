import chromadb
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import hashlib

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./myhead")
collection = chroma_client.get_or_create_collection(name="cyber_threats")

def canonicalize_url(url: str) -> str:
    """
    Return a canonical version of the URL by stripping out the fragment.
    This makes URLs with different fragments (e.g. "#comments") identical.
    """
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()

def generate_id(url: str) -> str:
    """Generate a unique ID based solely on the canonicalized URL."""
    canonical = canonicalize_url(url)
    return hashlib.md5(canonical.encode('utf-8')).hexdigest()

def is_new_report(url: str) -> bool:
    """Check if the report (identified by its canonical URL) is not already stored."""
    report_id = generate_id(url)
    existing = collection.get()
    if "ids" not in existing:
        return True
    return report_id not in existing["ids"]

def is_article_link(url: str) -> bool:
    """
    Determines if a URL likely belongs to an article based on a date pattern (/YYYY/MM/)
    and excludes common non-article paths.
    """
    canonical = canonicalize_url(url)
    parsed_url = urlparse(canonical)
    path = parsed_url.path.lower()
    date_pattern = re.compile(r"/\d{4}/\d{2}/")
    excluded_keywords = ["/category/", "/tag/", "/author/", "/about", "/contact", "/faq", "/page/"]
    if not date_pattern.search(path):
        return False
    if any(kw in path for kw in excluded_keywords):
        return False
    return True

def fetch_article_content(url: str) -> str:
    """
    Fetches the article's main content from the given URL.
    Tries to extract text from an <article> tag or a div with class "blog-content".
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article") or soup.find("div", class_="blog-content")
        if article:
            paragraphs = article.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paragraphs)
            return content
        return ""
    except Exception as e:
        print(f"Error fetching article content from {url}: {e}")
        return ""

def store_report(title: str, url: str, content: str):
    """
    Store the blog post in ChromaDB.
    The unique id is based on the canonical URL so that different fragments are treated the same.
    A new metadata field "processed" is added (default False) to flag further processing.
    """
    canonical = canonicalize_url(url)
    report_id = generate_id(canonical)
    collection.add(
        ids=[report_id],
        documents=[content],
        metadatas=[{"title": title, "url": canonical, "processed": False}]
    )
    print(f"✅ Stored: {title} → {canonical}")

def find_next_page(soup, current_url):
    """
    Searches for a 'next' page link that is:
      - Labeled with candidate texts (e.g., "next", "older posts", or "›")
      - On the same domain as the current page,
      - And contains '/page/' in its URL.
    """
    candidate_texts = re.compile(r"(next|older posts|›)", re.IGNORECASE)
    current_domain = urlparse(current_url).netloc
    candidates = soup.find_all("a", text=candidate_texts)
    for link in candidates:
        href = link.get("href")
        if not href:
            continue
        next_url = urljoin(current_url, href)
        if urlparse(next_url).netloc != current_domain:
            continue
        if "/page/" in next_url:
            return next_url
    return None

def scrape_page(url):
    """
    Scrapes a single page for article links, fetches their content,
    and stores new articles (only if the canonical URL is not already stored).
    Returns the next page URL if available.
    """
    try:
        print(f"🔍 Scraping: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Skipping {url} (HTTP {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        posts_found = 0

        for link in soup.find_all("a", href=True):
            full_link = urljoin(url, link["href"])
            title = link.get_text(strip=True)
            if title and is_article_link(full_link) and is_new_report(full_link):
                content = fetch_article_content(full_link)
                if not content:
                    content = title  # Fallback if no content is fetched
                store_report(title, full_link, content)
                posts_found += 1

        print(f"Found {posts_found} posts on page: {url}")
        next_page = find_next_page(soup, url)
        if next_page:
            print(f"Next page found: {next_page}")
        else:
            print("No next page found.")
        return next_page

    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
        return None

def scrape_all_pages(start_url):
    """
    Dynamically scrapes pages by following the 'next' link until no valid
    pagination link is found, while avoiding infinite loops.
    """
    current_url = start_url
    page_count = 0
    visited_pages = set()

    while current_url and page_count < 7:
        if current_url in visited_pages:
            print("⚠️ Already visited page, stopping to avoid infinite loop:", current_url)
            break
        visited_pages.add(current_url)
        next_url = scrape_page(current_url)
        page_count += 1
        time.sleep(1)  # Delay to reduce the chance of rate limiting
        if next_url in visited_pages:
            print("⚠️ Next page already visited, stopping pagination.")
            break
        current_url = next_url

    print(f"✅ Finished scraping {page_count} pages.")

def get_unprocessed_articles():
    """
    Retrieves all articles from the collection where metadata 'processed' is False.
    
    Returns:
        list of dict: Each dictionary contains the article's id, content, and metadata.
    """
    # Query the collection using a where filter on the 'processed' field
    result = collection.get(where={"processed": False})
    
    # Create a list of articles with all the fields
    articles = []
    if result and "ids" in result:
        for idx, article_id in enumerate(result["ids"]):
            articles.append({
                "id": article_id,
                "content": result["documents"][idx],
                "metadata": result["metadatas"][idx]
            })
    return articles


# Start scraping from the first page
start_url = "https://krebsonsecurity.com/"
scrape_all_pages(start_url)

unprocessed = get_unprocessed_articles()
for article in unprocessed:
    print("ID:", article["id"])
    print("Content:", article["content"])
    print("Metadata:", article["metadata"])
    print("-" * 40)