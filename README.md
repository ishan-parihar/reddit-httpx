# reddit-httpx 🤖

> A full-featured Reddit MCP server that uses browser cookies + TLS fingerprint impersonation to give AI agents complete Reddit automation — browsing, posting, commenting, voting, messaging, and moderation.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why This Exists

Reddit's official API is heavily rate-limited, requires OAuth app registration, and restricts many operations. This project takes a different approach:

- **Browser cookie authentication** — no API keys, no OAuth dance, no scope limitations
- **TLS fingerprint impersonation** via `curl_cffi` — requests are indistinguishable from a real Chrome browser at the network level (JA3/JA4 fingerprints match)
- **45 MCP tools** covering the full Reddit experience — from reading to posting to moderating
- **Zero browser automation** — pure HTTP, no Playwright/Selenium overhead

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent (Claude, etc.)                │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP Protocol (stdio/HTTP)
┌──────────────────────────▼──────────────────────────────┐
│                   FastMCP Server                          │
│  ┌─────────┐ ┌────────┐ ┌──────┐ ┌─────┐ ┌──────────┐ │
│  │ Browse  │ │ Search │ │ Post │ │Vote │ │Moderation│ │
│  │ 3 tools │ │3 tools │ │4 tool│ │3 tl │ │ 6 tools  │ │
│  └────┬────┘ └───┬────┘ └──┬───┘ └──┬──┘ └────┬─────┘ │
│       └──────────┴─────────┴────────┴──────────┘        │
│                          │                               │
│              ┌───────────▼────────────┐                  │
│              │   RedditAPIClient      │                  │
│              │   (curl_cffi + Chrome  │                  │
│              │    TLS impersonation)  │                  │
│              └───────────┬────────────┘                  │
│                          │                               │
│              ┌───────────▼────────────┐                  │
│              │   Cookie Manager       │                  │
│              │   (Browser extraction  │                  │
│              │    + AES-CBC decrypt)  │                  │
│              └────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
                           │
                    HTTPS (Chrome TLS)
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   www.reddit.com                          │
│              (sees a normal Chrome browser)               │
└─────────────────────────────────────────────────────────┘
```

## Features

### 45 Tools Across 12 Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **Browse** | 3 | Subreddit feeds, frontpage, r/popular |
| **Search** | 3 | Posts, subreddits, users |
| **Posts** | 2 | Get post details + comment trees |
| **User** | 4 | Profiles, post/comment history, own account |
| **Submit** | 4 | Text posts, link posts, edit, delete |
| **Comments** | 4 | Comment, reply, edit, delete |
| **Vote** | 3 | Upvote, downvote, unvote |
| **Messaging** | 3 | Inbox, send DMs, mark read |
| **Subreddit** | 4 | Subscribe, unsubscribe, info, my subs |
| **Save** | 5 | Save, unsave, hide, unhide, get saved |
| **Account** | 4 | Account info, friends management |
| **Moderation** | 6 | Remove, approve, distinguish, sticky, lock |

### Anti-Detection

- **TLS Fingerprinting**: `curl_cffi` impersonates Chrome's exact TLS handshake (JA3 hash matches real Chrome)
- **Cookie-based auth**: Uses the same session cookies as your browser — Reddit sees identical traffic
- **No OAuth fingerprint**: Avoids the `oauth.reddit.com` endpoint that flags automated clients
- **Realistic headers**: Full Chrome User-Agent, proper Accept headers, X-Requested-With

### Cookie Extraction

Automatically extracts and decrypts Reddit cookies from:
- **Brave** (Linux/macOS)
- **Chrome** (Linux/macOS)
- **Firefox** (Linux/macOS)
- **Edge** (Linux/macOS)

Handles Chromium's AES-128-CBC cookie encryption on Linux (PBKDF2 key derivation from `saltysalt`).

## Quick Start

### Installation

```bash
# Clone
git clone https://github.com/ishan-parihar/reddit-httpx.git
cd reddit-httpx

# Install
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Authentication

```bash
# Import cookies from your browser (interactive)
reddit-mcp --login

# Check status
reddit-mcp --status
# Output:
#   authenticated: True
#   cookies_count: 8
#   has_token: True
```

Or set cookies via environment variable:
```bash
export REDDIT_COOKIES='{"reddit_session": "...", "token_v2": "..."}'
```

### Run the MCP Server

```bash
# stdio transport (for Claude Desktop, Cursor, etc.)
reddit-mcp

# HTTP transport (for remote clients)
reddit-mcp --transport streamable-http --port 8000
```

