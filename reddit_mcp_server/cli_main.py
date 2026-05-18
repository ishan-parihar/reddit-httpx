import sys
import argparse
from reddit_mcp_server.logging_config import logger


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
            logger.info("Login successful. Cookies saved.")
        else:
            logger.error("Login failed. No cookies extracted.")
            sys.exit(1)
        return

    if args.logout:
        from reddit_mcp_server.session_state import clear_cookies
        clear_cookies()
        logger.info("Logged out. Cookies cleared.")
        return

    if args.status:
        from reddit_mcp_server.authentication import get_auth_status
        status = get_auth_status()
        for k, v in status.items():
            print(f"  {k}: {v}")
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
