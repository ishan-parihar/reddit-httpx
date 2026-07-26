from typing import Literal
from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_messaging_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_inbox(
        where: Literal["inbox", "unread", "messages", "sent", "mentions"] = "inbox",
        limit: int = 25,
    ) -> dict:
        """Get inbox messages."""
        try:
            client = await get_reddit_client()
            return await client.get_inbox(where, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def send_message(to: str, subject: str, body: str) -> dict:
        """Send a private message to a user."""
        try:
            client = await get_reddit_client()
            await client.send_message(to, subject, body)
            return {"ok": True, "action": "sent", "to": to, "subject": subject}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def mark_read(thing_id: str) -> dict:
        """Mark a message as read. thing_id format: t4_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.read_message(thing_id)
            return {"ok": True, "action": "marked_read", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
