---
name: reddit-lyr
description: Reddit automation with browsing, posting, commenting, voting, and moderation features. Use this skill whenever the user requests Reddit operations, social media posting, content creation, or any Reddit-related tasks. Triggers on phrases like "reddit post", "reddit search", "reddit comment", "reddit automation", "social media posting", "content creation", "subreddit", "browse reddit", "search reddit", or any request for Reddit functionality.
---

# Reddit-lyr Skill

This skill enables AI agents to interact with Reddit using the reddit-lyr CLI tool. It provides comprehensive Reddit automation including browsing, posting, commenting, voting, and moderation features.

## Prerequisites

- reddit-lyr CLI must be installed globally on the system
- The CLI must be accessible in the system PATH
- Browser cookies may be required for authenticated operations

## Command Structure

### Available Commands

```bash
# Session management
reddit-lyr                          # Show home view with live state
reddit-lyr --login                  # Import browser cookies
reddit-lyr --status                 # Check session status
reddit-lyr --list-tools             # List available MCP tools

# Browsing commands
reddit-lyr browse_subreddit --subreddit python --limit 5
reddit-lyr browse_frontpage --limit 10
reddit-lyr browse_popular --limit 10

# Search commands
reddit-lyr search_posts --query "rust lang" --limit 3
reddit-lyr search_subreddits --query "programming"
reddit-lyr search_users --query "username"

# Content commands
reddit-lyr get_post --post_id_or_url 1unctej
reddit-lyr get_comments --post_id_or_url 1unctej
reddit-lyr get_user_profile --username spez
reddit-lyr get_user_posts --username spez --limit 5
reddit-lyr get_user_comments --username spez --limit 5
reddit-lyr get_my_profile

# Engagement commands
reddit-lyr vote --thing_id t3_1unctej --direction up
reddit-lyr save_post --post_id_or_url 1unctej

# Writing commands
reddit-lyr submit_post --subreddit test --title "Test" --text "Content"
reddit-lyr submit_comment --post_id_or_url 1unctej --text "Comment"
```

## MCP Tool Usage

The reddit-lyr CLI serves as an MCP server with the following tools:

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

The CLI supports multiple output formats:

```bash
# TOON format (default, token-efficient)
reddit-lyr browse_subreddit --subreddit python --toon

# JSON format
reddit-lyr browse_subreddit --subreddit python --json

# Show complete text fields (no truncation)
reddit-lyr browse_subreddit --subreddit python --full

# Comma-separated extra fields for lists
reddit-lyr browse_subreddit --subreddit python --fields author,score
```

## Workflow

### Step 1: Analyze User Request
- Determine the type of Reddit operation needed (browse, search, post, comment)
- Identify if authentication is required
- Select appropriate command based on user intent

### Step 2: Generate Command
- Use the command structure above to build the appropriate CLI command
- Add relevant flags for output format and limits
- Include any required parameters (subreddit names, post IDs, usernames, etc.)

### Step 3: Execute and Validate
- Run the command using shell execution
- Check for successful completion
- Parse the output in the appropriate format
- Report the result to the user

### Step 4: Handle Errors
- If authentication fails: guide user to run `reddit-lyr --login`
- If command not found: suggest installing reddit-lyr
- If rate limited: suggest waiting before retrying
- If invalid parameters: provide correct usage examples

## Error Handling

### Common Issues and Solutions

1. **Command not found**
   - Error: "reddit-lyr: command not found"
   - Solution: Install reddit-lyr globally or add to PATH

2. **Authentication errors**
   - Error: "Authentication required"
   - Solution: Run `reddit-lyr --login` to import browser cookies

3. **Rate limiting**
   - Error: "Rate limit exceeded"
   - Solution: Wait before retrying the operation

4. **Invalid parameters**
   - Error: "Invalid subreddit/post ID"
   - Solution: Verify the subreddit name or post ID is correct

## Integration Example

### User Request: "Browse the Python subreddit"

**Skill Processing:**
1. Identify as a browse operation
2. Generate command: `reddit-lyr browse_subreddit --subreddit python --limit 10`
3. Execute and parse results in TOON format
4. Report posts to user

### User Request: "Search for posts about Rust programming"

**Skill Processing:**
1. Identify as a search operation
2. Generate command: `reddit-lyr search_posts --query "rust programming" --limit 5`
3. Execute and format results
4. Report search results to user

### User Request: "Post a comment on a specific Reddit post"

**Skill Processing:**
1. Identify as a write operation requiring authentication
2. Generate command: `reddit-lyr submit_comment --post_id_or_url <post_id> --text "Comment"`
3. Execute and report results

## Best Practices

1. **Always check authentication requirements** before executing write operations
2. **Use appropriate output formats** for the task (TOON for data processing, human-readable for display)
3. **Handle rate limiting gracefully** by suggesting delays between operations
4. **Provide context in results** when returning post data (subreddit, author, score, etc.)
5. **Use reasonable limits** when browsing to avoid overwhelming results
6. **Handle errors with actionable suggestions** for resolution
7. **Verify subreddit names** before posting to ensure they exist and allow posting