"""Pure filter/validation helpers for search params (e.g. normalize location strings)."""


def normalize_filters(keyword: str, location: str | None, remote: bool | None, date_posted: str | None) -> dict:
    return {
        "keyword": keyword.strip(),
        "location": location.strip() if location else None,
        "remote": remote,
        "date_posted": date_posted,
    }
