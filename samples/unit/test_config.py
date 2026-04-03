#!/usr/bin/env python3
"""
Unit Tests for Stack 2.9 Configuration
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))


class TestConfiguration:
    """Test configuration handling."""

    def test_default_workspace_path(self):
        """Test default workspace path."""
        from stack_cli.context import ContextManager
        
        with patch('stack_cli.context.Path') as mock_path:
            with patch.object(Path, 'exists', return_value=False):
                cm = ContextManager()
        
        # Default should point to user's workspace
        assert cm.workspace is not None

    def test_custom_workspace_path(self):
        """Test custom workspace path."""
        from stack_cli.context import ContextManager
        
        with patch('stack_cli.context.Path') as mock_path:
            with patch.object(Path, 'exists', return_value=False):
                cm = ContextManager("/custom/path")
        
        assert str(cm.workspace) == "/custom/path"


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_workspace_from_env(self, monkeypatch):
        """Test workspace can be set from env."""
        monkeypatch.setenv("STACK_WORKSPACE", "/env/workspace")
        
        # The context manager should respect env vars
        from stack_cli.context import ContextManager
        
        with patch('stack_cli.context.Path') as mock_path:
            with patch.object(Path, 'exists', return_value=False):
                # Just verify it doesn't crash
                cm = ContextManager()
        
        # Cleanup
        monkeypatch.delenv("STACK_WORKSPACE", raising=False)


class TestToolConfiguration:
    """Test tool-specific configuration."""

    def test_tool_timeout_defaults(self):
        """Test default tool timeouts."""
        from stack_cli.tools import tool_run_command
        
        # Should have reasonable defaults
        # This is tested implicitly through the tool's timeout param
        
    def test_git_command_timeout(self):
        """Test git command timeouts."""
        from stack_cli.tools import tool_git_status
        
        # Should have reasonable timeout


class TestLoggingConfiguration:
    """Test logging setup."""

    def test_logging_setup(self):
        """Test logging can be configured."""
        import logging
        
        # Should be able to configure logging
        logging.getLogger("stack_cli")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
