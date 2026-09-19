"""
Raw file -> plain text ONLY (PDF/DOCX parsing). No LLM calls here —
keeps 'get text out of a file' separate from 'interpret the text'.
"""
import io

from pypdf import PdfReader
import docx


def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif filename.lower().endswith(".docx"):
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)
    raise ValueError(f"Unsupported resume format: {filename}")
