import os
import sys
import sqlite3
import shutil
import tempfile
from pathlib import Path
from reddit_mcp_server.logging_config import logger

BROWSER_PATHS = {
    "brave": {
        "linux": Path.home() / ".config/BraveSoftware/Brave-Browser/Default/Cookies",
        "darwin": Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies",
    },
    "chrome": {
        "linux": Path.home() / ".config/google-chrome/Default/Cookies",
        "darwin": Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies",
    },
    "firefox": {
        "linux": Path.home() / ".mozilla/firefox",
        "darwin": Path.home() / "Library/Application Support/Firefox/Profiles",
    },
    "edge": {
        "linux": Path.home() / ".config/microsoft-edge/Default/Cookies",
        "darwin": Path.home() / "Library/Application Support/Microsoft Edge/Default/Cookies",
    },
}

def _get_platform() -> str:
    return "darwin" if sys.platform == "darwin" else "linux"

def _find_firefox_cookies() -> Path | None:
    platform = _get_platform()
    base = BROWSER_PATHS["firefox"].get(platform)
    if not base or not base.exists():
        return None
    for profile_dir in base.iterdir():
        cookies_file = profile_dir / "cookies.sqlite"
        if cookies_file.exists():
            return cookies_file
    return None

def _get_chromium_key(browser: str) -> bytes | None:
    """Get the decryption key for Chromium cookies on Linux."""
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        # Linux: key derived from 'peanuts' password with PBKDF2
        kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=16, salt=b"saltysalt", iterations=1)
        return kdf.derive(b"peanuts")
    except Exception as e:
        logger.debug(f"Could not derive chromium key: {e}")
        return None


def _decrypt_chromium_value(encrypted_value: bytes, key: bytes) -> str:
    """Decrypt a Chromium encrypted cookie value on Linux."""
    if not encrypted_value:
        return ""
    if encrypted_value[:3] in (b"v10", b"v11"):
        encrypted_value = encrypted_value[3:]
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            iv = b" " * 16
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_value) + decryptor.finalize()
            # Remove PKCS7 padding
            pad_len = decrypted[-1]
            if isinstance(pad_len, int) and 1 <= pad_len <= 16:
                decrypted = decrypted[:-pad_len]
            # Chromium prepends 16-byte random salt; first 2 blocks (32 bytes) are garbage
            # due to CBC mode with fixed IV not matching the random prefix
            if len(decrypted) > 32:
                return decrypted[32:].decode("utf-8", errors="ignore")
            return decrypted.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def _extract_chromium_cookies(db_path: Path, browser: str = "chrome") -> dict[str, str]:
    if not db_path.exists():
        return {}
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    shutil.copy2(db_path, tmp.name)
    cookies = {}
    try:
        conn = sqlite3.connect(tmp.name)
        # First try unencrypted values
        cursor = conn.execute(
            "SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE '%reddit.com'"
        )
        key = _get_chromium_key(browser)
        for name, value, encrypted_value in cursor.fetchall():
            if value:
                cookies[name] = value
            elif encrypted_value and key:
                decrypted = _decrypt_chromium_value(encrypted_value, key)
                if decrypted:
                    cookies[name] = decrypted
        conn.close()
    finally:
        os.unlink(tmp.name)
    return cookies

def _extract_firefox_cookies(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        return {}
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    shutil.copy2(db_path, tmp.name)
    cookies = {}
    try:
        conn = sqlite3.connect(tmp.name)
        cursor = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE baseDomain LIKE '%reddit.com' AND value != ''"
        )
        for name, value in cursor.fetchall():
            cookies[name] = value
        conn.close()
    finally:
        os.unlink(tmp.name)
    return cookies

def extract_cookies_from_browser(browser: str) -> dict[str, str]:
    platform = _get_platform()
    if browser == "firefox":
        db_path = _find_firefox_cookies()
        if not db_path:
            return {}
        return _extract_firefox_cookies(db_path)
    db_path = BROWSER_PATHS.get(browser, {}).get(platform)
    if not db_path:
        return {}
    return _extract_chromium_cookies(db_path, browser)

def detect_available_browsers() -> list[str]:
    available = []
    platform = _get_platform()
    for browser, paths in BROWSER_PATHS.items():
        if browser == "firefox":
            if _find_firefox_cookies():
                available.append(browser)
        else:
            path = paths.get(platform)
            if path and path.exists():
                available.append(browser)
    return available

def import_cookies_interactive() -> dict[str, str]:
    browsers = detect_available_browsers()
    if not browsers:
        logger.error("No supported browsers found with Reddit cookies.")
        return {}
    if len(browsers) == 1:
        browser = browsers[0]
        logger.info(f"Found cookies in {browser}")
    else:
        try:
            import inquirer
            answers = inquirer.prompt([inquirer.List("browser", message="Select browser", choices=browsers)])
            browser = answers["browser"] if answers else browsers[0]
        except Exception:
            browser = browsers[0]
    cookies = extract_cookies_from_browser(browser)
    if not cookies:
        logger.error(f"No Reddit cookies found in {browser}")
    else:
        logger.info(f"Extracted {len(cookies)} cookies from {browser}")
    return cookies
