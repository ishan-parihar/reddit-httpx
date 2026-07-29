from reddit_mcp_server.session_state import load_cookies
from reddit_mcp_server.logging_config import logger


def validate_session() -> bool:
    """Check if cookies exist. Returns True if at least one auth cookie is present."""
    cookies = load_cookies()
    if not cookies:
        return False
    return "reddit_session" in cookies or "token_v2" in cookies


def validate_write_session() -> bool:
    """Check if write operations are supported. Writes require reddit_session."""
    cookies = load_cookies()
    return "reddit_session" in cookies


def get_auth_status() -> dict:
    cookies = load_cookies()
    if not cookies:
        return {"authenticated": False, "reason": "No cookies stored"}
    has_session = "reddit_session" in cookies
    has_token = "token_v2" in cookies
    if has_session and has_token:
        mode = "full"
    elif has_token:
        mode = "reads_only"
    elif has_session:
        mode = "degraded"
    else:
        mode = "none"
    return {
        "authenticated": has_session or has_token,
        "mode": mode,
        "cookies_count": len(cookies),
        "has_session": has_session,
        "has_token": has_token,
        "has_csrf": "csrf_token" in cookies,
    }
