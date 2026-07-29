from reddit_mcp_server.bootstrap import ensure_ready_or_raise
from reddit_mcp_server.logging_config import logger

_client = None


async def get_reddit_client():
    global _client
    if _client is None:
        cookies = ensure_ready_or_raise()
        from reddit_mcp_server.scraping.api_client import RedditAPIClient

        _client = RedditAPIClient(cookies)
        logger.info("Reddit API client initialized")
        # Validate session on first init
        health = await _client.check_session()
        if not health.get("valid"):
            logger.warning(
                f"Session health check failed: {health.get('reason', 'unknown')}"
            )
    return _client


async def refresh_client():
    """Invalidate cached client so next get_reddit_client() re-reads cookies."""
    global _client
    if _client is not None:
        await _client.close()
    _client = None
    logger.info("Reddit API client reset — will re-read cookies on next call")


def reset_client():
    global _client
    if _client is not None:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_client.close())
        except RuntimeError:
            pass  # no event loop running (e.g. during tests)
    _client = None
