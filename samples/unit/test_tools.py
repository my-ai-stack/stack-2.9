#!/usr/bin/env python3
"""
Unit Tests for Stack 2.9 Tools Module
Tests all 37+ tools: file operations, git, code execution, web, memory, and task planning.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from tools import (
    TOOLS,
    get_tool,
    list_tools,
    get_tool_schemas,
    tool_read_file,
    tool_write_file,
    tool_edit_file,
    tool_search_files,
    tool_grep,
    tool_copy_file,
    tool_move_file,
    tool_delete_file,
    tool_git_status,
    tool_git_commit,
    tool_git_push,
    tool_git_pull,
    tool_git_branch,
    tool_git_log,
    tool_git_diff,
    tool_run_command,
    tool_run_tests,
    tool_lint_code,
    tool_format_code,
    tool_check_type,
    tool_start_server,
    tool_install_dependencies,
    tool_web_search,
    tool_web_fetch,
    tool_download_file,
    tool_check_url,
    tool_screenshot,
    tool_memory_recall,
    tool_memory_save,
    tool_memory_list,
    tool_context_load,
    tool_project_scan,
    tool_create_task,
    tool_list_tasks,
    tool_update_task,
    tool_delete_task,
    tool_create_plan,
    tool_execute_plan,
)


class TestToolsRegistry:
    """Test tools registry."""

    def test_tools_count(self):
        """Verify we have 37+ tools."""
        tools = list_tools()
        assert len(tools) >= 37, f"Expected 37+ tools, got {len(tools)}"

    def test_get_tool_valid(self):
        """Test getting a valid tool."""
        tool = get_tool("read")
        assert tool is not None
        assert callable(tool)

    def test_get_tool_invalid(self):
        """Test getting an invalid tool."""
        tool = get_tool("nonexistent_tool")
        assert tool is None

    def test_get_tool_schemas(self):
        """Test getting tool schemas."""
        schemas = get_tool_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0


class TestFileOperations:
    """Test file operation tools."""

    def test_read_file_success(self, temp_file):
        """Test reading a file."""
        result = tool_read_file(str(temp_file))
        
        assert result["success"] is True
        assert "content" in result
        assert "Line 1" in result["content"]

    def test_read_file_not_found(self):
        """Test reading nonexistent file."""
        result = tool_read_file("/nonexistent/file.txt")
        
        assert result["success"] is False
        assert "error" in result

    def test_read_file_with_limit(self, temp_file):
        """Test reading file with limit."""
        result = tool_read_file(str(temp_file), limit=2)
        
        assert result["success"] is True
        lines = result["content"].split('\n')
        assert len(lines) <= 3

    def test_write_file_success(self, temp_workspace):
        """Test writing a file."""
        path = temp_workspace / "written.txt"
        result = tool_write_file(str(path), "Hello World")
        
        assert result["success"] is True
        assert path.exists()
        assert path.read_text() == "Hello World"

    def test_write_file_creates_dirs(self, temp_workspace):
        """Test writing creates parent directories."""
        path = temp_workspace / "subdir" / "nested" / "file.txt"
        result = tool_write_file(str(path), "content")
        
        assert result["success"] is True
        assert path.exists()

    def test_edit_file_success(self, temp_file):
        """Test editing a file."""
        result = tool_edit_file(str(temp_file), "Line 1", "Line ONE")
        
        assert result["success"] is True
        content = temp_file.read_text()
        assert "Line ONE" in content

    def test_edit_file_not_found(self):
        """Test editing nonexistent file."""
        result = tool_edit_file("/nonexistent/file.txt", "old", "new")
        
        assert result["success"] is False

    def test_edit_file_text_not_found(self, temp_file):
        """Test editing with non-existent text."""
        result = tool_edit_file(str(temp_file), "NonExistentText", "new")
        
        assert result["success"] is False

    def test_search_files(self, temp_project):
        """Test searching for files."""
        result = tool_search_files(str(temp_project), "*.py")
        
        assert result["success"] is True
        assert "matches" in result

    def test_grep_basic(self, temp_file):
        """Test grep functionality."""
        result = tool_grep(str(temp_file), "Line 1")
        
        assert result["success"] is True
        assert "matches" in result
        assert result["count"] > 0

    def test_grep_with_context(self, temp_file):
        """Test grep with context."""
        result = tool_grep(str(temp_file), "Line", context=1)
        
        assert result["success"] is True
        if result["matches"]:
            assert "context" in result["matches"][0]

    def test_copy_file(self, temp_file, temp_workspace):
        """Test copying a file."""
        dest = temp_workspace / "copied.txt"
        result = tool_copy_file(str(temp_file), str(dest))
        
        assert result["success"] is True
        assert dest.exists()

    def test_move_file(self, temp_file, temp_workspace):
        """Test moving a file."""
        dest = temp_workspace / "moved.txt"
        result = tool_move_file(str(temp_file), str(dest))
        
        assert result["success"] is True
        assert dest.exists()

    def test_delete_file_without_force(self, temp_file):
        """Test delete without force."""
        result = tool_delete_file(str(temp_file))
        
        assert result["success"] is True
        assert "would_delete" in result

    def test_delete_file_with_force(self, temp_file):
        """Test delete with force."""
        result = tool_delete_file(str(temp_file), force=True)
        
        assert result["success"] is True
        assert not temp_file.exists()


class TestGitOperations:
    """Test git operation tools."""

    def test_git_status_no_repo(self):
        """Test git status on non-repo."""
        result = tool_git_status("/nonexistent")
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_git_status_success(self, mock_run, temp_git_repo):
        """Test git status success."""
        mock_result = MagicMock()
        mock_result.stdout = " M modified.py\nA added.py\n"
        mock_run.return_value = mock_result
        
        result = tool_git_status(str(temp_git_repo))
        
        assert result["success"] is True

    @patch('subprocess.run')
    def test_git_commit(self, mock_run, temp_git_repo):
        """Test git commit."""
        mock_result = MagicMock()
        mock_result.stdout = "[main abc123] Test commit"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = tool_git_commit(str(temp_git_repo), "Test commit")
        
        assert result["success"] is True

    @patch('subprocess.run')
    def test_git_push(self, mock_run):
        """Test git push."""
        mock_result = MagicMock()
        mock_result.stdout = "To github.com:test/test.git\n   abc123..def456  main -> main\n"
        mock_run.return_value = mock_result
        
        result = tool_git_push(str(temp_git_repo))
        
        assert result["success"] is True

    @patch('subprocess.run')
    def test_git_pull(self, mock_run):
        """Test git pull."""
        mock_result = MagicMock()
        mock_result.stdout = "Updating abc123..def456\n"
        mock_run.return_value = mock_result
        
        result = tool_git_pull(str(temp_git_repo))
        
        assert result["success"] is True

    @patch('subprocess.run')
    def test_git_branch_list(self, mock_run):
        """Test listing branches."""
        mock_result = MagicMock()
        mock_result.stdout = "* main\n  develop\n  feature/test\n"
        mock_run.return_value = mock_result
        
        result = tool_git_branch(str(temp_git_repo))
        
        assert result["success"] is True
        assert "branches" in result

    @patch('subprocess.run')
    def test_git_log(self, mock_run):
        """Test git log."""
        mock_result = MagicMock()
        mock_result.stdout = "abc123 Commit message 1\ndef456 Commit message 2\n"
        mock_run.return_value = mock_result
        
        result = tool_git_log(str(temp_git_repo))
        
        assert result["success"] is True

    @patch('subprocess.run')
    def test_git_diff(self, mock_run):
        """Test git diff."""
        mock_result = MagicMock()
        mock_result.stdout = "diff --git a/test.py b/test.py\n+new line\n"
        mock_run.return_value = mock_result
        
        result = tool_git_diff(str(temp_git_repo))
        
        assert result["success"] is True


class TestCodeExecution:
    """Test code execution tools."""

    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test running a command successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = tool_run_command("echo hello")
        
        assert result["success"] is True
        assert result["stdout"] == "output"

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test running a failing command."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result
        
        result = tool_run_command("false")
        
        assert result["success"] is False

    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 1)
        
        result = tool_run_command("sleep 100", timeout=1)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @patch('subprocess.run')
    def test_run_tests(self, mock_run):
        """Test running tests."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = tool_run_tests(".")
        
        assert "success" in result

    @patch('subprocess.run')
    def test_lint_code(self, mock_run):
        """Test linting code."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "lint output"
        mock_run.return_value = mock_result
        
        result = tool_lint_code(".")
        
        assert "success" in result

    @patch('subprocess.run')
    def test_format_code(self, mock_run):
        """Test formatting code."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = tool_format_code(".")
        
        assert "success" in result

    @patch('subprocess.run')
    def test_check_type(self, mock_run):
        """Test type checking."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = tool_check_type(".")
        
        assert "success" in result

    @patch('subprocess.Popen')
    def test_start_server_background(self, mock_popen):
        """Test starting server in background."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc
        
        result = tool_start_server("python server.py", 8000, background=True)
        
        assert result["success"] is True
        assert "pid" in result


