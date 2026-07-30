"""
Reddit-specific ObscuraCookieManager integration.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from obscura_cookie_manager import (
    ObscuraCookieManager,
    FileCookieStorage,
    BrowserCookie3Extractor,
    CookieSource,
    CookieValidationResult,
    ReLoginRequiredError,
)
from reddit_mcp_server.session_state import get_cookies_path, load_cookies, save_cookies
from reddit_mcp_server.scraping.api_client import RedditAPIClient
from reddit_mcp_server.constants import REDDIT_BASE_URL
from reddit_mcp_server.logging_config import logger

# Required cookies for Reddit
REDDIT_REQUIRED_COOKIES = ["token_v2", "reddit_session"]
REDDIT_WRITE_REQUIRED_COOKIES = ["reddit_session"]


class RedditCookieValidator:
    """Validates Reddit cookies by making an API call."""
    
    def __init__(self):
        self._client: Optional[RedditAPIClient] = None
    
    async def validate(self, cookies: dict[str, str]) -> bool:
        """Validate cookies by calling /api/me.json."""
        try:
            # Create a temporary client with these cookies
            client = RedditAPIClient(cookies)
            health = await client.check_session()
            await client.close()
            return health.get("valid", False)
        except Exception as e:
            logger.debug(f"Reddit cookie validation failed: {e}")
            return False
    
    async def validate_write(self, cookies: dict[str, str]) -> bool:
        """Validate cookies for write operations (requires reddit_session)."""
        if "reddit_session" not in cookies:
            return False
        return await self.validate(cookies)


class RedditObscuraManager:
    """Reddit-specific wrapper around ObscuraCookieManager."""
    
    def __init__(self):
        self._manager: Optional[ObscuraCookieManager] = None
        self._validator = RedditCookieValidator()
        self._initialized = False
    
    def _get_storage(self) -> FileCookieStorage:
        """Get file-based cookie storage."""
        return FileCookieStorage(get_cookies_path())
    
    def _get_extractor(self) -> BrowserCookie3Extractor:
        """Get browser cookie extractor (prefers Zen, then Brave)."""
        # Try Zen first (Firefox-based, unencrypted cookies)
        return BrowserCookie3Extractor("zen")
    
    def _get_manager(self) -> ObscuraCookieManager:
        """Get or create the ObscuraCookieManager instance."""
        if self._manager is None:
            self._manager = ObscuraCookieManager(
                storage=self._get_storage(),
                extractor=self._get_extractor(),
                validator=self._validator.validate,
                required_cookies=REDDIT_REQUIRED_COOKIES,
                validation_interval=300,  # 5 minutes
                max_re_extraction_attempts=3,
                re_extraction_cooldown=60,
            )
            # Set invalidation callback
            self._manager.set_invalidation_callback(self._on_auth_invalidated)
        return self._manager
    
    def _on_auth_invalidated(self) -> None:
        """Called when auth is invalidated - clear cached client."""
        from reddit_mcp_server.dependencies import reset_client
        reset_client()
        logger.warning("Reddit auth invalidated, client reset")
    
    async def get_valid_cookies(self, force_refresh: bool = False) -> CookieValidationResult:
        """Get valid cookies, performing validation and re-extraction as needed."""
        manager = self._get_manager()
        return await manager.get_cookies(force_refresh=force_refresh)
    
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
                metadata={"write_capable": False}
            )
        
        # Validate write capability
        is_write_valid = await self._validator.validate_write(result.cookies)
        if not is_write_valid:
            return CookieValidationResult(
                valid=False,
                source=result.source,
                cookies=result.cookies,
                error="reddit_session expired - write operations require re-login",
                metadata={"write_capable": False}
            )
        
        return CookieValidationResult(
            valid=True,
            source=result.source,
            cookies=result.cookies,
            metadata={"write_capable": True}
        )
    
    async def force_re_extraction(self) -> CookieValidationResult:
        """Force re-extraction from browser (call after user logs in)."""
        manager = self._get_manager()
        return await manager.force_re_extraction()
    
    async def invalidate_and_trigger_relogin(self) -> None:
        """Invalidate auth and trigger re-login flow."""
        manager = self._get_manager()
        await manager.invalidate_and_trigger_relogin()
    
    def is_cache_valid(self) -> bool:
        """Check if cached cookies are within validation interval."""
        manager = self._get_manager()
        return manager.is_cache_valid()


# Global instance
_reddit_obscura_manager: Optional[RedditObscuraManager] = None


def get_reddit_obscura_manager() -> RedditObscuraManager:
    """Get the global Reddit Obscura manager instance."""
    global _reddit_obscura_manager
    if _reddit_obscura_manager is None:
        _reddit_obscura_manager = RedditObscuraManager()
    return _reddit_obscura_manager


async def get_valid_reddit_cookies(force_refresh: bool = False) -> CookieValidationResult:
    """Get valid Reddit cookies using ObscuraCookieManager."""
    manager = get_reddit_obscura_manager()
    return await manager.get_valid_cookies(force_refresh)


async def get_write_reddit_cookies(force_refresh: bool = False) -> CookieValidationResult:
    """Get Reddit cookies valid for write operations."""
    manager = get_reddit_obscura_manager()
    return await manager.get_write_cookies(force_refresh)


async def force_reddit_cookie_refresh() -> CookieValidationResult:
    """Force re-extraction of Reddit cookies from browser."""
    manager = get_reddit_obscura_manager()
    return await manager.force_re_extraction()


async def invalidate_reddit_auth() -> None:
    """Invalidate Reddit auth and trigger re-login."""
    manager = get_reddit_obscura_manager()
    await manager.invalidate_and_trigger_relogin()