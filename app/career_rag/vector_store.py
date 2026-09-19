"""
Thin wrapper around Chroma (local persistent vector DB). ONLY job: upsert/query
vectors. Both career_rag and job_rag use this module with different collection names.
"""
import chromadb

from app.config import settings

_client = chromadb.PersistentClient(path=settings.vector_db_path)


def get_collection(name: str):
    return _client.get_or_create_collection(name)


def upsert(collection_name: str, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    collection = get_collection(collection_name)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def query(collection_name: str, query_embedding: list[float], top_k: int = 5):
    collection = get_collection(collection_name)
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)
