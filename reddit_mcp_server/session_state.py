import os
import json
import shutil
from pathlib import Path
from reddit_mcp_server.constants import DEFAULT_PROFILE_DIR, COOKIES_FILE

OLD_PROFILE_DIR = "~/.reddit-httpx"


def get_profile_dir() -> Path:
    d = Path(os.environ.get("REDDIT_MCP_PROFILE_DIR", DEFAULT_PROFILE_DIR)).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _has_usable_cookies(path: Path) -> bool:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    cookies = data.get("cookies", data)
    return isinstance(cookies, dict) and any(
        isinstance(v, str) and v for v in cookies.values()
    )


def _migrate_if_needed() -> None:
    """Copy cookies from ~/.reddit-httpx/ to ~/.reddit-lyr/ if the active file
    is missing or holds no usable cookies (e.g. a corrupt/empty file that would
    otherwise strand valid legacy cookies)."""
    old = Path(OLD_PROFILE_DIR).expanduser() / COOKIES_FILE
    new = get_profile_dir() / COOKIES_FILE
    if old.exists() and (not new.exists() or not _has_usable_cookies(new)):
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old, new)


def get_cookies_path() -> Path:
    _migrate_if_needed()
    return get_profile_dir() / COOKIES_FILE


def load_cookies() -> dict[str, str]:
    path = get_cookies_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("cookies", data) if isinstance(data, dict) else {}


def save_cookies(cookies: dict[str, str]) -> None:
    path = get_cookies_path()
    path.write_text(json.dumps({"cookies": cookies}, indent=2))


def clear_cookies() -> None:
    path = get_cookies_path()
    if path.exists():
        path.unlink()
