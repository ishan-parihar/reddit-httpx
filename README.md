# reddit-httpx

> **56 MCP tools** for complete Reddit automation — browsing, posting, commenting, voting, messaging, moderation, and engagement. Uses browser cookies + Chrome TLS fingerprint impersonation so every request looks like a real browser.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why This Exists

Reddit's official API is heavily rate-limited (60 req/min), requires OAuth app registration, and restricts many operations. This project takes a different approach:

- **Browser cookie authentication** — no API keys, no OAuth dance, no scope limitations
- **TLS fingerprint impersonation** via `curl_cffi` — requests are indistinguishable from a real Chrome browser at the network level (JA3/JA4 fingerprints match)
- **56 MCP tools** covering the full Reddit experience — from reading to posting to moderating
- **Zero browser automation** — pure HTTP, no Playwright/Selenium overhead
- **Rate-limit-aware** — pre-throttles from `X-Ratelimit-Remaining` headers, respects `Retry-After` on 429s
- **Token-efficient output** — normalizes Reddit's 100+ field responses to ~15 fields per post, truncates long text at 500 chars

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 AI Agent (Claude, etc.)                   │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP Protocol (stdio / HTTP)
┌──────────────────────────▼──────────────────────────────┐
│                    FastMCP Server                         │
│                                                          │
│  14 Tool Modules (56 tools)                              │
│  ┌────────┬────────┬────────┬────────┬────────┐         │
│  │ Browse │ Search │ Posts  │  User  │ Submit │         │
│  │  3     │  3     │  2     │  4     │  4     │         │
│  ├────────┼────────┼────────┼────────┼────────┤         │
│  │Comment │  Vote  │Message │Subreddit│ Save  │         │
│  │  4     │  1     │  3     │  4      │  5    │         │
│  ├────────┼────────┼────────┼────────┼────────┤         │
│  │Account │  Mod   │Engage  │  Info  │        │         │
│  │  4     │  6     │  9     │  4     │        │         │
│  └────────┴────────┴────────┴────────┴────────┘         │
│                           │                               │
│  ┌────────────────────────▼─────────────────────┐       │
│  │         Response Normalizer                    │       │
│  │  Reddit 100+ fields → ~15 clean fields/post   │       │
│  │  Long text truncated at 500 chars              │       │
│  └────────────────────────┬─────────────────────┘       │
│                           │                               │
│  ┌────────────────────────▼─────────────────────┐       │
│  │           Rate Limiter                        │       │
│  │  X-Ratelimit-Remaining → pre-throttle         │       │
│  │  Retry-After on 429 → exact sleep             │       │
│  └────────────────────────┬─────────────────────┘       │
│                           │                               │
│  ┌────────────────────────▼─────────────────────┐       │
│  │         RedditAPIClient                       │       │
│  │  curl_cffi + Chrome TLS impersonation         │       │
│  │  Structured errors with code + retry_after    │       │
│  └────────────────────────┬─────────────────────┘       │
│                           │                               │
│  ┌────────────────────────▼─────────────────────┐       │
│  │         Cookie Manager                        │       │
│  │  5 browsers: Brave/Chrome/Firefox/Edge/Zen    │       │
│  │  AES-128-CBC decryption (Chromium)            │       │
│  └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                           │
                    HTTPS (Chrome TLS)
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   www.reddit.com                          │
│              (sees a normal Chrome browser)               │
└─────────────────────────────────────────────────────────┘
```

## Tools

56 tools across 14 categories:

| Category | Count | Tools |
|----------|------:|-------|
| **Browse** | 3 | `browse_subreddit`, `browse_frontpage`, `browse_popular` |
| **Search** | 3 | `search_posts`, `search_subreddits`, `search_users` |
| **Posts** | 2 | `get_post`, `get_post_comments` |
| **User** | 4 | `get_user_profile`, `get_user_posts`, `get_user_comments`, `get_my_profile` |
| **Submit** | 4 | `submit_text_post`, `submit_link_post`, `edit_post`, `delete_post` |
| **Comments** | 4 | `comment`, `reply`, `edit_comment`, `delete_comment` |
| **Vote** | 1 | `vote` (up/down/none) |
| **Messaging** | 3 | `get_inbox`, `send_dm`, `mark_read` |
| **Subreddit** | 4 | `subscribe`, `unsubscribe`, `get_subreddit_info`, `get_my_subscriptions` |
| **Save** | 5 | `save`, `unsave`, `hide`, `unhide`, `get_saved` |
| **Account** | 4 | `get_account_info`, `add_friend`, `remove_friend`, `get_friends` |
| **Moderation** | 6 | `remove`, `approve`, `distinguish`, `undistinguish`, `sticky`, `unsticky`, `lock`, `unlock` |
| **Engagement** | 9 | `report`, `block_user`, `follow_post`, `sendreplies`, `read_all_messages`, `marknsfw`, `unmarknsfw`, `spoiler`, `unspoiler` |
| **Info** | 4 | `get_karma`, `get_user_overview`, `get_subreddit_rules`, `get_subreddit_moderators` |

## Quick Start

### Install

```bash
curl -sSL https://raw.githubusercontent.com/ishan-parihar/reddit-httpx/main/install.sh | bash
```

This installs `reddit-httpx` globally via pipx or pip. Requires Python 3.12+.

<details>
<summary>Manual install</summary>

```bash
git clone https://github.com/ishan-parihar/reddit-httpx.git
cd reddit-httpx
pip install -e .
```

</details>

### Authenticate

```bash
# Import cookies from your browser (interactive)
reddit-httpx --login