### MCP Client Configuration

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "reddit": {
      "command": "reddit-mcp",
      "args": []
    }
  }
}
```

**Cursor / VS Code** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "reddit": {
      "command": "reddit-mcp",
      "transportType": "stdio"
    }
  }
}
```

## Usage Examples

Once connected, an AI agent can:

```
"Browse the top posts on r/programming this week"
→ reddit_browse_subreddit(subreddit="programming", sort="top", time_filter="week")

"Search for posts about Rust async"
→ reddit_search_posts(query="rust async", limit=10)

"Get u/spez's profile"
→ reddit_get_user_profile(username="spez")

"Post to r/test"
→ reddit_submit_text_post(subreddit="test", title="Hello", text="World")

"Upvote this post"
→ reddit_upvote(thing_id="t3_abc123")

"Reply to this comment"
→ reddit_reply(comment_id="t1_xyz789", text="Great point!")
```

## Project Structure

```
reddit-httpx/
├── pyproject.toml                    # Dependencies & entry points
├── reddit_mcp_server/
│   ├── cli_main.py                   # CLI: --login, --logout, --status, --transport
│   ├── server.py                     # FastMCP server + tool registration
│   ├── scraping/
│   │   └── api_client.py            # RedditAPIClient (curl_cffi, retry, rate-limit)
│   ├── cookie_import.py             # Browser cookie extraction + AES decryption
│   ├── session_state.py             # Cookie persistence (~/.reddit-mcp/)
│   ├── authentication.py            # Session validation
│   ├── bootstrap.py                 # Startup initialization
│   ├── dependencies.py              # Lazy client singleton
│   ├── constants.py                 # URLs, timeouts, user-agent
│   ├── exceptions.py                # Error hierarchy
│   ├── error_handler.py             # Centralized error handling
│   ├── sequential_middleware.py     # One-tool-at-a-time execution
│   └── tools/                       # 12 tool modules, 45 tools total
│       ├── browse.py                # Subreddit/frontpage browsing
│       ├── search.py                # Search posts/subreddits/users
│       ├── posts.py                 # Post details + comments
│       ├── user.py                  # User profiles & history
│       ├── submit.py                # Create/edit/delete posts
│       ├── comments.py              # Comment/reply/edit/delete
│       ├── vote.py                  # Upvote/downvote/unvote
│       ├── messaging.py             # DMs & inbox
│       ├── subreddit.py             # Subscribe/unsubscribe
│       ├── save.py                  # Save/hide posts
│       ├── account.py               # Account & friends
│       └── moderation.py            # Mod actions
└── PLAN.md                          # Architecture & implementation plan
```

## Technical Details

### Why curl_cffi over httpx/requests?

Reddit uses TLS fingerprinting to detect automated clients. Standard Python HTTP libraries (httpx, requests, aiohttp) have distinctive TLS handshakes that differ from real browsers. `curl_cffi` wraps libcurl with browser impersonation — it reproduces Chrome's exact:

- TLS extensions and ordering
- ALPN protocols
- Cipher suite preferences
- JA3/JA4 fingerprint hash

This makes requests cryptographically indistinguishable from a real Chrome browser.

### Why browser cookies over OAuth?

| | Browser Cookies | OAuth API |
|---|---|---|
| Rate limits | Browser-level (generous) | 60 req/min (strict) |
| Scope | Full access | Limited by scopes |
| Registration | None needed | App registration required |
| 2FA accounts | Works | Doesn't work |
| Detection risk | Minimal (looks like browser) | Flagged as bot |

### Error Handling

- **429 Rate Limit** → Exponential backoff with configurable sleep
- **401/403 Auth** → Clear error message directing to `--login`
- **500 Server** → 3 retries with backoff
- **Session Expired** → Detected and reported cleanly

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Lint
ruff check reddit_mcp_server/

# Format
ruff format reddit_mcp_server/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDDIT_COOKIES` | JSON dict of cookies (alternative to `--login`) | — |
| `REDDIT_MCP_PROFILE_DIR` | Config directory | `~/.reddit-mcp` |
| `REDDIT_MCP_LOG_LEVEL` | Logging level | `INFO` |

## License

MIT

## Acknowledgments

- [curl_cffi](https://github.com/yifeikong/curl_cffi) — Browser-grade TLS impersonation
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- [Model Context Protocol](https://modelcontextprotocol.io) — The protocol standard
---
Developed by [Ishan Parihar](https://github.com/ishan-parihar) — If you find this useful, [consider supporting](https://rzp.io/rzp/ishan-parihar)
