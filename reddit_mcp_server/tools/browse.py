from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_browse_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def reddit_browse_subreddit(subreddit: str, sort: str = "hot", limit: int = 25, time_filter: str = "day", after: str | None = None) -> dict:
        """Browse posts from a subreddit. Sort: hot/new/top/rising/controversial. Time: hour/day/week/month/year/all."""
        try:
            client = await get_reddit_client()
            return await client.get_subreddit_posts(subreddit, sort, limit, time_filter, after)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_browse_frontpage(sort: str = "best", limit: int = 25, after: str | None = None) -> dict:
        """Browse the authenticated user's personalized frontpage."""
        try:
            client = await get_reddit_client()
            return await client.get_frontpage(sort, limit, after)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_browse_popular(limit: int = 25) -> dict:
        """Browse r/popular posts."""
        try:
            client = await get_reddit_client()
            return await client.get_popular(limit)
        except Exception as e:
            handle_api_error(e)
