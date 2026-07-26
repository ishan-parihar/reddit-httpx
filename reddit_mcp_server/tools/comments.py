from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_comment_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def comment(parent_id: str, text: str) -> dict:
        """Comment on a post. parent_id format: t3_xxxxx (post) or t1_xxxxx (comment for reply)."""
        try:
            client = await get_reddit_client()
            result = await client.comment(parent_id, text)
            return {"ok": True, "action": "commented", "id": parent_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reply(comment_id: str, text: str) -> dict:
        """Reply to a comment. comment_id format: t1_xxxxx."""
        try:
            client = await get_reddit_client()
            result = await client.comment(comment_id, text)
            return {"ok": True, "action": "replied", "id": comment_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def edit_comment(thing_id: str, text: str) -> dict:
        """Edit own comment. thing_id format: t1_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.edit_comment(thing_id, text)
            return {"ok": True, "action": "edited", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def delete_comment(thing_id: str) -> dict:
        """Delete own comment. thing_id format: t1_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.delete_thing(thing_id)
            return {"ok": True, "action": "deleted", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
