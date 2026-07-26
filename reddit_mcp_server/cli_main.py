import json
import os
import sys
import argparse

# ── TOON-like output helpers (AXI §1) ──────────────────────────────────────

def axi_error(msg: str, hint: str = None) -> None:
    """Print structured error to stdout (AXI §6) and exit with code 2."""
    out = {"error": msg}
    if hint:
        out["help"] = hint
    print(json.dumps(out))
    sys.exit(2)


def _truncate(s: str, max_chars: int = 60) -> str:
    """Truncate string with ellipsis (AXI §3)."""
    if len(s) <= max_chars:
        return s
    return f"{s[:max_chars]}...\n  ... (truncated, {len(s)} chars total)"


def _get_bin_path() -> str:
    """Get executable path with home dir collapsed to ~ (AXI §10)."""
    try:
        # Use sys.argv[0] which is the actual CLI entry point
        exe = sys.argv[0] if sys.argv else "reddit-httpx"
        home = os.environ.get("HOME", "")
        if home and exe.startswith(home):
            return exe.replace(home, "~", 1)
        return exe
    except Exception:
        return "reddit-httpx"


# ── Tool registry (auto-discovered from MCP server) ────────────────────────

def _discover_tools() -> list[tuple[str, str]]:
    """Dynamically list all registered MCP tools with their docstrings."""
    try:
        import asyncio
        from reddit_mcp_server.server import create_mcp_server
        mcp = create_mcp_server()
        tools_obj = asyncio.run(mcp.list_tools())
        return sorted([(t.name, (t.description or "").split("\n")[0].strip()) for t in tools_obj], key=lambda x: x[0])
    except Exception:
        # Fallback: static list if discovery fails
        return [
            ("browse_subreddit", "Browse posts from a subreddit"),
            ("browse_frontpage", "Browse the personalized frontpage"),
            ("browse_popular", "Browse r/popular"),
            ("search_posts", "Search Reddit posts"),
            ("search_subreddits", "Search for subreddits"),
            ("search_users", "Search for Reddit users"),
            ("get_post", "Get a post's details and comment tree"),
            ("get_comments", "Get comments for a post"),
            ("get_user_profile", "Get a Reddit user's profile"),
            ("get_user_posts", "Get a user's recent posts"),
            ("get_user_comments", "Get a user's recent comments"),
            ("get_my_profile", "Get the authenticated user's profile"),
        ]

TOOLS = _discover_tools()


# ── AXI §8: Content-first home view ───────────────────────────────────────

def _get_username() -> str:
    """Fetch username from Reddit's /api/me.json endpoint."""
    try:
        from reddit_mcp_server.session_state import load_cookies
        from reddit_mcp_server.scraping.api_client import RedditAPIClient
        cookies = load_cookies()
        if not cookies:
            return "unknown"
        import asyncio
        client = RedditAPIClient(cookies)
        try:
            data = asyncio.run(client.me())
            return data.get("data", {}).get("name", "unknown")
        finally:
            asyncio.run(client.close())
    except Exception:
        return "unknown"


def show_home_view() -> None:
    """Show live state when no args provided (AXI §8)."""
    bin_path = _get_bin_path()

    # Check session state
    has_cookies = False
    auth_status = {"authenticated": False}
    try:
        from reddit_mcp_server.session_state import load_cookies
        from reddit_mcp_server.authentication import get_auth_status
        has_cookies = load_cookies() is not None
        if has_cookies:
            auth_status = get_auth_status()
    except Exception as e:
        # Log warning but don't fail — session check is best-effort
        print(json.dumps({"warning": f"Session check failed: {e}"}), file=sys.stderr)

    # AXI §10: Tool identity header
    print(f"bin: {bin_path}")
    print(f"description: Reddit MCP server — browsing, posting, commenting, voting, and moderation")
    print()

    # Live session state
    print("session:")
    if has_cookies and auth_status.get("authenticated", False):
        username = _get_username()
        print(f"  status: authenticated")
        print(f"  username: {username}")
    else:
        print(f"  status: not_authenticated")
        print(f"  help: Run `reddit-httpx --login` to import browser cookies")
    print()

    # Tool listing in TOON format (AXI §2: minimal schema)
    print(f"tools[{len(TOOLS)}]{{name,description}}:")
    for name, desc in TOOLS:
        print(f"  {name},{_truncate(desc)}")
    print()

    # AXI §9: Contextual disclosure
    print("help[4]:")
    print("  Run `reddit-httpx --tool-info <name>` for detailed parameters")
    print("  Run `reddit-httpx --list-tools` to see all tools")
    print("  Run `reddit-httpx --login` to import browser cookies")
    print("  Run `reddit-httpx` to start the MCP server")


