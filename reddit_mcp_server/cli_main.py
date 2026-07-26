import json
import os
import sys
import argparse
import logging

# ── TOON output helpers (AXI §1) ──────────────────────────────────────────

def _toon_quote(val: str) -> str:
    """Quote a string value per TOON spec when it contains special chars."""
    if val == "":
        return '""'
    # Must quote: looks like bool/number, contains delimiter/colon/bracket, starts with -
    needs_quote = (
        val in ("true", "false", "null") or
        val.lstrip("-").replace(".", "", 1).replace("e", "", 1).replace("+", "", 1).isdigit() or
        any(c in val for c in (":", ",", '"', "[", "]", "{", "}", "#")) or
        val.startswith("-") or val.startswith("#") or
        val.startswith(" ") or val.endswith(" ") or
        val.startswith('"') or val.endswith('"')
    )
    if needs_quote:
        escaped = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return val


def _toon_kv(key: str, val) -> str:
    """Emit a single key: value TOON line."""
    if isinstance(val, bool):
        return f"{key}: {'true' if val else 'false'}"
    if isinstance(val, (int, float)):
        return f"{key}: {val}"
    return f"{key}: {_toon_quote(str(val))}"


def axi_error(msg: str, hint: str = None) -> None:
    """Print structured error in TOON format (AXI §6) and exit with code 2."""
    print(_toon_kv("error", msg))
    if hint:
        print(_toon_kv("help", hint))
    sys.exit(2)


def _toon_object(fields: dict) -> str:
    """Render a flat or one-level-nested object as TOON text."""
    lines = []
    for k, v in fields.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for sk, sv in v.items():
                lines.append(f"  {_toon_kv(sk, sv)}")
        elif isinstance(v, list):
            # list of dicts → tabular
            if v and isinstance(v[0], dict):
                keys = list(v[0].keys())
                hdr = ",".join(keys)
                lines.append(f"{k}[{len(v)}]{{{hdr}}}:")
                for item in v:
                    cells = ",".join(_toon_quote(str(item.get(fk, ""))) for fk in keys)
                    lines.append(f"  {cells}")
            else:
                # primitive list
                items = ",".join(_toon_quote(str(x)) for x in v)
                lines.append(f"{k}[{len(v)}]: {items}")
        else:
            lines.append(_toon_kv(k, v))
    return "\n".join(lines)


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


# ponytail: lazy — _discover_tools() calls create_mcp_server() which logs;
# defer past dup2 so the handler captures /devnull stderr, not the original.
_TOOLS_CACHE = None


def _get_tools() -> list[tuple[str, str]]:
    global _TOOLS_CACHE
    if _TOOLS_CACHE is None:
        _TOOLS_CACHE = _discover_tools()
    return _TOOLS_CACHE


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
        print(f"  help: Run `reddit-httpx --login` or `reddit-httpx --cookies-file <path>`")
    print()

    # Tool listing in TOON format (AXI §2: minimal schema)
    tools = _get_tools()
    print(f"tools[{len(tools)}]{{name,description}}:")
    for name, desc in tools:
        print(f"  {name},{_truncate(desc)}")
    print()

    # AXI §9: Contextual disclosure
    print("help[5]:")
    print("  Run `reddit-httpx --tool-info <name>` for detailed parameters")
    print("  Run `reddit-httpx --list-tools` to see all tools")
    print("  Run `reddit-httpx --login` to import browser cookies")
    print("  Run `reddit-httpx --cookies-file <path>` to import cookies from JSON")
    print("  Run `reddit-httpx` to start the MCP server")


def list_tools_and_exit() -> None:
    """List all available MCP tools and exit (AXI §8 content-first)."""
    tools = _get_tools()
    print(f"tools[{len(tools)}]{{name,description}}:")
    for name, desc in tools:
        print(f"  {name},{desc}")
    print()
    print("help[2]:")
    print("  Run `reddit-httpx --tool-info <name>` for details")
    print("  Run `reddit-httpx` to start the MCP server")
    sys.exit(0)


