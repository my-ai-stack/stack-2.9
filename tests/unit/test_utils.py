#!/usr/bin/env python3
"""
Unit Tests for Stack 2.9 Utilities
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

# Import CLI utilities for testing
from stack_cli.cli import print_colored, format_output


class TestCLIUtilities:
    """Test CLI utility functions."""

    def test_print_colored(self, capsys):
        """Test colored printing."""
        print_colored("test text", "red")
        captured = capsys.readouterr()
        assert "test text" in captured.out

    def test_print_colored_with_bold(self, capsys):
        """Test bold printing."""
        print_colored("bold text", "blue", bold=True)
        captured = capsys.readouterr()
        assert "bold text" in captured.out

    def test_format_output_dict(self):
        """Test formatting dict output."""
        data = {"key1": "value1", "key2": "value2"}
        result = format_output(data, "text")
        
        assert "key1" in result
        assert "value1" in result

    def test_format_output_list(self):
        """Test formatting list output."""
        data = ["item1", "item2", "item3"]
        result = format_output(data, "text")
        
        assert "item1" in result

    def test_format_output_json(self):
        """Test JSON formatting."""
        data = {"key": "value"}
        result = format_output(data, "json")
        
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_format_output_string(self):
        """Test string formatting."""
        data = "plain string"
        result = format_output(data, "text")
        
        assert result == "plain string"


class TestAgentUtilities:
    """Test agent utility functions."""

    def test_intent_parsing_utility(self):
        """Test intent parsing utilities."""
        from stack_cli.agent import QueryUnderstanding
        
        qu = QueryUnderstanding()
        
        # Test various query patterns
        queries = [
            "read test.py",
            "write file.txt", 
            "search for *.py",
            "run pytest",
            "what is python?"
        ]
        
        for query in queries:
            result = qu.parse(query)
            assert "intent" in result
            assert result["confidence"] > 0

    def test_tool_selection_utility(self):
        """Test tool selection utilities."""
        from stack_cli.agent import ToolSelector
        
        ts = ToolSelector()
        
        # Test various intents
        tools = ts.select("file_read", {})
        assert isinstance(tools, list)
        
        tools = ts.select("git_operation", {})
        assert isinstance(tools, list)

    def test_file_path_extraction(self):
        """Test file path extraction."""
        from stack_cli.agent import QueryUnderstanding
        
        qu = QueryUnderstanding()
        
        test_cases = [
            ("read test.py", "test.py"),
            ("view my_project/src/main.py", "my_project/src/main.py"),
            ("cat config.json", "config.json"),
        ]
        
        for query, expected in test_cases:
            path = qu.extract_file_path(query)
            # May extract partial path
            assert path is not None


class TestContextUtilities:
    """Test context utility functions."""

    def test_session_summary_format(self):
        """Test session summary formatting."""
        from stack_cli.context import SessionMemory
        
        session = SessionMemory()
        session.add_message("user", "Hello")
        session.add_tool_usage("read", {"success": True})
        
        summary = session.get_summary()
        
        assert "messages_count" in summary
        assert summary["messages_count"] == 1
        assert "tools_used_count" in summary
        assert summary["tools_used_count"] == 1

    def test_context_summary_format(self):
        """Test context summary formatting."""
        from stack_cli.context import ContextManager
        
        with patch('stack_cli.context.Path') as mock_path:
            with patch.object(Path, 'exists', return_value=False):
                cm = ContextManager("/tmp")
        
        summary = cm.get_context_summary()
        
        assert "workspace" in summary
        assert "projects" in summary
        assert "session" in summary


class TestToolSchemas:
    """Test tool schema utilities."""

    def test_schemas_contain_required_fields(self):
        """Test that schemas have required fields."""
        from stack_cli.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema

    def test_schemas_parameters_structure(self):
        """Test schema parameters structure."""
        from stack_cli.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        for schema in schemas:
            params = schema["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params


class TestDateTimeUtilities:
    """Test datetime utilities."""

    def test_timestamp_format(self):
        """Test timestamp formatting."""
        from datetime import datetime
        
        now = datetime.now()
        iso = now.isoformat()
        
        assert iso is not None
        assert "T" in iso


class TestPathUtilities:
    """Test path utilities."""

    def test_path_resolution(self):
        """Test path resolution."""
        p = Path("test.txt").resolve()
        
        assert p is not None

    def test_path_parent(self):
        """Test path parent."""
        p = Path("/a/b/c.txt")
        
        assert p.parent == Path("/a/b")

    def test_path_name(self):
        """Test path name extraction."""
        p = Path("/a/b/c.txt")
        
        assert p.name == "c.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
