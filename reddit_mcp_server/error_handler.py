from reddit_mcp_server.exceptions import AuthenticationError, RateLimitError, ToolError
from reddit_mcp_server.logging_config import logger

def raise_tool_error(message: str, cause: Exception | None = None) -> None:
    logger.error(f"Tool error: {message}", exc_info=cause)
    raise ToolError(message) from cause

def handle_api_error(e: Exception) -> None:
    if isinstance(e, AuthenticationError):
        raise_tool_error("Session expired. Run `reddit-mcp --login` to re-authenticate.", e)
    elif isinstance(e, RateLimitError):
        raise_tool_error(f"Rate limited by Reddit. Wait {e.retry_after}s.", e)
    else:
        raise_tool_error(f"Reddit API error: {e}", e)
