import chromadb
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import os
import re

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./myhead")
collection = chroma_client.get_or_create_collection(name="cyber_threats")


def is_new_report(title: str) -> bool:
	existing = collection.get()
	if "ids" not in existing:
		return True
	return title not in existing["ids"]


def is_article_link(url: str) -> bool:
	"""Filters URLs to detect blog posts or articles using date patterns."""
	parsed_url = urlparse(url)
	path = parsed_url.path.lower()

	# Regular expression to match a year/month format in the URL (YYYY/MM or YYYY-MM)
	date_pattern = re.compile(r"/\d{4}/\d{2}/")  # Matches /2025/02/ or /2024-10/
	
	# Exclude common non-article paths
	excluded_keywords = ["/category/", "/tag/", "/author/", "/page/", "/about", "/contact", "/faq"]

	# Check if URL contains a date pattern (YYYY/MM) and is not an excluded section
	return bool(date_pattern.search(path)) and not any(kw in path for kw in excluded_keywords)


def store_report(title: str, url: str):
	collection.add(
		ids=[title],
		documents=[""],  # No content storage
		metadatas=[{"title": title, "url": url}]
	)
	print(f"✅ Stored: {title}, url: {url}")


def scrape_page(url):
	"""Extract potential blog/article titles and URLs."""
	try:
		print(f"🔍 Scraping: {url}")
		headers = {"User-Agent": "Mozilla/5.0"}
		response = requests.get(url, headers=headers, timeout=10)
		if response.status_code != 200:
			return None

		soup = BeautifulSoup(response.text, "html.parser")

		for link in soup.find_all("a", href=True):
			full_link = urljoin(url, link["href"])
			title = link.get_text(strip=True)

			if title and is_article_link(full_link) and is_new_report(title):
				store_report(title, full_link)

	except Exception as e:
		print(f"❌ Error scraping {url}: {str(e)}")


def scrape_websites():
	"""Reads URLs from `websites.txt`, extracts only titles and URLs, and stores them."""
	if not os.path.exists("websites.txt"):
		print("❌ websites.txt file not found!")
		return

	with open("websites.txt", "r") as file:
		websites = [line.strip() for line in file.readlines()]

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		executor.map(scrape_page, websites)

	print("✅ Scraping complete.")

scrape_websites()
