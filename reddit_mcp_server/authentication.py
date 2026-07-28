from reddit_mcp_server.session_state import load_cookies
from reddit_mcp_server.logging_config import logger

REQUIRED_COOKIES = ["reddit_session"]


def validate_session() -> bool:
    cookies = load_cookies()
    if not cookies:
        return False
    for name in REQUIRED_COOKIES:
        if name not in cookies:
            # Also check token_v2 as alternative
            if "token_v2" not in cookies:
                logger.warning(f"Missing required cookie: {name}")
                return False
    return True


def get_auth_status() -> dict:
    cookies = load_cookies()
    if not cookies:
        return {"authenticated": False, "reason": "No cookies stored"}
    has_session = "reddit_session" in cookies or "token_v2" in cookies
    return {
        "authenticated": has_session,
        "cookies_count": len(cookies),
        "has_session": "reddit_session" in cookies,
        "has_token": "token_v2" in cookies,
        "has_csrf": "csrf_token" in cookies,
    }
