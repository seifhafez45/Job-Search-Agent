"""Unit tests for app/career_rag/: chunking logic in ingestion.py, retriever.py query shape (vector store mocked)."""
from app.career_rag.ingestion import _chunk_text
from app.career_rag import retriever


def test_chunk_text_shorter_than_chunk_size_returns_one_chunk():
    text = "short text"
    chunks = _chunk_text(text, chunk_size=800, overlap=100)
    assert chunks == [text]


def test_chunk_text_never_splits_a_word():
    text = " ".join(f"word{i}" for i in range(300))  # realistic, space-separated
    chunks = _chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    original_words = set(text.split())
    for chunk in chunks:
        assert len(chunk) <= 120
        for word in chunk.split():
            assert word in original_words  # never a fragment of a word


def test_chunk_text_overlap_repeats_trailing_words():
    text = " ".join(f"word{i}" for i in range(300))
    chunks = _chunk_text(text, chunk_size=120, overlap=20)
    for prev_chunk, next_chunk in zip(chunks, chunks[1:]):
        prev_words = prev_chunk.split()
        next_words = next_chunk.split()
        # overlap can carry more than one trailing word depending on word
        # lengths, so check the next chunk starts with one of the previous
        # chunk's trailing words, not an exact single-word handoff.
        assert next_words[0] in prev_words[-5:]


def test_chunk_text_covers_every_word_at_least_once():
    text = " ".join(f"word{i}" for i in range(300))
    chunks = _chunk_text(text, chunk_size=120, overlap=20)
    seen = {word for chunk in chunks for word in chunk.split()}
    assert set(text.split()) <= seen


def test_chunk_text_handles_a_single_unbroken_token_longer_than_chunk_size():
    text = "x" * 1000  # no spaces at all, e.g. a long URL
    chunks = _chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) == 2
    assert all(len(c) <= 800 for c in chunks)
    assert "".join(chunks) == text  # no overlap applies to an unsplittable token; just covers it


def test_retrieve_relevant_chunks_returns_documents(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": [["chunk a", "chunk b"]]},
    )
    result = retriever.retrieve_relevant_chunks("what should I study?", top_k=2)
    assert result == ["chunk a", "chunk b"]


def test_retrieve_relevant_chunks_handles_empty_results(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": []},
    )
    result = retriever.retrieve_relevant_chunks("anything")
    assert result == []


def test_retrieve_resources_pairs_chunks_with_source_urls(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {
            "documents": [["chunk a", "chunk b"]],
            "metadatas": [[{"source_url": "https://a.example"}, {"source_url": "https://b.example"}]],
        },
    )
    result = retriever.retrieve_resources("system design")
    assert result == [
        {"excerpt": "chunk a", "source_url": "https://a.example"},
        {"excerpt": "chunk b", "source_url": "https://b.example"},
    ]


def test_retrieve_resources_handles_empty_results(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": []},
    )
    result = retriever.retrieve_resources("anything")
    assert result == []
