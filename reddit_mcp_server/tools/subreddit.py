from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_subreddit_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def subscribe(subreddit: str) -> dict:
        """Subscribe to a subreddit."""
        try:
            client = await get_reddit_client()
            await client.subscribe(subreddit)
            return {"ok": True, "action": "subscribed", "subreddit": subreddit}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def unsubscribe(subreddit: str) -> dict:
        """Unsubscribe from a subreddit."""
        try:
            client = await get_reddit_client()
            await client.unsubscribe(subreddit)
            return {"ok": True, "action": "unsubscribed", "subreddit": subreddit}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_subreddit_info(subreddit: str) -> dict:
        """Get subreddit details (description, rules, subscribers, created date)."""
        try:
            client = await get_reddit_client()
            return await client.get_subreddit_info(subreddit)
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def get_my_subreddits(limit: int = 100) -> dict:
        """List the authenticated user's subscribed subreddits."""
        try:
            client = await get_reddit_client()
            return await client.get_my_subreddits(limit)
        except Exception as e:
            handle_api_error(e)
