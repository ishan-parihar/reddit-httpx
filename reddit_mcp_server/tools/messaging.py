from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_messaging_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def reddit_get_inbox(where: str = "inbox", limit: int = 25) -> dict:
        """Get inbox messages. where: inbox/unread/messages/sent/mentions."""
        try:
            client = await get_reddit_client()
            return await client.get_inbox(where, limit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_send_message(to: str, subject: str, body: str) -> dict:
        """Send a private message to a user."""
        try:
            client = await get_reddit_client()
            return await client.send_message(to, subject, body)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_mark_read(thing_id: str) -> dict:
        """Mark a message as read. thing_id format: t4_xxxxx."""
        try:
            client = await get_reddit_client()
            return await client.read_message(thing_id)
        except Exception as e:
            handle_api_error(e)
