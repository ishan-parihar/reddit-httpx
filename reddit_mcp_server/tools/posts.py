import re
from typing import Literal
from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def _parse_post_id(post_id_or_url: str) -> tuple[str | None, str]:
    """Extract (subreddit, post_id) from URL or bare ID."""
    m = re.search(r"/r/([^/]+)/comments/([a-z0-9]+)", post_id_or_url)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"redd\.it/([a-z0-9]+)", post_id_or_url)
    if m:
        return None, m.group(1)
    return None, post_id_or_url.strip()


def register_post_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_post(
        post_id_or_url: str,
        sort: Literal["best", "top", "new", "controversial", "old", "qa"] = "best",
        limit: int = 50,
    ) -> list:
        """Get a post's details and comment tree. Accepts post ID, full URL, or redd.it short URL."""
        try:
            client = await get_reddit_client()
            subreddit, post_id = _parse_post_id(post_id_or_url)
            if subreddit:
                return await client.get_post(subreddit, post_id, sort, limit)
            return await client.get_post_by_id(post_id, sort, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_comments(
        post_id_or_url: str,
        sort: Literal["best", "top", "new", "controversial", "old", "qa"] = "best",
        limit: int = 100,
    ) -> dict:
        """Get comments for a post."""
        try:
            client = await get_reddit_client()
            subreddit, post_id = _parse_post_id(post_id_or_url)
            if subreddit:
                result = await client.get_post(subreddit, post_id, sort, limit)
            else:
                result = await client.get_post_by_id(post_id, sort, limit)
            return result[1] if isinstance(result, list) and len(result) > 1 else result
        except Exception as e:
            handle_api_error(e)
