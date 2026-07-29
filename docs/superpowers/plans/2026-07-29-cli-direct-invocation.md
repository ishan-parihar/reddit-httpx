# CLI Direct Tool Invocation — Parity Gap Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable `reddit-httpx <tool_name> <args>` to call any of the 56 tools directly from the CLI without going through the MCP protocol.

**Architecture:** Intercept the first positional arg before argparse runs. If it matches a tool name, dispatch to a direct invocation path that parses `--key value` args, calls `tool.fn(**kwargs)` directly, and prints JSON output. No MCP protocol, no subprocess, no JSON-RPC — just a thin CLI-to-function bridge.

**Tech Stack:** Python 3.11+, argparse (existing), asyncio (existing tool functions are async), json (existing output format)

## Global Constraints

- Python 3.11+ (VPS constraint)
- AXI TOON output for CLI management surfaces (`--status`, `--list-tools`, etc.)
- JSON output for tool results (matches MCP behavior — agents parse JSON)
- All 56 tools must be callable, not just a subset
- `--full` flag must bypass truncation for tool results too
- Error output must use `axi_error()` TOON format (exit code 2)
- No new dependencies

---

## Discrepancy Analysis

| Capability | CLI (current) | MCP (current) | Gap |
|-----------|--------------|--------------|-----|
| List tools | `--list-tools` ✅ | `tools/list` ✅ | None |
| Tool metadata | `--tool-info` ✅ | `tools/list` ✅ | None |
| Auth check | `--status` ✅ | N/A | None |
| Auth management | `--login/--logout` ✅ | N/A | None |
| **Execute tool** | ❌ Not possible | `tools/call` ✅ | **THE GAP** |
| Read operations | ❌ | ✅ | **THE GAP** |
| Write operations | ❌ | ✅ | **THE GAP** |

**Root cause:** The CLI is a management interface only. Tools are registered via `@mcp.tool()` decorators inside FastMCP, accessible only through the MCP JSON-RPC protocol. There's no CLI dispatch path.

**What exists:** Each tool is an async function with a `fn` attribute on the FastMCP tool object. The function signature includes type annotations and default values that FastMCP extracts into the input schema.

**The fix:** A single dispatch function that:
1. Matches `sys.argv[1]` against tool names
2. Parses remaining args as `--key value` pairs
3. Calls `tool.fn(**kwargs)` directly
4. Prints the result as JSON

---

## File Map

| File | Change | Responsibility |
|------|--------|---------------|
| `cli_main.py:409-456` | Add `--toon` flag, early dispatch before argparse | CLI routing |
| `cli_main.py` (new function) | `run_tool_direct(tool_name, args, toon)` | Direct invocation engine |
| `cli_main.py:379-406` | Update `show_help()` with invocation examples | Help text |
| `tests/test_axi_cli_wrappers.py` | Add tests for direct invocation | Test coverage |

---

### Task 1: Add `--toon` flag and early tool dispatch in `main()`

**Files:**
- Modify: `reddit_mcp_server/cli_main.py:409-456` (main function)

**Interfaces:**
- Consumes: `_get_tools()` for tool name matching, tool `.fn` attribute for invocation
- Produces: `run_tool_direct()` function callable from `main()`

**Implementation:**

In `main()`, BEFORE argparse runs, check if `sys.argv[1]` matches a tool name:

```python
def main():
    # ── Direct tool invocation: reddit-httpx <tool_name> [args...] ──────
    # Intercept before argparse so tool names aren't parsed as flags.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        tool_name = sys.argv[1]
        # Check if it's a known tool (fast check — no server init yet)
        tool_names = [t[0] for t in _get_tools()]
        if tool_name in tool_names:
            toon = "--toon" in sys.argv
            remaining = [a for a in sys.argv[2:] if a != "--toon"]
            run_tool_direct(tool_name, remaining, toon)
            return

    parser = argparse.ArgumentParser(description="Reddit MCP Server", add_help=False)
    # ... existing parser setup ...
    parser.add_argument(
        "--toon",
        action="store_true",
        help="Render tool results in TOON format instead of JSON",
    )
    args, unknown = parser.parse_known_args()
    # ... rest of main ...
```

- [ ] **Step 1: Add the early dispatch block at the top of `main()`**

```python
def main():
    # ── Direct tool invocation: reddit-httpx <tool_name> [args...] ──────
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        tool_name = sys.argv[1]
        tool_names = [t[0] for t in _get_tools()]
        if tool_name in tool_names:
            toon = "--toon" in sys.argv
            remaining = [a for a in sys.argv[2:] if a != "--toon"]
            run_tool_direct(tool_name, remaining, toon)
            return

    parser = argparse.ArgumentParser(...)
```

