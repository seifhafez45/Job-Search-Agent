"""Query-time retrieval ONLY: embed the question, fetch top-k chunks. No generation here."""
from app.career_rag.embedder import embed_text
from app.career_rag.vector_store import query
from app.career_rag.ingestion import COLLECTION_NAME


def retrieve_relevant_chunks(question: str, top_k: int = 5) -> list[str]:
    query_embedding = embed_text([question])[0]
    result = query(COLLECTION_NAME, query_embedding, top_k)
    return result["documents"][0] if result["documents"] else []
