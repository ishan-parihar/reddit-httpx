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
    return _client

def reset_client():
    global _client
    _client = None
