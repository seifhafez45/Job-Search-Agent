"""
Pipeline: source URL -> scraper.py (raw text) -> chunk -> embedder.py -> vector_store.py.
Run via scripts/ingest_career_resources.py, not by the live API (this is a batch/offline job).
"""
import hashlib

from app.career_rag.scraper import scrape_page
from app.career_rag.embedder import embed_text
from app.career_rag.vector_store import upsert

COLLECTION_NAME = "career_resources"


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def ingest_url(url: str, topic_tag: str) -> int:
    """Scrapes, chunks, embeds, and stores one source page. Returns number of chunks stored."""
    text = scrape_page(url)
    chunks = _chunk_text(text)
    ids = [hashlib.sha256(f"{url}-{i}".encode()).hexdigest() for i in range(len(chunks))]
    embeddings = embed_text(chunks)
    metadatas = [{"source_url": url, "topic": topic_tag} for _ in chunks]
    upsert(COLLECTION_NAME, ids, chunks, embeddings, metadatas)
    return len(chunks)
