name: Reddit MCP Server
description: Reddit automation with browsing, posting, commenting, voting, and moderation features
triggers:
  - "reddit post"
  - "reddit search"
  - "reddit comment"
  - "reddit automation"
  - "social media posting"
  - "content creation"
  - "subreddit"

## Overview
Reddit MCP Server provides comprehensive Reddit automation:
- Browse posts, comments, and subreddits
- Search posts, users, and subreddits
- Post and comment
- Vote and save content
- User profiles and karma
- Moderation tools

## Quick Start
```bash
# Show home view with live state
reddit-lyr

# Import browser cookies
reddit-lyr --login

# Check session status
reddit-lyr --status

# List available tools
reddit-lyr --list-tools

# Start MCP server
reddit-lyr
```

## MCP Tools
- `browse_subreddit` - Browse posts from a subreddit
- `browse_frontpage` - Browse the personalized frontpage
- `browse_popular` - Browse r/popular
- `search_posts` - Search Reddit posts
- `search_subreddits` - Search for subreddits
- `search_users` - Search for Reddit users
- `get_post` - Get a post's details and comment tree
- `get_comments` - Get comments for a post
- `get_user_profile` - Get a Reddit user's profile
- `get_user_posts` - Get a user's recent posts
- `get_user_comments` - Get a user's recent comments
- `get_my_profile` - Get the authenticated user's profile
- `vote` - Vote on a post or comment
- `save_post` - Save a post
- `submit_post` - Submit a new post
- `submit_comment` - Submit a new comment

## Session Integration
Install session hooks for ambient context:
```bash
reddit-lyr --install-hook
```

This shows Reddit session state on every agent session start.

## Output Formats
- `--toon` - TOON format (default, token-efficient)
- `--json` - JSON format
- `--full` - Show complete text fields (no truncation)
- `--fields <fields>` - Comma-separated extra fields for lists

## Examples
```bash
# Browse a subreddit
reddit-lyr browse_subreddit --subreddit python --limit 5

# Search posts
reddit-lyr search_posts --query "rust lang" --limit 3

# Get post details
reddit-lyr get_post --post_id_or_url 1unctej

# Vote on a post
reddit-lyr vote --thing_id t3_1unctej --direction up
```
