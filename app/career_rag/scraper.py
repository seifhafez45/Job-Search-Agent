"""
Fetches raw course/doc pages from configured sources. ONLY job: HTML -> clean text.
No chunking/embedding here — see ingestion.py for that.
"""
import requests
from bs4 import BeautifulSoup

# Some sites block requests with no User-Agent (or the default python-requests
# one) as a basic anti-scraping measure; a realistic browser-like header avoids
# that for the plain, publicly-readable article pages this scraper targets.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_page(url: str) -> str:
    resp = requests.get(url, timeout=10, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
