from fastmcp import FastMCP
from reddit_mcp_server.dependencies import get_reddit_client
from reddit_mcp_server.error_handler import handle_api_error


def register_engagement_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def report(thing_id: str, reason: str = "", rule_reason: str = "", site_reason: str = "", other_reason: str = "") -> dict:
        """Report a post or comment to subreddit moderators. thing_id: t3_xxx or t1_xxx. Provide at least one reason field."""
        try:
            client = await get_reddit_client()
            await client.report(thing_id, reason=reason, rule_reason=rule_reason, site_reason=site_reason, other_reason=other_reason)
            return {"ok": True, "action": "reported", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def block_user(username: str) -> dict:
        """Block a Reddit user. They won't be able to message you or see your posts."""
        try:
            client = await get_reddit_client()
            await client.block_user(username)
            return {"ok": True, "action": "blocked", "user": username}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def follow_post(thing_id: str, follow: bool = True) -> dict:
        """Follow or unfollow a post to get inbox replies for new comments. thing_id: t3_xxx."""
        try:
            client = await get_reddit_client()
            await client.follow_post(thing_id, follow)
            return {"ok": True, "action": "followed" if follow else "unfollowed", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def sendreplies(thing_id: str, state: bool = True) -> dict:
        """Enable or disable inbox replies for a post or comment you created. thing_id: t3_xxx or t1_xxx."""
        try:
            client = await get_reddit_client()
            await client.sendreplies(thing_id, state)
            return {"ok": True, "action": "replies_enabled" if state else "replies_disabled", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def read_all_messages() -> dict:
        """Mark all inbox messages as read."""
        try:
            client = await get_reddit_client()
            await client.read_all_messages()
            return {"ok": True, "action": "all_messages_read"}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def marknsfw(thing_id: str) -> dict:
        """Mark your own post as NSFW. thing_id: t3_xxx."""
        try:
            client = await get_reddit_client()
            await client.marknsfw(thing_id)
            return {"ok": True, "action": "marked_nsfw", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def unmarknsfw(thing_id: str) -> dict:
        """Remove NSFW tag from your own post. thing_id: t3_xxx."""
        try:
            client = await get_reddit_client()
            await client.unmarknsfw(thing_id)
            return {"ok": True, "action": "unmarked_nsfw", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def spoiler(thing_id: str) -> dict:
        """Mark your own post as a spoiler. thing_id: t3_xxx."""
        try:
            client = await get_reddit_client()
            await client.spoiler(thing_id)
            return {"ok": True, "action": "marked_spoiler", "id": thing_id}
        except Exception as e:
            handle_api_error(e)

    @mcp.tool()
    async def unspoiler(thing_id: str) -> dict:
        """Remove spoiler tag from your own post. thing_id: t3_xxx."""
        try:
            client = await get_reddit_client()
            await client.unspoiler(thing_id)
            return {"ok": True, "action": "unmarked_spoiler", "id": thing_id}
        except Exception as e:
            handle_api_error(e)
