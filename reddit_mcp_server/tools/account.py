from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_account_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_account_info() -> dict:
        """Get the authenticated user's account details (karma, email, preferences)."""
        try:
            client = await get_reddit_client()
            return await client.me()
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_friends() -> dict:
        """List the authenticated user's friends."""
        try:
            client = await get_reddit_client()
            return await client.get_friends()
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def add_friend(username: str) -> dict:
        """Add a user as friend."""
        try:
            client = await get_reddit_client()
            await client.add_friend(username)
            return {"ok": True, "action": "friended", "user": username}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def remove_friend(username: str) -> dict:
        """Remove a user from friends list."""
        try:
            client = await get_reddit_client()
            await client.remove_friend(username)
            return {"ok": True, "action": "unfriended", "user": username}
        except Exception as e:
            handle_api_error(e)
