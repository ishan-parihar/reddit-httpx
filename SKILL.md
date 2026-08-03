---
name: reddit-mcp
description: >
  Browse, post, comment, vote, and moderate on Reddit via MCP. Uses browser
  cookies and TLS fingerprinting for full Reddit automation without API keys.
---

# Reddit MCP Skill

Full Reddit automation via MCP — browsing, posting, commenting, voting, and moderation.

<!-- Static skill -->
<!-- Install: npx skills add <owner/reddit-lyr> --skill reddit-mcp -->
<!-- CI check: diff <(reddit-lyr --help) SKILL.md && exit 1 -->

## Quick Start

```bash
# Run the MCP server
reddit-lyr

# Or with HTTP transport
reddit-lyr --transport streamable-http --port 8000
```

## MCP Configuration

```json
{
  "mcpServers": {
    "reddit": {
      "command": "reddit-lyr",
      "args": []
    }
  }
}
```

## Key Tools (45 total)

| Tool | Description |
|------|-------------|
| `reddit_browse_subreddit` | Browse a subreddit feed |
| `reddit_browse_frontpage` | Browse Reddit frontpage |
| `reddit_search_posts` | Search posts across Reddit |
| `reddit_search_subreddits` | Search for subreddits |
| `reddit_get_post_details` | Get post details + comments |
| `reddit_submit_text_post` | Create a text post |
| `reddit_submit_link_post` | Create a link post |
| `reddit_comment` | Comment on a post |
| `reddit_reply` | Reply to a comment |
| `reddit_upvote` | Upvote a post or comment |
| `reddit_downvote` | Downvote a post or comment |
| `reddit_send_dm` | Send a direct message |
| `reddit_get_inbox` | Get inbox messages |
| `reddit_subscribe` | Subscribe to a subreddit |
| `reddit_remove` | Remove a post or comment (mod) |
| `reddit_approve` | Approve a post or comment (mod) |

And more — run the MCP server to see all 45 tools.

## Authentication

```bash
# Import cookies from browser
reddit-lyr --login

# Check status
reddit-lyr --status
```

Or set `REDDIT_COOKIES` env var.