"""
Orchestrates the RAG answer: retriever.py -> LLM synthesis grounded in retrieved chunks.
This is the ONLY module that combines retrieval + generation for career resources.
"""
from app.llm.client import complete
from app.llm.base_prompts import GROUNDING_RULE
from app.career_rag.retriever import retrieve_relevant_chunks

SYSTEM_PROMPT = f"You answer 'what should I study for X' questions using ONLY the provided source excerpts. {GROUNDING_RULE}"


def answer_study_question(question: str) -> dict:
    chunks = retrieve_relevant_chunks(question)
    context = "\n\n---\n\n".join(chunks)
    answer = complete(SYSTEM_PROMPT, f"SOURCE EXCERPTS:\n{context}\n\nQUESTION: {question}")
    return {"answer": answer, "sources_used": len(chunks)}