- [ ] **Step 2: Add `--toon` flag to the argparse parser**

```python
    parser.add_argument(
        "--toon",
        action="store_true",
        help="Render tool results in TOON format instead of JSON",
    )
```

- [ ] **Step 3: Verify no regression in existing CLI flags**

Run: `reddit-httpx --help`, `reddit-httpx --status`, `reddit-httpx --list-tools`
Expected: All unchanged

- [ ] **Step 4: Commit**

```bash
git add reddit_mcp_server/cli_main.py
git commit -m "feat: add early dispatch for direct tool invocation in CLI"
```

---

### Task 2: Implement `run_tool_direct()` function

**Files:**
- Create: `reddit_mcp_server/cli_main.py` (add function before `main()`)

**Interfaces:**
- Consumes: `_get_tools()` for tool discovery, `create_mcp_server()` for tool objects with `.fn`
- Produces: JSON to stdout, TOON error via `axi_error()` on failure

**Implementation:**

```python
def run_tool_direct(tool_name: str, args: list[str], toon: bool = False) -> None:
    """Execute a tool directly from CLI without MCP protocol."""
    import asyncio
    from reddit_mcp_server.server import create_mcp_server
    from reddit_mcp_server.bootstrap import initialize_bootstrap

    # Parse --key value pairs into a dict
    kwargs = {}
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kwargs[key] = args[i + 1]
                i += 2
            else:
                kwargs[key] = "true"  # bare --flag = boolean true
                i += 1
        else:
            positional.append(arg)
            i += 1

    # Get tool object
    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    tool = next((t for t in tools if t.name == tool_name), None)
    if not tool:
        axi_error(f"Unknown tool: '{tool_name}'", f"Run `reddit-httpx --list-tools` to see available tools")

    # Map positional args to required params
    schema = tool.parameters or {}
    props = schema.get("properties", {})
    required = schema.get("required", [])
    required_params = [p for p in required if p in props]
    
    for idx, val in enumerate(positional):
        if idx < len(required_params):
            kwargs[required_params[idx]] = val
        else:
            axi_error(f"Unexpected positional arg: '{val}'", f"Tool `{tool_name}` expects: {', '.join(required_params)}")

    # Type coercion from schema
    for key, val in kwargs.items():
        if key in props:
            prop = props[key]
            prop_type = prop.get("type", "string")
            if prop_type == "integer":
                kwargs[key] = int(val)
            elif prop_type == "number":
                kwargs[key] = float(val)
            elif prop_type == "boolean":
                kwargs[key] = val.lower() in ("true", "1", "yes")
            # Literal types stay as strings (validated by the function itself)

    # Initialize bootstrap (loads cookies)
    initialize_bootstrap()

    # Call the tool
    try:
        result = asyncio.run(tool.fn(**kwargs))
    except SystemExit:
        raise  # axi_error() calls sys.exit
    except Exception as e:
        axi_error(f"Tool `{tool_name}` failed: {e}")

    # Output
    if toon:
        if isinstance(result, dict):
            print(_toon_object(result))
        else:
            print(result)
    else:
        print(json.dumps(result, indent=2))
```

- [ ] **Step 1: Add `run_tool_direct()` function in `cli_main.py`**

Place it after `show_help()` and before `main()`. Full implementation above.

- [ ] **Step 2: Test basic invocation**

```bash
reddit-httpx browse_subreddit --subreddit python --limit 2
```
Expected: JSON output with 2 posts from r/python

- [ ] **Step 3: Test positional arg shorthand**

```bash
reddit-httpx browse_subreddit python --limit 2
```
Expected: Same result (first positional maps to `subreddit`)

- [ ] **Step 4: Test --toon flag**

```bash
reddit-httpx browse_subreddit --subreddit python --limit 2 --toon
```
Expected: TOON-formatted output instead of JSON

- [ ] **Step 5: Test error handling**

```bash
reddit-httpx nonexistent_tool foo
reddit-httpx browse_subreddit
```
Expected: TOON error messages, exit code 2

- [ ] **Step 6: Commit**

```bash
git add reddit_mcp_server/cli_main.py
git commit -m "feat: implement run_tool_direct() for CLI tool invocation"
```

---

### Task 3: Test all tool categories end-to-end on VPS

**Files:**
- No file changes — verification only

**Interfaces:**
- Consumes: All 56 tools via CLI direct invocation
- Produces: Pass/fail report

**Test matrix:**

