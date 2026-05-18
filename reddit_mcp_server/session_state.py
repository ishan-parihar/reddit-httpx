import os
import json
from pathlib import Path
from reddit_mcp_server.constants import DEFAULT_PROFILE_DIR, COOKIES_FILE

def get_profile_dir() -> Path:
    d = Path(os.environ.get("REDDIT_MCP_PROFILE_DIR", DEFAULT_PROFILE_DIR)).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_cookies_path() -> Path:
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
