"""
Feature-specific exceptions for CV extraction.

Shared exceptions are inherited from app.common.exceptions.
"""

from app.common.exceptions import ExtractionError


class EmptyCVError(ExtractionError):
    """Raised when the uploaded CV contains no readable text."""
    pass


class UnsupportedFileError(ExtractionError):
    """Raised when the uploaded file format is not supported."""
    pass


class ProfileConflictError(Exception):
    """Raised when a profile upload conflicts with an existing upload."""
    pass