# Check status
reddit-httpx --status
```

Or set cookies directly:
```bash
export REDDIT_COOKIES='{"reddit_session": "...", "token_v2": "..."}'
```

### Run the Server

```bash
# stdio transport (for Claude Desktop, Cursor, etc.)
reddit-httpx

# HTTP transport (for remote clients)
reddit-httpx --transport streamable-http --port 8000
```

### MCP Client Config

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "reddit": {
      "command": "reddit-httpx",
      "args": []
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "reddit": {
      "command": "reddit-httpx",
      "transportType": "stdio"
    }
  }
}
```

## Usage

```
"Browse the top posts on r/programming this week"
→ browse_subreddit(subreddit="programming", sort="top", time_filter="week")

"Search for posts about Rust async"
→ search_posts(query="rust async", limit=10)

"Get u/spez's profile"
→ get_user_profile(username="spez")

"Post to r/test"
→ submit_text_post(subreddit="test", title="Hello", text="World")

"Upvote this post"
→ vote(thing_id="t3_abc123", direction="up")

"Reply to this comment"
→ reply(comment_id="t1_xyz789", text="Great point!")

"Get my karma breakdown"
→ get_karma()
```

## Project Structure

```
reddit-httpx/
├── pyproject.toml
├── reddit_mcp_server/
│   ├── cli_main.py              # CLI: --login, --status, --transport, --list-tools
│   ├── server.py                # FastMCP server + tool registration
│   ├── normalizer.py            # Flatten Reddit responses (~15 fields per post)
│   ├── ratelimit.py             # Sliding-window throttle from X-Ratelimit-* headers
│   ├── scraping/
│   │   └── api_client.py        # RedditAPIClient (curl_cffi, retry, rate-limit, errors)
│   ├── cookie_import.py         # Browser cookie extraction + AES decryption
│   ├── session_state.py         # Cookie persistence (~/.reddit-mcp/)
│   ├── authentication.py        # Session validation
│   ├── bootstrap.py             # Startup initialization
│   ├── dependencies.py          # Lazy client singleton
│   ├── constants.py             # URLs, timeouts, user-agent
│   ├── exceptions.py            # Error hierarchy
│   ├── error_handler.py         # Centralized error handling
│   └── tools/                   # 14 tool modules, 56 tools total
│       ├── browse.py            # Subreddit/frontpage browsing
│       ├── search.py            # Search posts/subreddits/users
│       ├── posts.py             # Post details + comments
│       ├── user.py              # User profiles & history
│       ├── submit.py            # Create/edit/delete posts
│       ├── comments.py          # Comment/reply/edit/delete
│       ├── vote.py              # Upvote/downvote/unvote
│       ├── messaging.py         # DMs & inbox
│       ├── subreddit.py         # Subscribe/unsubscribe
│       ├── save.py              # Save/hide posts
│       ├── account.py           # Account & friends
│       ├── moderation.py        # Mod actions
│       ├── engagement.py        # Report, block, follow, NSFW/spoiler
│       └── info.py              # Karma, overview, rules, moderators
└── tests/
    └── test_axi_cli_wrappers.py
```