class TestWebTools:
    """Test web tools."""

    @patch('subprocess.run')
    def test_web_search(self, mock_run):
        """Test web search."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"title": "Result", "url": "http://example.com"}]'
        mock_run.return_value = mock_result
        
        result = tool_web_search("python")
        
        assert result["success"] is True
        assert "results" in result

    @patch('subprocess.run')
    def test_web_fetch(self, mock_run):
        """Test web fetch."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<html>test</html>"
        mock_run.return_value = mock_result
        
        result = tool_web_fetch("http://example.com")
        
        assert result["success"] is True
        assert "content" in result

    @patch('subprocess.run')
    def test_check_url(self, mock_run):
        """Test URL check."""
        mock_result = MagicMock()
        mock_result.stdout = "200"
        mock_run.return_value = mock_result
        
        result = tool_check_url("http://example.com")
        
        assert result["success"] is True


class TestMemoryTools:
    """Test memory tools."""

    @patch('pathlib.Path.read_text')
    def test_memory_recall(self, mock_read):
        """Test memory recall."""
        mock_read.return_value = "### test\ntest content"
        
        result = tool_memory_recall("test")
        
        assert result["success"] is True

    @patch('pathlib.Path.write_text')
    def test_memory_save(self, mock_write):
        """Test memory save."""
        with patch('pathlib.Path.exists', return_value=True):
            result = tool_memory_save("test_key", "test_value")
        
        assert result["success"] is True

    @patch('pathlib.Path.exists')
    def test_memory_list(self, mock_exists):
        """Test memory list."""
        mock_exists.return_value = False
        
        result = tool_memory_list()
        
        assert result["success"] is True

    @patch('pathlib.Path.read_text')
    def test_context_load(self, mock_read):
        """Test context load."""
        mock_read.return_value = "# Context"
        
        result = tool_context_load()
        
        assert result["success"] is True

    def test_project_scan(self, temp_project):
        """Test project scan."""
        result = tool_project_scan(str(temp_project))
        
        assert result["success"] is True
        assert "project" in result


