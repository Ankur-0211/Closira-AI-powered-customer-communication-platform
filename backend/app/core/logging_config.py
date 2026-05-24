

import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Custom log formatter that serialises every LogRecord to a JSON string.

    Standard fields always present:
        timestamp  — ISO-8601 UTC
        level      — DEBUG / INFO / WARNING / ERROR / CRITICAL
        logger     — dotted logger name
        message    — the log message

    Extra fields (passed via logger.info(..., extra={...})):
        event_type — maps to EventType enum values
        enquiry_id — integer ID of the related enquiry (if applicable)
        details    — any additional key/value pairs
    """

    RESERVED_ATTRS = {
        "args", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "message",
        "module", "msecs", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "thread",
        "threadName", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Base structure always present
        log_object: dict = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Append exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Pull any extra fields injected via logger.xxx(..., extra={...})
        extras: dict = {}
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                extras[key] = value

        if extras:
            log_object.update(extras)

        return json.dumps(log_object, default=str)


def setup_logging(log_dir: str = "app/logs", log_file: str = "app/logs/app.log") -> None:
    """
    Configure the root logger with:
      - StreamHandler  → stdout (always active)
      - RotatingFileHandler → log_file (5 MB cap, 3 rotations)

    Call this once at application startup (in main.py lifespan).

    Args:
        log_dir : Directory to create if it does not exist.
        log_file: Full path to the rotating log file.
    """
    os.makedirs(log_dir, exist_ok=True)

    formatter = JSONFormatter()

    # --- stdout handler ---
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    # --- rotating file handler ---
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,   # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # --- root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if setup_logging is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(stream_handler)
        root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)