

from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    Return the current UTC datetime as a timezone-aware object.
    Prefer this over datetime.utcnow() which returns a naive datetime.
    """
    return datetime.now(tz=timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """
    Format a datetime object to an ISO-8601 string with UTC suffix.

    Args:
        dt: datetime object (naive or aware).

    Returns:
        String like '2024-06-01T14:30:00Z'
    """
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def truncate(text: str, max_length: int = 120) -> str:
    """
    Truncate a string to max_length characters, appending '...' if cut.

    Useful for log messages and summary fields.

    Args:
        text      : Input string.
        max_length: Maximum allowed length (default 120).

    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitise_message(message: str) -> str:
    """
    Strip leading/trailing whitespace and collapse internal newlines.
    Applied to raw customer messages before processing.

    Args:
        message: Raw input string.

    Returns:
        Cleaned string.
    """
    return " ".join(message.split())