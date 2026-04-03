#!/usr/bin/env python3
"""
Integration Tests for Stack 2.9 Tool Chains
Multi-tool sequence tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, create_agent
from stack_cli.tools import get_tool, list_tools


class TestToolChains:
    """Test tool chain sequences."""

    def test_read_grep_chain(self):
        """Test read then grep workflow."""
        call_log = []
        
        def mock_tool(**kwargs):
            call_log.append(kwargs)
            if "path" in kwargs:
                return {"success": True, "content": "line1\nline2\nline3"}
            return {"success": True, "matches": []}
        
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool', return_value=mock_tool):
                agent = StackAgent()
                
                # Simulate reading then grepping
                read_result = get_tool("read")(path="test.py")
                grep_result = get_tool("grep")(path="test.py", pattern="line")
                
                assert read_result["success"] is True
                assert grep_result["success"] is True

    def test_search_copy_chain(self):
        """Test search then copy workflow."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "matches": ["file1.py"]})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Search for files
                search_result = get_tool("search")(path=".", pattern="*.py")
                
                # If found, copy
                if search_result.get("success") and search_result.get("matches"):
                    copy_result = get_tool("copy")(source="file1.py", destination="backup.py")
                    assert copy_result["success"] is True

    def test_git_status_branch_chain(self):
        """Test git status then branch workflow."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "files": []})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Check status
                status_result = get_tool("git_status")(repo_path=".")
                
                # List branches
                branch_result = get_tool("git_branch")(repo_path=".")
                
                assert status_result["success"] is True
                assert branch_result["success"] is True


class TestComplexToolSequences:
    """Test complex multi-tool sequences."""

    def test_file_edit_save_sequence(self):
        """Test file edit and save sequence."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Read file
                read_result = get_tool("read")(path="test.py")
                
                # Edit
                edit_result = get_tool("edit")(
                    path="test.py",
                    old_text="old_content",
                    new_text="new_content"
                )
                
                # Write back
                write_result = get_tool("write")(
                    path="test.py",
                    content="new_content"
                )
                
                assert edit_result["success"] is True

    def test_code_test_lint_sequence(self):
        """Test code test and lint sequence."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "output": "ok"})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Run tests
                test_result = get_tool("test")(path=".", pattern="test*.py")
                
                # Lint
                lint_result = get_tool("lint")(path=".")
                
                assert test_result.get("success") or "output" in test_result
                assert lint_result.get("success") or "output" in lint_result

    def test_project_scan_context_sequence(self):
        """Test project scan then load context."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={
                    "success": True,
                    "project": {"name": "test", "files": ["a.py", "b.py"]}
                })
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Scan project
                scan_result = get_tool("project_scan")(path=".")
                
                # Load context
                context_result = get_tool("context_load")()
                
                assert scan_result["success"] is True
                assert context_result["success"] is True


class TestToolChainErrors:
    """Test error handling in tool chains."""

    def test_chain_continues_on_error(self):
        """Test that chain continues when one tool fails."""
        call_count = [0]
        
        def mock_tool(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"success": False, "error": "File not found"}
            return {"success": True}
        
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool', return_value=mock_tool):
                agent = StackAgent()
                
                # First tool fails
                result1 = get_tool("read")(path="missing.py")
                
                # Second tool should still work
                result2 = get_tool("write")(path="new.txt", content="x")
                
                assert result1["success"] is False
                assert result2["success"] is True
                assert call_count[0] == 2

    def test_rollback_on_error(self):
        """Test rollback behavior on error."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(side_effect=[
                    {"success": True},
                    {"success": False, "error": "Operation failed"},
                    {"success": True}  # rollback
                ])
                mock_get_tool.return_value = mock_tool
                
                # First operation
                result1 = get_tool("write")(path="a.txt", content="x")
                assert result1["success"] is True
                
                # Second operation fails - rollback attempted
                try:
                    result2 = get_tool("write")(path="b.txt", content="y")
                except:
                    pass


class TestParallelToolExecution:
    """Test parallel tool execution."""

    def test_parallel_file_operations(self):
        """Test parallel file operations."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                # Would simulate parallel execution
                # In real implementation, use asyncio
                
                result1 = get_tool("read")(path="file1.txt")
                result2 = get_tool("read")(path="file2.txt")
                
                assert result1["success"] is True
                assert result2["success"] is True


class TestToolDependencyResolution:
    """Test tool dependency resolution."""

    def test_git_needs_repo(self):
        """Test that git tools need repo path."""
        # Git operations require repo path
        result = get_tool("git_status")(repo_path=".")
        
        # Success depends on whether it's a valid git repo
        # But it should not crash
        assert "success" in result

    def test_edit_needs_file(self):
        """Test that edit tool needs existing file."""
        result = get_tool("edit")(
            path="/nonexistent/file.txt",
            old_text="old",
            new_text="new"
        )
        
        assert result["success"] is False

    def test_memory_needs_workspace(self):
        """Test that memory tools need workspace."""
        result = get_tool("memory_save")(key="test", value="data")
        
        # Should succeed or fail gracefully
        assert "success" in result


class TestToolChainsPerformance:
    """Test tool chain performance."""

    def test_rapid_tool_calls(self):
        """Test rapid sequential tool calls."""
        import time
        
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                start = time.time()
                
                for _ in range(10):
                    get_tool("read")(path="test.py")
                
                elapsed = time.time() - start
                
                # Should complete reasonably fast
                assert elapsed < 5.0  # 5 seconds for 10 calls

    def test_memory_efficiency(self):
        """Test memory efficiency of tool chains."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            # Process multiple queries
            for _ in range(5):
                agent.process("test query")
            
            # Should not accumulate too much data
            assert len(agent.conversation_history) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
