from typing import Literal
from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_moderation_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def mod_remove(thing_id: str, spam: bool = False) -> dict:
        """Remove a post or comment as moderator. thing_id: t3_xxx or t1_xxx."""
        try:
            client = await get_reddit_client()
            await client.mod_remove(thing_id, spam)
            return {"ok": True, "action": "removed_spam" if spam else "removed", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mod_approve(thing_id: str) -> dict:
        """Approve a post or comment as moderator."""
        try:
            client = await get_reddit_client()
            await client.mod_approve(thing_id)
            return {"ok": True, "action": "approved", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mod_distinguish(
        thing_id: str,
        how: Literal["yes", "no", "admin", "special"] = "yes",
    ) -> dict:
        """Distinguish a comment as moderator."""
        try:
            client = await get_reddit_client()
            await client.mod_distinguish(thing_id, how)
            return {"ok": True, "action": f"distinguished_{how}", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mod_sticky(thing_id: str, state: bool = True) -> dict:
        """Sticky or unsticky a post."""
        try:
            client = await get_reddit_client()
            await client.mod_sticky(thing_id, state)
            return {"ok": True, "action": "stickied" if state else "unstickied", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mod_lock(thing_id: str) -> dict:
        """Lock a post (prevent new comments)."""
        try:
            client = await get_reddit_client()
            await client.mod_lock(thing_id)
            return {"ok": True, "action": "locked", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mod_unlock(thing_id: str) -> dict:
        """Unlock a previously locked post."""
        try:
            client = await get_reddit_client()
            await client.mod_unlock(thing_id)
            return {"ok": True, "action": "unlocked", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