def list_tools_and_exit() -> None:
    """List all available MCP tools and exit (AXI §8 content-first)."""
    print(f"tools[{len(TOOLS)}]{{name,description}}:")
    for name, desc in TOOLS:
        print(f"  {name},{desc}")
    print()
    print("help[2]:")
    print("  Run `reddit-httpx --tool-info <name>` for details")
    print("  Run `reddit-httpx` to start the MCP server")
    sys.exit(0)


def tool_info_and_exit(tool_name: str) -> None:
    """Show detailed info for a specific tool."""
    try:
        import asyncio
        from reddit_mcp_server.server import create_mcp_server
        mcp = create_mcp_server()
        tools_obj = asyncio.run(mcp.list_tools())
        tool = next((t for t in tools_obj if t.name == tool_name), None)
        if tool:
            info = {"name": tool.name, "description": tool.description or ""}
            # Extract parameter info from schema if available
            if hasattr(tool, "parameters") and tool.parameters:
                info["parameters"] = tool.parameters
            print(json.dumps(info, indent=2, default=str))
        else:
            valid = sorted([t.name for t in tools_obj])
            axi_error(f"Unknown tool: '{tool_name}'", f"Valid tools: {', '.join(valid)}")
    except Exception as e:
        axi_error(f"Failed to load tool info: {e}")
    sys.exit(0)


def show_help() -> None:
    """Show usage information (AXI §10)."""
    print("reddit-httpx v0.1.0")
    print("Reddit MCP server — browsing, posting, commenting, voting, and moderation")
    print()
    print("Usage:")
    print("  reddit-httpx                    Show home view with live state")
    print("  reddit-httpx --list-tools       List all available MCP tools")
    print("  reddit-httpx --tool-info <name> Show details for a specific tool")
    print("  reddit-httpx --login            Import cookies from browser")
    print("  reddit-httpx --logout           Clear stored session")
    print("  reddit-httpx --status           Check authentication status")
    print("  reddit-httpx --help             Show this help message")
    print()
    print("Examples:")
    print("  reddit-httpx --tool-info search_posts")
    print("  reddit-httpx --list-tools")
    print("  reddit-httpx --login")


def main():
    parser = argparse.ArgumentParser(description="Reddit MCP Server", add_help=False)
    parser.add_argument("--login", action="store_true", help="Import cookies from browser")
    parser.add_argument("--logout", action="store_true", help="Clear stored session")
    parser.add_argument("--status", action="store_true", help="Check authentication status")
    parser.add_argument("--list-tools", action="store_true", help="List all available MCP tools")
    parser.add_argument("--tool-info", type=str, metavar="TOOL", help="Show details for a specific tool")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio", help="MCP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    parser.add_argument("--help", "-h", action="store_true", help="Show help message")
    args, unknown = parser.parse_known_args()

    # AXI §6: Fail loud on unrecognized input
    if unknown:
        axi_error(f"Unknown flag: '{unknown[0]}'", "Run `reddit-httpx --help` for usage")

    if args.help:
        show_help()
        return

    if args.list_tools:
        list_tools_and_exit()

    if args.tool_info:
        tool_info_and_exit(args.tool_info)

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

    # Start MCP server
    from reddit_mcp_server.bootstrap import initialize_bootstrap
    from reddit_mcp_server.server import create_mcp_server

    initialize_bootstrap()
    mcp = create_mcp_server()

    if len(sys.argv) == 1:
        if sys.stdin.isatty():
            # Interactive terminal: show home view (CLI mode)
            show_home_view()
            return
        # Pipe from MCP client (e.g. Claude Desktop): start server
        mcp.run(transport="stdio")
    elif args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()