def tool_info_and_exit(tool_name: str) -> None:
    """Show detailed info for a specific tool in TOON format."""
    try:
        import asyncio
        from reddit_mcp_server.server import create_mcp_server
        mcp = create_mcp_server()
        tools_obj = asyncio.run(mcp.list_tools())
        tool = next((t for t in tools_obj if t.name == tool_name), None)
        if tool:
            fields = {"name": tool.name, "description": tool.description or ""}
            # Flatten schema to TOON param list (AXI §2: minimal schemas)
            schema = getattr(tool, "inputSchema", None) or getattr(tool, "parameters", None) or {}
            if isinstance(schema, dict):
                props = schema.get("properties", {})
                required = set(schema.get("required", []))
                if props:
                    params = []
                    for pname, pdef in props.items():
                        params.append({
                            "name": pname,
                            "type": pdef.get("type", "any"),
                            "required": "true" if pname in required else "false",
                            "description": pdef.get("description", "")[:80]
                        })
                    fields["params"] = params
            print(_toon_object(fields))
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
    print("  reddit-httpx --cookies-file F   Import cookies from a JSON file")
    print("  reddit-httpx --logout           Clear stored session")
    print("  reddit-httpx --status           Check authentication status")
    print("  reddit-httpx --help             Show this help message")
    print()
    print("Environment:")
    print("  REDDIT_COOKIES     JSON string of cookies (loaded at server startup)")
    print("  REDDIT_MCP_LOG_LEVEL  Log level: DEBUG, INFO, WARNING, ERROR")
    print()
    print("Examples:")
    print("  reddit-httpx --tool-info search_posts")
    print("  reddit-httpx --list-tools")
    print("  reddit-httpx --login")
    print("  reddit-httpx --cookies-file ~/reddit-cookies.json")


def main():
    parser = argparse.ArgumentParser(description="Reddit MCP Server", add_help=False)
    parser.add_argument("--login", action="store_true", help="Import cookies from browser")
    parser.add_argument("--cookies-file", type=str, metavar="PATH", help="Import cookies from a JSON file")
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
            print(_toon_object({"status": "success", "message": "Cookies saved."}))
        else:
            axi_error("Login failed. No cookies extracted.", "Ensure you are logged into Reddit in your browser.")
        return

    if args.cookies_file:
        from reddit_mcp_server.session_state import save_cookies
        from pathlib import Path
        path = Path(args.cookies_file)
        if not path.exists():
            axi_error(f"File not found: {args.cookies_file}", "Check the path and try again.")
        try:
            data = json.loads(path.read_text())
            cookies = data.get("cookies", data) if isinstance(data, dict) else data
            if not isinstance(cookies, dict) or not cookies:
                axi_error("Invalid cookies file.", "Expected JSON object with cookie names as keys.")
            save_cookies(cookies)
            print(_toon_object({"status": "success", "message": f"Imported {len(cookies)} cookies from {path.name}."}))
        except json.JSONDecodeError:
            axi_error("Invalid JSON in cookies file.", "File must contain valid JSON.")
        return

    if args.logout:
        from reddit_mcp_server.session_state import clear_cookies
        clear_cookies()
        print(_toon_object({"status": "success", "message": "Logged out. Cookies cleared."}))
        return

    if args.status:
        from reddit_mcp_server.bootstrap import initialize_bootstrap
        from reddit_mcp_server.authentication import get_auth_status
        initialize_bootstrap()  # loads REDDIT_COOKIES env var if present
        status = get_auth_status()
        print(_toon_object({"status": "ok", "auth": status}))
        return

    # Detect interactive vs MCP-client invocation early so we can suppress
    # logging noise before any server code runs (AXI §1: clean stderr for agents).
    interactive = sys.stdin.isatty()
    is_mcp_stdio = (not interactive) or (args.transport == "stdio")

    # In stdio MCP mode, silence ALL stderr output at the OS level.
    # MCP clients read stdout (JSON-RPC) only — all stderr is noise.
    if is_mcp_stdio:
        os.environ["FASTMCP_LOG_LEVEL"] = "WARNING"
        os.environ["REDDIT_MCP_LOG_LEVEL"] = "WARNING"
        # Redirect fd 2 (stderr) to /devnull at the OS level before any imports.
        # This silences logging, FastMCP banner, curl_cffi warnings — everything.
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, sys.stderr.fileno())
        os.close(devnull_fd)
        sys.stderr = open(os.devnull, "w")  # Python-level redirect too

    # Start MCP server
    from reddit_mcp_server.bootstrap import initialize_bootstrap
    from reddit_mcp_server.server import create_mcp_server

    initialize_bootstrap()
    mcp = create_mcp_server()

    if len(sys.argv) == 1:
        if interactive:
            # Interactive terminal: show home view (CLI mode)
            show_home_view()
            return
        # Pipe from MCP client (e.g. Claude Desktop): start server
        mcp.run(transport="stdio", show_banner=False)
    elif is_mcp_stdio:
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()