## Technical Details

### Why curl_cffi?

Reddit uses TLS fingerprinting to detect automated clients. Standard Python HTTP libraries (httpx, requests, aiohttp) have distinctive TLS handshakes that differ from real browsers. `curl_cffi` wraps libcurl with browser impersonation — it reproduces Chrome's exact:

- TLS extensions and ordering
- ALPN protocols
- Cipher suite preferences
- JA3/JA4 fingerprint hash

Requests are cryptographically indistinguishable from a real Chrome browser.

### Browser Cookies vs OAuth

| | Browser Cookies | OAuth API |
|---|---|---|
| Rate limits | Browser-level (generous) | 60 req/min (strict) |
| Scope | Full access | Limited by scopes |
| Registration | None needed | App registration required |
| 2FA accounts | Works | Doesn't work |
| Detection risk | Minimal (looks like browser) | Flagged as bot |

### Response Normalization

Reddit wraps everything in `data.children[].data` with 100+ fields per object. The normalizer extracts only what matters:

| Before | After |
|--------|-------|
| `{"data": {"children": [{"data": {"title": "...", "selftext": "...", "score": 1, ...100 fields}}]}}` | `{"items": [{"id": "...", "title": "...", "score": 1, "num_comments": 5, ...}], "next": "t3_xxx", "count": 1}` |

Long `selftext` and `body` fields are truncated at 500 characters with a separate `_chars` field preserving the original length.

### Cookie Extraction

Automatically extracts and decrypts Reddit cookies from:

- **Brave** (Linux/macOS)
- **Chrome** (Linux/macOS)
- **Firefox** (Linux/macOS)
- **Edge** (Linux/macOS)
- **Zen** (Linux/macOS)

Handles Chromium's AES-128-CBC cookie encryption (PBKDF2 key derivation from `saltysalt`).

### Error Handling

- **429 Rate Limit** — sleeps for exact `Retry-After` duration (no guessing)
- **401/403 Auth** — clear error message directing to `reddit-httpx --login`
- **500 Server** — 3 retries with exponential backoff
- **Session Expired** — detected via `USER_REQUIRED` in 2xx response bodies
- **Non-JSON responses** — handled gracefully (e.g., `read_all_messages` returns 202 with text)

All errors include a `code` field (`rate_limited`, `auth_required`, `api_error`) and `retry_after` when applicable.

### CLI

```bash
# List all 56 registered tools
reddit-httpx --list-tools

# Get details for a specific tool
reddit-httpx --tool-info browse_subreddit

# Check authentication status
reddit-httpx --status

# Import cookies from browser
reddit-httpx --login
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDDIT_COOKIES` | JSON dict of cookies (alternative to `--login`) | — |
| `REDDIT_MCP_PROFILE_DIR` | Config directory | `~/.reddit-mcp` |
| `REDDIT_MCP_LOG_LEVEL` | Logging level | `INFO` |

## Development

```bash
pip install -e ".[dev]"

# Lint
ruff check reddit_mcp_server/

# Format
ruff format reddit_mcp_server/

# Test
pytest
```

---

Developed by [Ishan Parihar](https://github.com/ishan-parihar) — If you find this useful, [consider supporting](https://rzp.io/rzp/ishan-parihar)
