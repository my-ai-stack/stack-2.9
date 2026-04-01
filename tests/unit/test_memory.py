#!/usr/bin/env python3
"""
Unit Tests for Stack 2.9 Memory & Context Module
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.context import (
    ProjectContext,
    SessionMemory,
    ContextManager,
    ProjectAware,
    create_context_manager
)


class TestProjectContext:
    """Test ProjectContext dataclass."""

    def test_project_context_creation(self):
        """Test creating a project context."""
        ctx = ProjectContext(
            name="test_project",
            path="/path/to/project",
            language="python",
            framework="fastapi"
        )
        
        assert ctx.name == "test_project"
        assert ctx.path == "/path/to/project"
        assert ctx.language == "python"
        assert ctx.framework == "fastapi"
        assert ctx.files == []
        assert ctx.dirs == []

    def test_project_context_defaults(self):
        """Test default values."""
        ctx = ProjectContext(name="test", path="/test")
        
        assert ctx.language is None
        assert ctx.framework is None
        assert ctx.has_git is False


class TestSessionMemory:
    """Test SessionMemory class."""

    def test_session_memory_creation(self):
        """Test creating session memory."""
        session = SessionMemory()
        
        assert session.messages == []
        assert session.tools_used == []
        assert session.files_touched == []
        assert session.commands_run == []

    def test_add_message(self):
        """Test adding a message."""
        session = SessionMemory()
        session.add_message("user", "Hello")
        
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"

    def test_add_tool_usage(self):
        """Test recording tool usage."""
        session = SessionMemory()
        session.add_tool_usage("read", {"success": True})
        
        assert len(session.tools_used) == 1
        assert session.tools_used[0]["tool"] == "read"

    def test_add_file_touched(self):
        """Test recording file access."""
        session = SessionMemory()
        session.add_file_touched("test.py", "read")
        
        assert len(session.files_touched) == 1
        assert session.files_touched[0]["path"] == "test.py"

    def test_add_command(self):
        """Test recording command execution."""
        session = SessionMemory()
        session.add_command("ls -la", {"success": True})
        
        assert len(session.commands_run) == 1
        assert session.commands_run[0]["command"] == "ls -la"

    def test_get_summary(self):
        """Test getting session summary."""
        session = SessionMemory()
        session.add_message("user", "Hello")
        session.add_tool_usage("read", {"success": True})
        
        summary = session.get_summary()
        
        assert summary["messages_count"] == 1
        assert summary["tools_used_count"] == 1
        assert "duration_minutes" in summary


class TestContextManager:
    """Test ContextManager class."""

    @patch('stack_cli.context.Path')
    def test_context_manager_creation(self, mock_path):
        """Test creating context manager."""
        with patch.object(Path, 'exists', return_value=False):
            cm = ContextManager("/tmp/test")
        
        assert cm is not None
        assert cm.workspace == Path("/tmp/test")

    @patch('stack_cli.context.Path')
    def test_load_context(self, mock_path):
        """Test loading context files."""
        with patch.object(Path, 'exists', return_value=False):
            cm = ContextManager("/tmp/test")
        
        assert hasattr(cm, 'context')
        assert hasattr(cm, 'projects')

    @patch('stack_cli.context.Path')
    def test_get_context_summary(self, mock_path):
        """Test getting context summary."""
        with patch.object(Path, 'exists', return_value=False):
            cm = ContextManager("/tmp/test")
        
        summary = cm.get_context_summary()
        
        assert "workspace" in summary
        assert "projects" in summary
        assert "session" in summary

    @patch('stack_cli.context.Path')
    def test_get_workspace_context(self, mock_path):
        """Test getting formatted workspace context."""
        with patch.object(Path, 'exists', return_value=False):
            cm = ContextManager("/tmp/test")
        
        context = cm.get_workspace_context()
        
        assert isinstance(context, str)
        assert "Workspace Context" in context

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_search_memory(self, mock_read, mock_exists):
        """Test searching memory."""
        # Setup mock
        mock_exists.return_value = True
        
        def mock_file_exists(self):
            if str(self).endswith('MEMORY.md'):
                return True
            return False
        
        with patch.object(Path, 'exists', mock_file_exists):
            mock_read.return_value = "### key\nvalue"
            
            cm = ContextManager("/tmp/test")
            results = cm.search_memory("key")
            
            assert isinstance(results, list)

    @patch('pathlib.Path.write_text')
    def test_save_to_memory(self, mock_write):
        """Test saving to memory."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('pathlib.Path.open', mock_open(read_data="")):
                cm = ContextManager("/tmp/test")
                cm.save_to_memory("test_key", "test_value")
        
        mock_write.assert_called()


class TestProjectAware:
    """Test ProjectAware mixin."""

    def test_project_aware_creation(self):
        """Test creating project aware."""
        pa = ProjectAware()
        
        assert pa is not None
        assert hasattr(pa, 'context_manager')

    def test_detect_project(self):
        """Test project detection."""
        pa = ProjectAware()
        
        # Should return None for non-existent path
        result = pa.detect_project("/nonexistent/path")
        
        assert result is None or isinstance(result, str)

    def test_get_project_context(self):
        """Test getting project context."""
        pa = ProjectAware()
        
        # Should return None for non-existent project
        result = pa.get_project_context("nonexistent_project")
        
        assert result is None or isinstance(result, ProjectContext)

    def test_format_context_for_prompt(self):
        """Test formatting context for prompt."""
        pa = ProjectAware()
        
        context = pa.format_context_for_prompt()
        
        assert isinstance(context, str)


class TestCreateContextManager:
    """Test create_context_manager factory."""

    @patch('stack_cli.context.ContextManager')
    def test_create_context_manager_default(self, mock_cm):
        """Test creating with defaults."""
        mock_cm.return_value = MagicMock()
        
        cm = create_context_manager()
        
        assert cm is not None

    @patch('stack_cli.context.ContextManager')
    def test_create_context_manager_custom(self, mock_cm):
        """Test creating with custom workspace."""
        mock_cm.return_value = MagicMock()
        
        cm = create_context_manager("/custom/path")
        
        assert cm is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
