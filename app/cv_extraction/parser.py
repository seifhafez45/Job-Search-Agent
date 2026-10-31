import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError
import docx


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from PDF or DOCX files.
    This function only handles file parsing.
    No LLM calls or data interpretation.
    """

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    if not filename:
        raise ValueError("Filename is missing.")

    extension = filename.lower().rsplit(".", 1)[-1]

    try:
        # PDF Parsing
        if extension == "pdf":
            reader = PdfReader(io.BytesIO(file_bytes))

            if reader.is_encrypted:
                raise ValueError("Password-protected PDF files are not supported.")

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        # DOCX Parsing
        elif extension == "docx":
            document = docx.Document(io.BytesIO(file_bytes))

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        else:
            raise ValueError(
                f"Unsupported file format: .{extension}"
            )

    except PdfReadError as e:
        raise ValueError(f"Could not read PDF file: {e}")

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"File parsing failed: {e}")

    if not text.strip():
        raise ValueError(
            "No readable text found in the uploaded file."
        )

    return text.strip()
