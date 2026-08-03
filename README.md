# Reddit-Httpx

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![MCP](https://img.shields.io/badge/MCP-1.0-orange?logo=modelcontextprotocol)
![Endpoints](https://img.shields.io/badge/Endpoints-50+-blue)
![Async](https://img.shields.io/badge/Async-httpx-green)


**Complete Reddit API wrapper** — 50+ endpoints, async httpx, MCP server, zero PRAW dependency.

![Reddit-Httpx MCP](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/reddit-lyr-mcp.png)

---

## What it is

| Layer | Description |
|-------|-------------|
| **Core** | `RedditClient` — async, typed, 50+ endpoints |
| **MCP Server** | 32 tools for agents (browse, post, comment, vote, mod) |
| **CLI** | `reddit-lyr browse`, `reddit-lyr post`, `reddit-lyr inbox` |

**Endpoints:** Frontpage, Subreddits, Posts, Comments, Users, Messages, Moderation, Search, Wiki, Live, Collections, Awards, Polls, Predictions

---

## Quick start

```bash
# Install
pipx install reddit-lyr

# Auth (interactive)
reddit-lyr auth login

# Use as library
from reddit_httpx import RedditClient
client = RedditClient()
posts = await client.browse_subreddit("rust", sort="hot", limit=25)

# MCP server for agents
reddit-lyr mcp
```

---

## MCP Tools (32)

| Category | Tools |
|----------|-------|
| **Browse** | `browse_frontpage`, `browse_popular`, `browse_subreddit`, `get_post`, `get_comments` |
| **Post** | `submit_text`, `submit_link`, `edit_post`, `delete_post` |
| **Comment** | `comment`, `reply`, `edit_comment`, `delete_comment` |
| **Vote** | `vote_post`, `vote_comment` |
| **Message** | `get_inbox`, `send_message`, `mark_read` |
| **User** | `get_profile`, `get_karma`, `get_saved` |
| **Mod** | `mod_approve`, `mod_remove`, `mod_lock`, `mod_sticky` |
| **Search** | `search_posts`, `search_subreddits`, `search_users` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RedditClient                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Auth    │  │  Models  │  │  Endpoints│  │  MCP     │     │
│  │  (OAuth) │  │  (Pydantic)│  │  (50+)   │  │  Server  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
           httpx.AsyncClient
           (connection pool, retry, timeout)
```

---

## Example: Agent browsing Reddit

```python
# Agent uses MCP tools:
# 1. browse_subreddit("MachineLearning", sort="hot", limit=10)
# 2. get_post("t3_abc123") → full post + comments
# 3. search_posts("transformer architecture", subreddit="MachineLearning")
# 4. submit_text("r/MySub", "Title", "Body") — with auth
```

---


## Visual proof

| MCP tools | Comment tree | Post detail |
|:---:|:---:|:---:|
| ![Tools](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/tools.png) | ![Comments](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/comments.png) | ![Post](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/post.png) |

| Search results | Mod tools | Message inbox |
|:---:|:---:|:---:|
| ![Search](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/search.png) | ![Mod](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/mod.png) | ![Messages](https://github.com/ishan-parihar/reddit-lyr/raw/main/assets/readme/messages.png) |

## Requirements

- Python 3.11+
- Reddit app credentials (client_id, client_secret)

---

## Related CLI Tools

This project is part of a family of agent-friendly CLI tools for social platforms:

| Tool | CLI | Repo |
|------|-----|------|
| Instagram | `instagram-lyr` | [ishan-parihar/instagram-lyr](https://github.com/ishan-parihar/instagram-lyr) |
| Reddit | `reddit-lyr` | [ishan-parihar/reddit-lyr](https://github.com/ishan-parihar/reddit-lyr) |
| LinkedIn | `linkedin-lyr` | [ishan-parihar/linkedin-lyr](https://github.com/ishan-parihar/linkedin-lyr) |
| Twitter/X | `twitter-lyr` | [ishan-parihar/twitter-lyr](https://github.com/ishan-parihar/twitter-lyr) |
| Discord | `discord` | [ishan-parihar/discord-cli](https://github.com/ishan-parihar/discord-cli) |
| Telegram | `tg` | [ishan-parihar/tg-cli](https://github.com/ishan-parihar/tg-cli) |

---

## License

MIT — see [LICENSE](LICENSE).
