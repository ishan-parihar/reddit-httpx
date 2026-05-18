import asyncio
from typing import Any
from curl_cffi.requests import AsyncSession
from reddit_mcp_server.constants import (
    REDDIT_BASE_URL, DEFAULT_USER_AGENT, MAX_RETRIES, RETRY_BACKOFF, RATE_LIMIT_SLEEP,
)
from reddit_mcp_server.exceptions import (
    AuthenticationError, RateLimitError, SessionExpiredError, RedditMCPError,
)
from reddit_mcp_server.logging_config import logger


class RedditAPIClient:
    def __init__(self, cookies: dict[str, str]):
        self._cookies = cookies
        self._session: AsyncSession | None = None
        self._modhash: str | None = None

    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(impersonate="chrome")
            for name, value in self._cookies.items():
                self._session.cookies.set(name, value, domain=".reddit.com")
        return self._session

    async def _ensure_modhash(self) -> str:
        if self._modhash:
            return self._modhash
        data = await self._get("/api/me.json")
        self._modhash = data.get("data", {}).get("modhash", "")
        return self._modhash

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        session = await self._get_session()
        url = f"{REDDIT_BASE_URL}{path}" if path.startswith("/") else path
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        kwargs.setdefault("headers", {}).update(headers)

        for attempt in range(MAX_RETRIES):
            try:
                resp = await session.request(method, url, **kwargs)
                if resp.status_code == 429:
                    wait = RATE_LIMIT_SLEEP * (attempt + 1)
                    logger.warning(f"Rate limited, sleeping {wait}s")
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code in (401, 403):
                    text = resp.text
                    if "login" in text.lower() or resp.status_code == 401:
                        raise SessionExpiredError("Session expired")
                    raise AuthenticationError(f"Auth error {resp.status_code}")
                if resp.status_code >= 500:
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))
                        continue
                    raise RedditMCPError(f"Server error {resp.status_code}")
                resp.raise_for_status()
                if not resp.text.strip():
                    return {"status": "ok", "data": None}
                result = resp.json()
                # Reddit returns '"{}"' (string) for unauthenticated endpoints
                if isinstance(result, str):
                    return {"status": "requires_auth", "data": None, "raw": result}
                return result
            except (AuthenticationError, SessionExpiredError, RateLimitError):
                raise
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
                raise RedditMCPError(f"Request failed: {e}") from e
        raise RateLimitError()

    async def _get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, data: dict | None = None) -> Any:
        modhash = await self._ensure_modhash()
        if data is None:
            data = {}
        data["uh"] = modhash
        data["api_type"] = "json"
        return await self._request("POST", path, data=data)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    # === Identity ===
    async def me(self) -> dict:
        return await self._get("/api/me.json")

    # === Browse ===
    async def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 25, time_filter: str = "day", after: str | None = None) -> dict:
        params = {"limit": limit, "raw_json": 1, "t": time_filter}
        if after:
            params["after"] = after
        return await self._get(f"/r/{subreddit}/{sort}.json", params=params)

    async def get_frontpage(self, sort: str = "best", limit: int = 25, after: str | None = None) -> dict:
        params = {"limit": limit, "raw_json": 1}
        if after:
            params["after"] = after
        return await self._get(f"/{sort}.json", params=params)

    async def get_popular(self, limit: int = 25) -> dict:
        return await self._get("/r/popular/hot.json", params={"limit": limit, "raw_json": 1})

    # === Search ===
    async def search(self, query: str, subreddit: str | None = None, sort: str = "relevance", time_filter: str = "all", limit: int = 25) -> dict:
        params = {"q": query, "sort": sort, "t": time_filter, "limit": limit, "raw_json": 1, "type": "link"}
        path = f"/r/{subreddit}/search.json" if subreddit else "/search.json"
        if subreddit:
            params["restrict_sr"] = "on"
        return await self._get(path, params=params)

    async def search_subreddits(self, query: str, limit: int = 10) -> dict:
        return await self._get("/subreddits/search.json", params={"q": query, "limit": limit, "raw_json": 1})

    async def search_users(self, query: str, limit: int = 10) -> dict:
        return await self._get("/users/search.json", params={"q": query, "limit": limit, "raw_json": 1})

    # === Posts ===
    async def get_post(self, subreddit: str, post_id: str, sort: str = "best", limit: int = 50) -> list:
        params = {"sort": sort, "limit": limit, "raw_json": 1}
        return await self._get(f"/r/{subreddit}/comments/{post_id}.json", params=params)

    async def get_post_by_id(self, post_id: str, sort: str = "best", limit: int = 50) -> list:
        params = {"sort": sort, "limit": limit, "raw_json": 1}
        return await self._get(f"/comments/{post_id}.json", params=params)

    # === User ===
    async def get_user(self, username: str) -> dict:
        return await self._get(f"/user/{username}/about.json", params={"raw_json": 1})

    async def get_user_posts(self, username: str, sort: str = "new", limit: int = 25) -> dict:
        return await self._get(f"/user/{username}/submitted.json", params={"sort": sort, "limit": limit, "raw_json": 1})

    async def get_user_comments(self, username: str, sort: str = "new", limit: int = 25) -> dict:
        return await self._get(f"/user/{username}/comments.json", params={"sort": sort, "limit": limit, "raw_json": 1})

    # === Submit ===
    async def submit_text(self, subreddit: str, title: str, text: str = "", flair_id: str | None = None, nsfw: bool = False, spoiler: bool = False) -> dict:
        data = {"sr": subreddit, "kind": "self", "title": title, "text": text, "nsfw": nsfw, "spoiler": spoiler}
        if flair_id:
            data["flair_id"] = flair_id
        return await self._post("/api/submit", data=data)

    async def submit_link(self, subreddit: str, title: str, url: str, flair_id: str | None = None, nsfw: bool = False) -> dict:
        data = {"sr": subreddit, "kind": "link", "title": title, "url": url, "nsfw": nsfw}
        if flair_id:
            data["flair_id"] = flair_id
        return await self._post("/api/submit", data=data)

    async def edit_post(self, thing_id: str, text: str) -> dict:
        return await self._post("/api/editusertext", data={"thing_id": thing_id, "text": text})

    async def delete_thing(self, thing_id: str) -> dict:
        return await self._post("/api/del", data={"id": thing_id})

    # === Comments ===
    async def comment(self, parent_id: str, text: str) -> dict:
        return await self._post("/api/comment", data={"thing_id": parent_id, "text": text})

    async def edit_comment(self, thing_id: str, text: str) -> dict:
        return await self._post("/api/editusertext", data={"thing_id": thing_id, "text": text})

    # === Vote ===
    async def vote(self, thing_id: str, direction: int) -> dict:
        return await self._post("/api/vote", data={"id": thing_id, "dir": str(direction)})

    # === Save ===
    async def save(self, thing_id: str) -> dict:
        return await self._post("/api/save", data={"id": thing_id})

    async def unsave(self, thing_id: str) -> dict:
        return await self._post("/api/unsave", data={"id": thing_id})

    async def hide(self, thing_id: str) -> dict:
        return await self._post("/api/hide", data={"id": thing_id})

    async def unhide(self, thing_id: str) -> dict:
        return await self._post("/api/unhide", data={"id": thing_id})

    async def get_saved(self, username: str, limit: int = 25) -> dict:
        return await self._get(f"/user/{username}/saved.json", params={"limit": limit, "raw_json": 1})

    # === Messaging ===
    async def get_inbox(self, where: str = "inbox", limit: int = 25) -> dict:
        return await self._get(f"/message/{where}.json", params={"limit": limit, "raw_json": 1})

    async def send_message(self, to: str, subject: str, body: str) -> dict:
        return await self._post("/api/compose", data={"to": to, "subject": subject, "text": body})

    async def read_message(self, thing_id: str) -> dict:
        return await self._post("/api/read_message", data={"id": thing_id})

    # === Subreddit ===
    async def subscribe(self, subreddit: str) -> dict:
        return await self._post("/api/subscribe", data={"sr_name": subreddit, "action": "sub"})

    async def unsubscribe(self, subreddit: str) -> dict:
        return await self._post("/api/subscribe", data={"sr_name": subreddit, "action": "unsub"})

    async def get_subreddit_info(self, subreddit: str) -> dict:
        return await self._get(f"/r/{subreddit}/about.json", params={"raw_json": 1})

    async def get_my_subreddits(self, limit: int = 100) -> dict:
        return await self._get("/subreddits/mine/subscriber.json", params={"limit": limit, "raw_json": 1})

    # === Account ===
    async def get_friends(self) -> dict:
        return await self._get("/api/v1/me/friends.json", params={"raw_json": 1})

    async def add_friend(self, username: str) -> dict:
        return await self._request("PUT", f"/api/v1/me/friends/{username}", json={"name": username})

    async def remove_friend(self, username: str) -> dict:
        return await self._request("DELETE", f"/api/v1/me/friends/{username}")

    # === Moderation ===
    async def mod_remove(self, thing_id: str, spam: bool = False) -> dict:
        return await self._post("/api/remove", data={"id": thing_id, "spam": spam})

    async def mod_approve(self, thing_id: str) -> dict:
        return await self._post("/api/approve", data={"id": thing_id})

    async def mod_distinguish(self, thing_id: str, how: str = "yes") -> dict:
        return await self._post("/api/distinguish", data={"id": thing_id, "how": how})

    async def mod_sticky(self, thing_id: str, state: bool = True) -> dict:
        return await self._post("/api/set_subreddit_sticky", data={"id": thing_id, "state": state})

    async def mod_lock(self, thing_id: str) -> dict:
        return await self._post("/api/lock", data={"id": thing_id})

    async def mod_unlock(self, thing_id: str) -> dict:
        return await self._post("/api/unlock", data={"id": thing_id})
