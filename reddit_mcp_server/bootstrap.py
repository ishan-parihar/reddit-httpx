import os
import json
from reddit_mcp_server.session_state import load_cookies, save_cookies
from reddit_mcp_server.authentication import validate_session
from reddit_mcp_server.logging_config import logger

def initialize_bootstrap() -> bool:
    env_cookies = os.environ.get("REDDIT_COOKIES")
    if env_cookies:
        try:
            cookies = json.loads(env_cookies)
            if isinstance(cookies, dict):
                save_cookies(cookies)
                logger.info("Loaded cookies from REDDIT_COOKIES env var")
        except json.JSONDecodeError:
            logger.error("Invalid JSON in REDDIT_COOKIES env var")
            return False
    return validate_session()

def ensure_ready_or_raise() -> dict[str, str]:
    cookies = load_cookies()
    if not cookies:
        raise RuntimeError("Not authenticated. Run `reddit-httpx --login`, `reddit-httpx --cookies-file <path>`, or set REDDIT_COOKIES env var.")
    if not validate_session():
        raise RuntimeError("Session invalid. Run `reddit-httpx --login` to re-authenticate.")
    return cookies
