from fastmcp import FastMCP
from reddit_mcp_server.logging_config import logger
from reddit_mcp_server.tools import (
    register_browse_tools,
    register_search_tools,
    register_post_tools,
    register_user_tools,
    register_submit_tools,
    register_comment_tools,
    register_vote_tools,
    register_messaging_tools,
    register_subreddit_tools,
    register_save_tools,
    register_account_tools,
    register_moderation_tools,
    register_engagement_tools,
    register_info_tools,
)


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "reddit-httpx",
        instructions="Reddit MCP server - full Reddit automation via browser cookies",
    )

    # Register all tool modules
    register_browse_tools(mcp)
    register_search_tools(mcp)
    register_post_tools(mcp)
    register_user_tools(mcp)
    register_submit_tools(mcp)
    register_comment_tools(mcp)
    register_vote_tools(mcp)
    register_messaging_tools(mcp)
    register_subreddit_tools(mcp)
    register_save_tools(mcp)
    register_account_tools(mcp)
    register_moderation_tools(mcp)
    register_engagement_tools(mcp)
    register_info_tools(mcp)

    logger.info("Reddit MCP server created with all tools registered")
    return mcp
