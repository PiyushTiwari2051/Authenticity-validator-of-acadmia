"""Structured logging configuration.
Emits clean JSON logs with request correlation IDs and strict PII scrubbers.
"""

import logging
import sys
import structlog
from typing import Any


def censor_sensitive_keys(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Scrub sensitive keys from structured logs to prevent credential or personal data leakage."""
    sensitive_keys = {
        "password", "password_hash", "token", "totp_secret",
        "secret", "kek", "private_key", "authorization", "enrolment_no"
    }
    for key in list(event_dict.keys()):
        if any(sens in key.lower() for sens in sensitive_keys):
            event_dict[key] = "[REDACTED]"
    return event_dict


def setup_logging(is_dev: bool = True) -> None:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        censor_sensitive_keys,
    ]

    if is_dev:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.processors.format_by_level,
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


logger = structlog.get_logger("sanad")
