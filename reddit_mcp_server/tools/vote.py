from typing import Literal
from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_vote_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def vote(
        thing_id: str,
        direction: Literal["up", "down", "none"],
    ) -> str:
        """Vote on a Reddit thing (post or comment). thing_id format: t3_xxxxx or t1_xxxxx."""
        direction_map = {"up": 1, "down": -1, "none": 0}
        try:
            client = await get_reddit_client()
            return await client.vote(thing_id, direction_map[direction])
        except Exception as e:
            handle_api_error(e)
