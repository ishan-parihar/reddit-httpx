from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def reddit_search_posts(query: str, subreddit: str | None = None, sort: str = "relevance", time_filter: str = "all", limit: int = 25) -> dict:
        """Search Reddit posts. Optionally restrict to a subreddit. Sort: relevance/hot/top/new/comments."""
        try:
            client = await get_reddit_client()
            return await client.search(query, subreddit, sort, time_filter, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_search_subreddits(query: str, limit: int = 10) -> dict:
        """Search for subreddits by name or topic."""
        try:
            client = await get_reddit_client()
            return await client.search_subreddits(query, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_search_users(query: str, limit: int = 10) -> dict:
        """Search for Reddit users."""
        try:
            client = await get_reddit_client()
            return await client.search_users(query, limit)
        except Exception as e:
            handle_api_error(e)
