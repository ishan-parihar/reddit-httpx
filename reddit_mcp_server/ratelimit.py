"""Sliding-window rate limiter for Reddit API.

Reddit sends these headers on every response:
  X-Ratelimit-Remaining: how many requests remain in the current window
  X-Ratelimit-Reset:     epoch seconds when the window resets
  Retry-After:           seconds to wait (only on 429)

This module tracks the remaining budget and pre-throttles before hitting 429.
On 429, it sleeps for the exact Retry-After duration instead of guessing.
"""

import asyncio
import time
from reddit_mcp_server.logging_config import logger


class RateLimiter:
    def __init__(self, min_remaining: int = 5):
        # When remaining drops below this, sleep until reset
        self._min_remaining = min_remaining
        self._reset_at: float = 0.0  # epoch when window resets
        self._remaining: int = 999   # assume generous until first response
        self._lock = asyncio.Lock()

    def update_from_headers(self, headers: dict) -> None:
        """Parse X-Ratelimit-* headers from a response."""
        remaining = headers.get("x-ratelimit-remaining")
        reset = headers.get("x-ratelimit-reset")
        if remaining is not None:
            try:
                self._remaining = int(float(remaining))
            except (ValueError, TypeError):
                pass
        if reset is not None:
            try:
                self._reset_at = float(reset)
            except (ValueError, TypeError):
                pass

    async def acquire(self) -> None:
        """Wait if we're near the rate limit ceiling."""
        async with self._lock:
            if self._remaining <= self._min_remaining and self._reset_at > 0:
                wait = max(0.0, self._reset_at - time.time())
                if wait > 0:
                    logger.info(f"Rate limiter: {self._remaining} remaining, sleeping {wait:.1f}s until reset")
                    await asyncio.sleep(wait)
                    # After sleeping, assume the window has refreshed
                    self._remaining = 999

    async def wait_for_retry_after(self, retry_after_header: str | None) -> float:
        """On 429, sleep the exact Retry-After duration. Returns seconds slept."""
        if retry_after_header:
            try:
                wait = float(retry_after_header)
            except (ValueError, TypeError):
                wait = 60.0
        else:
            wait = 60.0
        logger.warning(f"429 Rate limited, sleeping {wait:.1f}s (Retry-After)")
        await asyncio.sleep(wait)
        self._remaining = 999  # assume refreshed after wait
        return wait

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def reset_at(self) -> float:
        return self._reset_at
