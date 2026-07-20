import json
import sys
import argparse


def axi_error(msg: str, hint: str = None) -> None:
    """Print structured error to stdout (AXI §6) and exit with code 2."""
    out = {"error": msg}
    if hint:
        out["help"] = hint
    print(json.dumps(out))
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Reddit MCP Server")
    parser.add_argument("--login", action="store_true", help="Import cookies from browser")
    parser.add_argument("--logout", action="store_true", help="Clear stored session")
    parser.add_argument("--status", action="store_true", help="Check authentication status")
    parser.add_argument("--list-tools", action="store_true", help="List all available MCP tools")
    parser.add_argument("--tool-info", type=str, metavar="TOOL", help="Show details for a specific tool")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio", help="MCP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    args = parser.parse_args()

    if args.login:
        from reddit_mcp_server.cookie_import import import_cookies_interactive
        from reddit_mcp_server.session_state import save_cookies
        cookies = import_cookies_interactive()
        if cookies:
            save_cookies(cookies)
            print(json.dumps({"status": "success", "message": "Cookies saved."}))
        else:
            axi_error("Login failed. No cookies extracted.", "Ensure you are logged into Reddit in your browser.")
        return

    if args.logout:
        from reddit_mcp_server.session_state import clear_cookies
        clear_cookies()
        print(json.dumps({"status": "success", "message": "Logged out. Cookies cleared."}))
        return

    if args.status:
        from reddit_mcp_server.authentication import get_auth_status
        status = get_auth_status()
        print(json.dumps({"status": "ok", "auth": status}))
        return

    if args.list_tools:
        list_tools_and_exit()

    if args.tool_info:
        tool_info_and_exit(args.tool_info)

    # Start MCP server
    from reddit_mcp_server.bootstrap import initialize_bootstrap
    from reddit_mcp_server.server import create_mcp_server

    initialize_bootstrap()
    mcp = create_mcp_server()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()


def list_tools_and_exit() -> None:
    """List all available MCP tools and exit (AXI §8 content-first)."""
    tools = [
        ("reddit_search", "Search Reddit posts and comments"),
        ("reddit_get_post", "Get a specific Reddit post by ID or URL"),
        ("reddit_get_comments", "Get comments on a Reddit post"),
        ("reddit_get_subreddit", "Get subreddit information"),
        ("reddit_get_user", "Get Reddit user profile information"),
        ("reddit_get_user_posts", "Get a user's recent posts"),
        ("reddit_get_user_comments", "Get a user's recent comments"),
        ("reddit_get_trending", "Get trending posts from a subreddit"),
        ("reddit_get_wiki", "Get subreddit wiki page content"),
        ("reddit_get_rules", "Get subreddit rules"),
        ("reddit_get_flairs", "Get available post flairs for a subreddit"),
        ("reddit_get_mod_log", "Get moderator action log"),
        ("reddit_get_post_awards", "Get awards on a post"),
        ("reddit_get_related_posts", "Get related/similar posts"),
        ("reddit_get_subreddit_about", "Get detailed subreddit metadata"),
        ("reddit_search_comments", "Search within comments of a subreddit"),
    ]
    print(f"tools[{len(tools)}]{{name,description}}:")
    for name, desc in tools:
        print(f"  {name},{desc}")
    print()
    print("help[2]:")
    print("  Run `reddit-httpx --tool-info <name>` for details")
    print("  Run `reddit-httpx` to start the MCP server")
    sys.exit(0)


def tool_info_and_exit(tool_name: str) -> None:
    """Show detailed info for a specific tool (AXI §9 contextual disclosure)."""
    tools_info = {
        "reddit_search": {
            "name": "reddit_search",
            "description": "Search Reddit posts and comments",
            "parameters": {"query": "string (required)", "subreddit": "string (optional)", "sort": "relevance|hot|top|new|comments (default relevance)", "time": "hour|day|week|month|year|all (default all)", "limit": "number (default 25)"},
            "returns": "Array of post objects with title, score, author, comments",
        },
        "reddit_get_post": {
            "name": "reddit_get_post",
            "description": "Get a specific Reddit post by ID or full URL",
            "parameters": {"url_or_id": "string (required)"},
            "returns": "Post object with selftext, score, comments count",
        },
    }
    if tool_name in tools_info:
        print(json.dumps(tools_info[tool_name], indent=2))
    else:
        valid = list(tools_info.keys())
        axi_error(f"Unknown tool: '{tool_name}'", f"Valid tools: {', '.join(valid)}")
    sys.exit(0)
