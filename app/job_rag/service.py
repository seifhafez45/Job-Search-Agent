"""
STRETCH FEATURE (Phase 7): semantic/loose job search — 'find me something like X'
rather than exact keyword filters. Embeds recent postings (ingested separately,
e.g. by extending job_search/job_api_client.py's results) and ranks by similarity
to the user's free-text query or profile summary.
"""
from app.job_rag.embedder import embed_text
from app.job_rag.vector_store import query, COLLECTION_NAME
from app.schemas.job import JobPosting


def semantic_search(free_text_query: str, top_k: int = 10) -> list[JobPosting]:
    query_embedding = embed_text([free_text_query])[0]
    result = query(COLLECTION_NAME, query_embedding, top_k)
    postings = []
    for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        postings.append(JobPosting(match_score=1 - dist, description=doc, **meta))
    return postings
