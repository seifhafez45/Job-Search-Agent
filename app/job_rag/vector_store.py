"""Uses the shared Chroma wrapper (career_rag/vector_store.py) with its OWN collection name."""
from app.career_rag.vector_store import upsert, query

COLLECTION_NAME = "job_postings"

__all__ = ["upsert", "query", "COLLECTION_NAME"]
