"""Utility helpers: retry/backoff helper used for API calls."""
import time
import logging
from typing import Callable, Any

LOGGER = logging.getLogger(__name__)


def retry_with_backoff(fn: Callable[..., Any], retries: int = 3, base_delay: float = 1.0, *args, **kwargs) -> Any:
    """Call fn with retries and exponential backoff. Returns fn result or raises last exception."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            delay = base_delay * (2 ** (attempt - 1))
            LOGGER.warning("Attempt %s failed: %s. Retrying in %.1fs...", attempt, e, delay)
            time.sleep(delay)
    LOGGER.error("All %s attempts failed.", retries)
    raise last_exc
