"""
Fetches raw course/doc pages from configured sources. ONLY job: HTML -> clean text.
No chunking/embedding here — see ingestion.py for that.
"""
import requests
from bs4 import BeautifulSoup


def scrape_page(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
