from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_save_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def save(thing_id: str) -> dict:
        """Save a post or comment. thing_id format: t3_xxxxx or t1_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.save(thing_id)
            return {"ok": True, "action": "saved", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def unsave(thing_id: str) -> dict:
        """Unsave a post or comment."""
        try:
            client = await get_reddit_client()
            await client.unsave(thing_id)
            return {"ok": True, "action": "unsaved", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_saved(limit: int = 25) -> dict:
        """Get the authenticated user's saved posts and comments."""
        try:
            client = await get_reddit_client()
            return await client.get_saved(limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def hide(thing_id: str) -> dict:
        """Hide a post from your feed."""
        try:
            client = await get_reddit_client()
            await client.hide(thing_id)
            return {"ok": True, "action": "hidden", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def unhide(thing_id: str) -> dict:
        """Unhide a previously hidden post."""
        try:
            client = await get_reddit_client()
            await client.unhide(thing_id)
            return {"ok": True, "action": "unhidden", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
