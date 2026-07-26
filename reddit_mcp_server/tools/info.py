from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_info_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_karma() -> dict:
        """Get the authenticated user's karma breakdown by subreddit."""
        try:
            client = await get_reddit_client()
            return await client.get_karma()
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_user_overview(username: str, sort: str = "new", limit: int = 25) -> dict:
        """Get a user's combined overview of posts and comments."""
        try:
            client = await get_reddit_client()
            return await client.get_user_overview(username, sort, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_subreddit_rules(subreddit: str) -> dict:
        """Get the rules for a subreddit."""
        try:
            client = await get_reddit_client()
            return await client.get_subreddit_rules(subreddit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_subreddit_moderators(subreddit: str) -> dict:
        """Get the list of moderators for a subreddit."""
        try:
            client = await get_reddit_client()
            return await client.get_subreddit_moderators(subreddit)
        except Exception as e:
            handle_api_error(e)
