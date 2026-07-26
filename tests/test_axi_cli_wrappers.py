"""Tests for AXI CLI wrappers: --list-tools, --tool-info, and axi_error (TOON output)."""

import json
import sys

import pytest

from reddit_mcp_server.cli_main import (
    list_tools_and_exit, tool_info_and_exit, axi_error, _get_tools,
    _toon_object, _toon_kv, _toon_quote,
)


# ── TOON output parsing helpers (for test assertions) ──────────────────────

def _parse_treon_kv(text: str) -> dict:
    """Parse flat TOON key: value lines into a dict. Only top-level scalars."""
    result = {}
    for line in text.strip().splitlines():
        if ":" in line and not line.startswith(" ") and not line.endswith(":"):
            key, _, val = line.partition(":")
            val = val.strip()
            # Unquote
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1].replace('\\"', '"').replace("\\n", "\n")
            elif val == "true":
                val = True
            elif val == "false":
                val = False
            else:
                try:
                    val = int(val)
                except ValueError:
                    pass
            result[key.strip()] = val
    return result


# ── TOON helper unit tests ─────────────────────────────────────────────────

class TestToonHelpers:
    """Unit tests for TOON formatting helpers."""

    def test_toon_kv_string(self):
        assert _toon_kv("name", "reddit-httpx") == "name: reddit-httpx"

    def test_toon_kv_bool(self):
        assert _toon_kv("ok", True) == "ok: true"
        assert _toon_kv("ok", False) == "ok: false"

    def test_toon_kv_int(self):
        assert _toon_kv("count", 42) == "count: 42"

    def test_toon_quote_simple(self):
        assert _toon_quote("hello world") == "hello world"

    def test_toon_quote_needs_quoting(self):
        # Contains colon
        assert _toon_quote("key: value").startswith('"')
        # Is a bool literal
        assert _toon_quote("true").startswith('"')
        # Is a number
        assert _toon_quote("42").startswith('"')

    def test_toon_object_flat(self):
        out = _toon_object({"status": "ok", "count": 5})
        assert "status: ok" in out
        assert "count: 5" in out

    def test_toon_object_nested(self):
        out = _toon_object({"auth": {"authenticated": True, "count": 9}})
        assert "auth:" in out
        assert "  authenticated: true" in out
        assert "  count: 9" in out

    def test_toon_object_tabular(self):
        out = _toon_object({"items": [{"name": "a"}, {"name": "b"}]})
        assert "items[2]{name}:" in out
        assert "  a" in out
        assert "  b" in out


# ── list-tools tests ───────────────────────────────────────────────────────

class TestListTools:
    """Tests for the --list-tools flag (AXI §8 content-first)."""

    def test_list_tools_exits_with_code_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            list_tools_and_exit()
        assert exc_info.value.code == 0

    def test_list_tools_output_contains_tool_header(self, capsys):
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        expected_count = len(_get_tools())
        assert f"tools[{expected_count}]" in out

    def test_list_tools_output_contains_all_discovered_tools(self, capsys):
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        for tool_name, _ in _get_tools():
            assert tool_name in out, f"Tool '{tool_name}' not found in --list-tools output"

    def test_list_tools_output_contains_help_hints(self, capsys):
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        assert "help[" in out
        assert "--tool-info" in out

    def test_list_tools_output_format_is_toon(self, capsys):
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        assert not out.strip().startswith("{")


# ── tool-info tests ────────────────────────────────────────────────────────

class TestToolInfo:
    """Tests for the --tool-info flag (AXI §9 contextual disclosure)."""

    def test_tool_info_exits_with_code_zero_for_known_tool(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            tool_info_and_exit("browse_subreddit")
        assert exc_info.value.code == 0

    def test_tool_info_outputs_treon_format(self, capsys):
        """Output should be TOON key: value, not JSON."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("browse_subreddit")
        out = capsys.readouterr().out
        # Should NOT be JSON
        assert not out.strip().startswith("{")
        # Should contain TOON key-value
        assert "name: browse_subreddit" in out

    def test_tool_info_contains_required_fields(self, capsys):
        """Output should contain name and description as TOON fields."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("browse_subreddit")
        out = capsys.readouterr().out
        assert "name: browse_subreddit" in out
        assert "description:" in out

    def test_tool_info_search_has_query_param(self, capsys):
        """search_posts should have params with query."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("search_posts")
        out = capsys.readouterr().out
        assert "params[" in out
        assert "query" in out

    def test_tool_info_get_post_has_parameters(self, capsys):
        """get_post should have params."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("get_post")
        out = capsys.readouterr().out
        assert "params[" in out

    def test_tool_info_unknown_tool_exits_with_code_2(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            tool_info_and_exit("nonexistent_tool")
        assert exc_info.value.code == 2

    def test_tool_info_unknown_tool_outputs_error_treon(self, capsys):
        """Unknown tool should output structured error in TOON."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("nonexistent_tool")
        out = capsys.readouterr().out
        assert "error:" in out
        assert "nonexistent_tool" in out

    def test_tool_info_unknown_tool_suggests_valid_tools(self, capsys):
        with pytest.raises(SystemExit):
            tool_info_and_exit("nonexistent_tool")
        out = capsys.readouterr().out
        assert "help:" in out
        assert "Valid tools" in out


# ── axi_error tests ────────────────────────────────────────────────────────

class TestAxiError:
    """Tests for the axi_error structured error function (AXI §6)."""

    def test_axi_error_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            axi_error("test error")
        assert exc_info.value.code == 2

    def test_axi_error_outputs_error_treon(self, capsys):
        """axi_error should output TOON error, not JSON."""
        with pytest.raises(SystemExit):
            axi_error("something went wrong")
        out = capsys.readouterr().out
        assert "error: something went wrong" in out
        assert not out.strip().startswith("{")

    def test_axi_error_with_hint_includes_help(self, capsys):
        with pytest.raises(SystemExit):
            axi_error("missing input", "Run with --flag")
        out = capsys.readouterr().out
        assert "help: Run with --flag" in out
