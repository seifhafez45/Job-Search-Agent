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
    """Packs whole words into ~chunk_size-character chunks (never splitting a
    word in half), carrying the trailing ~overlap characters' worth of words
    into the next chunk so retrieved excerpts don't start/end mid-word."""
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        # A "word" with no whitespace of its own (a long URL, an unbroken
        # token) can still exceed chunk_size; word-boundary splitting can't
        # help there, so fall back to a raw character slice for it alone.
        if len(word) > chunk_size:
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            for i in range(0, len(word), chunk_size):
                chunks.append(word[i:i + chunk_size])
            continue

        added_len = len(word) + (1 if current else 0)
        if current and current_len + added_len > chunk_size:
            chunks.append(" ".join(current))
            carry: list[str] = []
            carry_len = 0
            for w in reversed(current):
                if carry_len + len(w) + 1 > overlap:
                    break
                carry.insert(0, w)
                carry_len += len(w) + 1
            current, current_len = carry, carry_len
        current.append(word)
        current_len += added_len

    if current:
        chunks.append(" ".join(current))
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
