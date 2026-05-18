from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_vote_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def reddit_upvote(thing_id: str) -> dict:
        """Upvote a post or comment. thing_id format: t3_xxxxx or t1_xxxxx."""
        try:
            client = await get_reddit_client()
            return await client.vote(thing_id, 1)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_downvote(thing_id: str) -> dict:
        """Downvote a post or comment. thing_id format: t3_xxxxx or t1_xxxxx."""
        try:
            client = await get_reddit_client()
            return await client.vote(thing_id, -1)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def reddit_unvote(thing_id: str) -> dict:
        """Remove vote from a post or comment. thing_id format: t3_xxxxx or t1_xxxxx."""
        try:
            client = await get_reddit_client()
            return await client.vote(thing_id, 0)
        except Exception as e:
            handle_api_error(e)
