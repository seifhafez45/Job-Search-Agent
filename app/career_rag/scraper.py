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
    # resp.content (raw bytes) instead of resp.text: many sites only declare
    # their charset inside the HTML <meta> tag, not the HTTP header, which
    # makes requests' encoding guess wrong and garbles non-ASCII characters
    # (e.g. a non-breaking space becoming "Â "). BeautifulSoup detects
    # encoding from the bytes/meta tags itself, far more reliably.
    soup = BeautifulSoup(resp.content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
