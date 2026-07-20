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
