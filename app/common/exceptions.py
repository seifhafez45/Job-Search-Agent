"""Shared exception types raised across feature modules, caught centrally in main.py if needed."""


class NotFoundError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class ExternalAPIError(Exception):
    """Raised when a 3rd-party API (job board, LLM provider) fails or times out."""
    pass


class ExtractionError(Exception):
    """Raised when CV parsing/structuring fails validation."""
    pass
