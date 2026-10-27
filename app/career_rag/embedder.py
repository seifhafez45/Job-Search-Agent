"""Wraps the sentence-transformers model. ONLY job: text -> vector. Reused by ingestion.py and retriever.py."""
from sentence_transformers import SentenceTransformer

from app.config import settings

_model = None


def _get_model() -> SentenceTransformer:
    # Lazy-loaded so importing this module (and anything that imports it) never
    # triggers a model download by itself — only the first real embed call does.
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_text(texts: list[str]) -> list[list[float]]:
    # Rely on the default convert_to_numpy=True so this always returns a
    # numpy array (guaranteed to have .tolist()). With convert_to_numpy=False,
    # some sentence-transformers versions return a plain Python list instead
    # of an array/tensor, which doesn't have .tolist() and crashes here.
    return _get_model().encode(texts).tolist()
