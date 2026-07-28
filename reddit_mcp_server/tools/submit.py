from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_submit_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def submit_text_post(
        subreddit: str,
        title: str,
        text: str = "",
        flair_id: str | None = None,
        nsfw: bool = False,
        spoiler: bool = False,
    ) -> dict:
        """Submit a text/self post to a subreddit."""
        try:
            client = await get_reddit_client()
            result = await client.submit_text(
                subreddit, title, text, flair_id, nsfw, spoiler
            )
            # Reddit returns {"json": {"data": {"id": "...", "name": "t3_..."}}}
            post_id = result.get("json", {}).get("data", {}).get("name", "unknown")
            return {
                "ok": True,
                "action": "posted",
                "subreddit": subreddit,
                "id": post_id,
            }
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def submit_link_post(
        subreddit: str,
        title: str,
        url: str,
        flair_id: str | None = None,
        nsfw: bool = False,
    ) -> dict:
        """Submit a link post to a subreddit."""
        try:
            client = await get_reddit_client()
            result = await client.submit_link(subreddit, title, url, flair_id, nsfw)
            post_id = result.get("json", {}).get("data", {}).get("name", "unknown")
            return {
                "ok": True,
                "action": "posted",
                "subreddit": subreddit,
                "id": post_id,
                "url": url,
            }
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def edit_post(thing_id: str, text: str) -> dict:
        """Edit a self post's body text. thing_id format: t3_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.edit_post(thing_id, text)
            return {"ok": True, "action": "edited", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def delete_post(thing_id: str) -> dict:
        """Delete own post. thing_id format: t3_xxxxx."""
        try:
            client = await get_reddit_client()
            await client.delete_thing(thing_id)
            return {"ok": True, "action": "deleted", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