```bash
# Read operations
reddit-httpx get_post --post_id_or_url 1unctej --limit 2
reddit-httpx browse_subreddit --subreddit python --limit 3
reddit-httpx browse_frontpage --limit 2
reddit-httpx search_posts --query "python tutorial" --limit 2
reddit-httpx search_subreddits --query "python" --limit 2
reddit-httpx get_comments --post_id_or_url 1unctej --limit 2
reddit-httpx get_user_profile --username spez
reddit-httpx get_account_info
reddit-httpx get_my_profile
reddit-httpx get_my_subreddits --limit 3
reddit-httpx get_inbox --limit 2
reddit-httpx get_karma

# Write operations (non-destructive first)
reddit-httpx vote --thing_id t3_1unctej --direction up
reddit-httpx vote --thing_id t3_1unctej --direction none
reddit-httpx save --thing_id t3_1unctej
reddit-httpx unsave --thing_id t3_1unctej
reddit-httpx subscribe --subreddit python

# Error cases
reddit-httpx nonexistent_tool
reddit-httpx browse_subreddit
reddit-httpx get_post
```

- [ ] **Step 1: Deploy to VPS**

```bash
cd /home/nerd/reddit-httpx && git pull && pipx install -e . --force
```

- [ ] **Step 2: Run read operation tests**

All should return valid JSON.

- [ ] **Step 3: Run write operation tests**

All should return `{"ok": true, ...}` objects.

- [ ] **Step 4: Run error case tests**

All should return TOON error messages and exit 2.

- [ ] **Step 5: Verify --full flag works with direct invocation**

```bash
reddit-httpx get_post --post_id_or_url 1unctej --full
```

Expected: `selftext` field is not truncated.

- [ ] **Step 6: Verify help text is updated**

```bash
reddit-httpx --help
```

Expected: Shows direct invocation examples.

---

### Task 4: Update help text and documentation

**Files:**
- Modify: `reddit_mcp_server/cli_main.py:379-406` (show_help function)

**Interfaces:**
- Consumes: Tool list from `_get_tools()`
- Produces: Updated help output

**Implementation:**

Add direct invocation examples to `show_help()`:

```python
def show_help() -> None:
    print("reddit-httpx v0.1.0")
    print("Reddit MCP server — browsing, posting, commenting, voting, and moderation")
    print()
    print("Usage:")
    print("  reddit-httpx                    Show home view with live state")
    print("  reddit-httpx <tool> [args]      Call a tool directly (see examples)")
    print("  reddit-httpx --list-tools       List all available MCP tools")
    print("  reddit-httpx --tool-info <name> Show details for a specific tool")
    print("  reddit-httpx --login            Import cookies from browser")
    print("  reddit-httpx --cookies-file F   Import cookies from a JSON file")
    print("  reddit-httpx --logout           Clear stored session")
    print("  reddit-httpx --status           Check authentication status")
    print("  reddit-httpx --fields <fields>  Comma-separated extra fields for lists")
    print("  reddit-httpx --full            Show complete text fields (no truncation)")
    print("  reddit-httpx --toon            Render tool results in TOON format")
    print("  reddit-httpx --help             Show this help message")
    print()
    print("Examples:")
    print("  reddit-httpx browse_subreddit --subreddit python --limit 5")
    print("  reddit-httpx search_posts --query 'rust lang' --limit 3")
    print("  reddit-httpx get_post --post_id_or_url 1unctej")
    print("  reddit-httpx vote --thing_id t3_1unctej --direction up")
    print("  reddit-httpx --tool-info search_posts")
    print("  reddit-httpx --list-tools")
    print("  reddit-httpx --login")
```

- [ ] **Step 1: Update `show_help()` with new examples**

- [ ] **Step 2: Verify help output**

Run: `reddit-httpx --help`
Expected: Shows direct invocation examples

- [ ] **Step 3: Commit**

```bash
git add reddit_mcp_server/cli_main.py
git commit -m "docs: update --help with direct invocation examples"
```

---

## Verification Checklist

After all tasks, verify:

1. **Parity:** Every tool callable via `reddit-httpx <tool_name> <args>` ✅
2. **Output match:** CLI output matches MCP output (JSON) ✅
3. **TOON option:** `--toon` flag renders human-readable output ✅
4. **Error handling:** Unknown tool / missing args → TOON error, exit 2 ✅
5. **Type coercion:** `--limit 5` becomes int, `--direction up` stays string ✅
6. **Positional args:** `reddit-httpx browse_subreddit python` works ✅
7. **Existing CLI:** `--status`, `--list-tools`, `--help` unchanged ✅
8. **`--full` flag:** Bypasses truncation for tool results ✅
9. **VPS test:** All 56 tools work from CLI on the VPS ✅
10. **Tests pass:** `pytest tests/` green ✅
