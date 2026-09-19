"""Wraps the sentence-transformers model. ONLY job: text -> vector. Reused by ingestion.py and retriever.py."""
from sentence_transformers import SentenceTransformer

from app.config import settings

_model = SentenceTransformer(settings.embedding_model)


def embed_text(texts: list[str]) -> list[list[float]]:
    return _model.encode(texts, convert_to_numpy=False).tolist()
