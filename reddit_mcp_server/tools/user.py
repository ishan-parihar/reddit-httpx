from typing import Literal
from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_user_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_user_profile(username: str) -> dict:
        """Get a Reddit user's profile (karma, cake day, trophies)."""
        try:
            client = await get_reddit_client()
            return await client.get_user(username)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_user_posts(
        username: str,
        sort: Literal["new", "top", "hot", "controversial"] = "new",
        limit: int = 25,
    ) -> dict:
        """Get a user's submitted posts."""
        try:
            client = await get_reddit_client()
            return await client.get_user_posts(username, sort, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_user_comments(
        username: str,
        sort: Literal["new", "top", "hot", "controversial"] = "new",
        limit: int = 25,
    ) -> dict:
        """Get a user's comment history."""
        try:
            client = await get_reddit_client()
            return await client.get_user_comments(username, sort, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_my_profile() -> dict:
        """Get the authenticated user's own profile and account details."""
        try:
            client = await get_reddit_client()
            return await client.me()
        except Exception as e:
            handle_api_error(e)
