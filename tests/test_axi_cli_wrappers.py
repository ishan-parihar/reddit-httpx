"""Tests for AXI CLI wrappers: --list-tools and --tool-info (AXI §8/§9)."""

import json
import sys

import pytest

from reddit_mcp_server.cli_main import list_tools_and_exit, tool_info_and_exit, axi_error, TOOLS


class TestListTools:
    """Tests for the --list-tools flag (AXI §8 content-first)."""

    def test_list_tools_exits_with_code_zero(self, capsys):
        """list_tools_and_exit should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            list_tools_and_exit()
        assert exc_info.value.code == 0

    def test_list_tools_output_contains_tool_header(self, capsys):
        """Output should contain the TOON-style tools header with correct count."""
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        expected_count = len(TOOLS)
        assert f"tools[{expected_count}]" in out

    def test_list_tools_output_contains_all_discovered_tools(self, capsys):
        """All discovered tools should be listed."""
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        for tool_name, _ in TOOLS:
            assert tool_name in out, f"Tool '{tool_name}' not found in --list-tools output"

    def test_list_tools_output_contains_help_hints(self, capsys):
        """Output should contain AXI §9 help hints."""
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        assert "help[" in out
        assert "--tool-info" in out

    def test_list_tools_output_format_is_toon(self, capsys):
        """Output should use TOON-style formatting, not raw JSON."""
        with pytest.raises(SystemExit):
            list_tools_and_exit()
        out = capsys.readouterr().out
        assert not out.strip().startswith("{")


class TestToolInfo:
    """Tests for the --tool-info flag (AXI §9 contextual disclosure)."""

    def test_tool_info_exits_with_code_zero_for_known_tool(self, capsys):
        """tool_info_and_exit should exit with code 0 for a known tool."""
        with pytest.raises(SystemExit) as exc_info:
            tool_info_and_exit("browse_subreddit")
        assert exc_info.value.code == 0

    def test_tool_info_outputs_valid_json(self, capsys):
        """Output for a known tool should be valid JSON."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("browse_subreddit")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_tool_info_contains_required_fields(self, capsys):
        """Output should contain name and description."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("browse_subreddit")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "name" in data
        assert "description" in data

    def test_tool_info_search_has_query_param(self, capsys):
        """search_posts should have parameters with query."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("search_posts")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "parameters" in data

    def test_tool_info_get_post_has_parameters(self, capsys):
        """get_post should have parameters."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("get_post")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "parameters" in data

    def test_tool_info_unknown_tool_exits_with_code_2(self, capsys):
        """Unknown tool should exit with code 2 (AXI §6 structured error)."""
        with pytest.raises(SystemExit) as exc_info:
            tool_info_and_exit("nonexistent_tool")
        assert exc_info.value.code == 2

    def test_tool_info_unknown_tool_outputs_error_json(self, capsys):
        """Unknown tool should output structured error JSON."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("nonexistent_tool")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "error" in data
        assert "nonexistent_tool" in data["error"]

    def test_tool_info_unknown_tool_suggests_valid_tools(self, capsys):
        """Unknown tool error should suggest valid tool names."""
        with pytest.raises(SystemExit):
            tool_info_and_exit("nonexistent_tool")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "help" in data
        assert "Valid tools" in data["help"]


class TestAxiError:
    """Tests for the axi_error structured error function (AXI §6)."""

    def test_axi_error_exits_with_code_2(self):
        """axi_error should exit with code 2."""
        with pytest.raises(SystemExit) as exc_info:
            axi_error("test error")
        assert exc_info.value.code == 2

    def test_axi_error_outputs_error_json(self, capsys):
        """axi_error should output structured error JSON."""
        with pytest.raises(SystemExit):
            axi_error("something went wrong")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["error"] == "something went wrong"

    def test_axi_error_with_hint_includes_help(self, capsys):
        """axi_error with hint should include help field."""
        with pytest.raises(SystemExit):
            axi_error("missing input", "Run with --flag")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["help"] == "Run with --flag"