class TestTaskPlanningTools:
    """Test task planning tools."""

    @patch('pathlib.Path.write_text')
    def test_create_task(self, mock_write):
        """Test creating a task."""
        with patch('pathlib.Path.exists', return_value=False):
            result = tool_create_task("Test task", "Description", "high")
        
        assert result["success"] is True
        assert "task" in result

    @patch('pathlib.Path.read_text')
    def test_list_tasks(self, mock_read):
        """Test listing tasks."""
        mock_read.return_value = "[]"
        
        result = tool_list_tasks()
        
        assert result["success"] is True

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_update_task(self, mock_write, mock_read):
        """Test updating a task."""
        mock_read.return_value = '[{"id": "test123", "title": "Test"}]'
        
        result = tool_update_task("test123", status="completed")
        
        assert result["success"] is True

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_delete_task(self, mock_write, mock_read):
        """Test deleting a task."""
        mock_read.return_value = '[{"id": "test123", "title": "Test"}]'
        
        result = tool_delete_task("test123")
        
        assert result["success"] is True

    @patch('pathlib.Path.write_text')
    def test_create_plan(self, mock_write):
        """Test creating a plan."""
        with patch('pathlib.Path.exists', return_value=False):
            result = tool_create_plan("Goal", ["step1", "step2"])
        
        assert result["success"] is True

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_execute_plan(self, mock_write, mock_read):
        """Test executing a plan."""
        mock_read.return_value = '[{"id": "plan1", "goal": "Goal", "steps": ["step1"]}]'
        
        result = tool_execute_plan("plan1")
        
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
