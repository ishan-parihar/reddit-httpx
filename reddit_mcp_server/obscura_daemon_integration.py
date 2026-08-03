"""
Reddit-specific Obscura Daemon plugin integration.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from obscura_core import ObscuraPlugin, CookieValidationResult

logger = logging.getLogger(__name__)

# Required cookies for Reddit
REDDIT_REQUIRED_COOKIES = ["token_v2", "reddit_session"]
REDDIT_WRITE_REQUIRED_COOKIES = ["reddit_session"]


class RedditDaemonManager:
    """Reddit-specific wrapper around Obscura Daemon plugin."""

    def __init__(self, daemon_url: str = "http://127.0.0.1:9999"):
        self.daemon_url = daemon_url
        self._plugin: Optional[ObscuraPlugin] = None
        self._use_daemon = os.getenv("REDDIT_USE_DAEMON", "true").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    async def _get_plugin(self) -> ObscuraPlugin:
        """Get or create the ObscuraPlugin instance."""
        if self._plugin is None:
            self._plugin = ObscuraPlugin(daemon_url=self.daemon_url)
            await self._plugin.connect()
        return self._plugin

    async def get_valid_cookies(self, force_refresh: bool = False) -> CookieValidationResult:
        """Get valid cookies from daemon cache."""
        if not self._use_daemon:
            logger.debug("Daemon integration disabled, falling back to local ObscuraCookieManager")
            # Import here to avoid circular imports
            from reddit_mcp_server.obscura_integration import get_valid_reddit_cookies

            return await get_valid_reddit_cookies(force_refresh)

        try:
            plugin = await self._get_plugin()

            if force_refresh:
                # Trigger sync to refresh cache
                await plugin.sync_cookies("reddit")

            cookies = await plugin.get_cookies("reddit")

            if cookies is None:
                logger.warning("No cookies found in daemon cache for reddit")
                return CookieValidationResult(
                    valid=False,
                    source="daemon",
                    cookies={},
                    error="No cookies found in daemon cache",
                )

            # Validate required cookies
            for cookie in REDDIT_REQUIRED_COOKIES:
                if cookie not in cookies or not cookies[cookie]:
                    logger.debug(f"Required cookie missing: {cookie}")
                    return CookieValidationResult(
                        valid=False,
                        source="daemon",
                        cookies=cookies,
                        error=f"Required cookie missing: {cookie}",
                    )

            return CookieValidationResult(
                valid=True,
                cookies=cookies,
                source="daemon",
            )
        except Exception as e:
            logger.error(f"Error getting cookies from daemon: {e}")
            # Fall back to local ObscuraCookieManager
            logger.debug("Falling back to local ObscuraCookieManager")
            from reddit_mcp_server.obscura_integration import get_valid_reddit_cookies

            return await get_valid_reddit_cookies(force_refresh)

    async def get_write_cookies(self, force_refresh: bool = False) -> CookieValidationResult:
        """Get cookies valid for write operations (requires reddit_session)."""
        result = await self.get_valid_cookies(force_refresh)

        if not result.valid:
            return result

        # Check if we have reddit_session for writes
        if "reddit_session" not in result.cookies:
            return CookieValidationResult(
                valid=False,
                source=result.source,
                cookies=result.cookies,
                error="reddit_session cookie missing - write operations require re-login",
                metadata={"write_capable": False},
            )

        return CookieValidationResult(
            valid=True,
            source=result.source,
            cookies=result.cookies,
            metadata={"write_capable": True},
        )

    async def close(self) -> None:
        """Close the plugin connection."""
        if self._plugin:
            await self._plugin.close()
            self._plugin = None


# Global instance
_reddit_daemon_manager: Optional[RedditDaemonManager] = None


def get_reddit_daemon_manager(daemon_url: str = "http://127.0.0.1:9999") -> RedditDaemonManager:
    """Get the global Reddit Daemon manager instance."""
    global _reddit_daemon_manager
    if _reddit_daemon_manager is None:
        _reddit_daemon_manager = RedditDaemonManager(daemon_url=daemon_url)
    return _reddit_daemon_manager


async def get_valid_reddit_cookies_from_daemon(
    force_refresh: bool = False,
) -> CookieValidationResult:
    """Get valid Reddit cookies using Obscura Daemon plugin."""
    manager = get_reddit_daemon_manager()
    return await manager.get_valid_cookies(force_refresh)


async def get_write_reddit_cookies_from_daemon(
    force_refresh: bool = False,
) -> CookieValidationResult:
    """Get Reddit cookies valid for write operations using Obscura Daemon plugin."""
    manager = get_reddit_daemon_manager()
    return await manager.get_write_cookies(force_refresh)
