from reddit_mcp_server.exceptions import AuthenticationError, RateLimitError, ToolError
from reddit_mcp_server.logging_config import logger


def raise_tool_error(message: str, cause: Exception | None = None) -> None:
    logger.error(f"Tool error: {message}", exc_info=cause)
    raise ToolError(message) from cause


def handle_api_error(e: Exception) -> None:
    if isinstance(e, AuthenticationError):
        # Best-effort: invalidate cached client so next call re-reads cookies.
        # If the user re-logged in externally, the next tool call picks it up.
        import asyncio
        try:
            from reddit_mcp_server.dependencies import refresh_client
            loop = asyncio.get_running_loop()
            loop.create_task(refresh_client())
        except Exception:
            pass
        raise_tool_error(
            "Session expired. Run `reddit-httpx --login` to re-authenticate.", e
        )
    elif isinstance(e, RateLimitError):
        raise_tool_error(f"Rate limited by Reddit. Wait {e.retry_after}s.", e)
    elif isinstance(e, RuntimeError):
        # From bootstrap.ensure_ready_or_raise() — setup issue, not API error
        raise_tool_error(str(e), e)
    else:
        # Sanitize: don't leak raw exception details (AXI §6)
        msg = str(e)
        # Common patterns to sanitize
        if "429" in msg or "rate limit" in msg.lower():
            msg = "Rate limited by Reddit. Please wait."
        elif "401" in msg or "403" in msg or "unauthorized" in msg.lower() or "forbidden" in msg.lower():
            msg = "Authentication failed. Run `reddit-httpx --login` to re-authenticate."
        elif "500" in msg or "502" in msg or "503" in msg:
            msg = "Reddit server error. Please try again later."
        elif "timeout" in msg.lower():
            msg = "Request timed out. Please try again."
        elif "connection" in msg.lower():
            msg = "Network error. Check your connection and try again."
        else:
            msg = "Reddit API error. Please try again."
        raise_tool_error(msg, e)
