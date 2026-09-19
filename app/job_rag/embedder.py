"""
Separate from career_rag/embedder.py on purpose: job postings churn daily and
may warrant a different refresh cadence / model later. Currently delegates to
the same underlying model to avoid duplicate loading.
"""
from app.career_rag.embedder import embed_text  # re-used intentionally; swap independently later if needed

__all__ = ["embed_text"]
