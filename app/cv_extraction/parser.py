"""
Raw file -> plain text ONLY (PDF/DOCX parsing). No LLM calls and no database
access here: this module answers one question, "what text is inside this file?".
"""
import io
import logging
import zipfile
from pathlib import PurePath

import docx
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from app.cv_extraction.errors import EmptyCVError, UnsupportedFileError
from app.common.exceptions import ExtractionError

logger = logging.getLogger(__name__)

# Fewer characters than this almost certainly means a scanned / image-only file.
MIN_TEXT_CHARS = 30


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Return the cleaned text of a PDF or DOCX file.

    Raises:
        UnsupportedFileError: the extension is not .pdf / .docx
        ExtractionError: the file is corrupted, password-protected, etc.
        EmptyCVError: the file opened fine but contains (almost) no text
    """
    suffix = PurePath(filename or "").suffix.lower()

    if suffix == ".pdf":
        text = _read_pdf(file_bytes)
    elif suffix == ".docx":
        text = _read_docx(file_bytes)
    elif suffix == ".doc":
        raise UnsupportedFileError(
            "Legacy .doc files are not supported. Please save the CV as .docx or .pdf."
        )
    else:
        raise UnsupportedFileError(
            "Unsupported resume format. Please upload a PDF or DOCX file."
        )

    text = _clean(text)
    if len(text) < MIN_TEXT_CHARS:
        raise EmptyCVError(
            "No readable text was found in the file. "
            "If it is a scanned image, please upload a text-based PDF or a DOCX."
        )
    return text


def _clean(text: str) -> str:
    # PostgreSQL rejects NUL characters in text columns; PDFs often contain them.
    return text.replace("\x00", "").strip()


def _read_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ExtractionError("The PDF is password-protected and cannot be read.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ExtractionError:
        raise
    except Exception as exc:  # pypdf raises many different error types
        logger.warning("PDF parsing failed: %s", type(exc).__name__)
        raise ExtractionError(
            "The PDF file is corrupted, password-protected, or cannot be read."
        ) from exc


def _read_docx(file_bytes: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        parts: list[str] = []

        # Walk the body in document order so tables stay where they appear.
        # (document.paragraphs alone silently skips every table.)
        for child in document.element.body.iterchildren():
            if child.tag == qn("w:p"):
                parts.append(Paragraph(child, document).text)
            elif child.tag == qn("w:tbl"):
                parts.extend(_table_lines(Table(child, document)))
        return "\n".join(parts)
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        logger.warning("DOCX parsing failed: %s", type(exc).__name__)
        raise ExtractionError(
            "The DOCX file is corrupted or is not a valid Word document."
        ) from exc
    except Exception as exc:
        logger.warning("DOCX parsing failed: %s", type(exc).__name__)
        raise ExtractionError("The DOCX file cannot be read.") from exc


def _table_lines(table: Table) -> list[str]:
    lines: list[str] = []
    for row in table.rows:
        seen: set[int] = set()
        cells: list[str] = []
        for cell in row.cells:
            # Merged cells are repeated by python-docx; keep each only once.
            if id(cell._tc) in seen:
                continue
            seen.add(id(cell._tc))
            value = cell.text.strip()
            if value:
                cells.append(value)
        if cells:
            lines.append(" | ".join(cells))
    return lines
