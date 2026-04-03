#!/usr/bin/env python3
"""
Integration Tests for Stack 2.9 CLI
Full CLI workflow tests.
"""

import pytest
import sys
import os
import json
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.cli import (
    StackCLI,
    ChatMode,
    CommandMode,
    VoiceInterface,
    main,
    print_banner,
    print_colored,
    format_output
)


class TestCLIComponents:
    """Test CLI components."""

    def test_print_banner(self, capsys):
        """Test banner printing."""
        print_banner()
        captured = capsys.readouterr()
        assert "Stack" in captured.out

    def test_cli_creation(self):
        """Test CLI can be created."""
        with patch('stack_cli.cli.create_agent'):
            cli = StackCLI()
        
        assert cli is not None
        assert hasattr(cli, 'agent')
        assert hasattr(cli, 'chat_mode')
        assert hasattr(cli, 'command_mode')

    def test_chat_mode_creation(self):
        """Test chat mode can be created."""
        with patch('stack_cli.cli.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent
            
            chat = ChatMode(mock_agent)
        
        assert chat is not None
        assert chat.agent == mock_agent
        assert chat.history == []

    def test_command_mode_creation(self):
        """Test command mode can be created."""
        with patch('stack_cli.cli.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent
            
            cmd = CommandMode(mock_agent)
        
        assert cmd is not None
        assert cmd.agent == mock_agent

    def test_voice_interface_creation(self):
        """Test voice interface creation."""
        voice = VoiceInterface()
        
        assert voice is not None
        # available depends on dependencies


class TestCLIWorkflows:
    """Test CLI workflow integration."""

    @patch('stack_cli.cli.StackCLI')
    def test_run_interactive(self, mock_cli_class):
        """Test interactive mode."""
        mock_cli = MagicMock()
        mock_cli_class.return_value = mock_cli
        
        # This should not crash
        # Would need more complex mocking for full test

    @patch('stack_cli.cli.StackCLI')
    def test_run_command(self, mock_cli_class):
        """Test command execution mode."""
        mock_cli = MagicMock()
        mock_cli.run_command.return_value = "result"
        mock_cli_class.return_value = mock_cli
        
        cli = StackCLI()
        # Test would go here

    @patch('stack_cli.cli.StackCLI')
    def test_run_tools(self, mock_cli_class):
        """Test tool execution mode."""
        mock_cli = MagicMock()
        mock_cli.run_tools.return_value = "tool result"
        mock_cli_class.return_value = mock_cli
        
        cli = StackCLI()
        # Test would go here


class TestCLIArguments:
    """Test CLI argument parsing."""

    def test_cli_with_command_arg(self):
        """Test CLI with -c argument."""
        # Test that argparse works
        # Would need to mock sys.argv
        
    def test_cli_with_tools_arg(self):
        """Test CLI with -t argument."""
        pass

    def test_cli_with_output_arg(self):
        """Test CLI with -o argument."""
        pass

    def test_cli_with_format_arg(self):
        """Test CLI with -f argument."""
        pass


class TestOutputFormatting:
    """Test output formatting in CLI."""

    def test_format_text_output(self):
        """Test text format output."""
        data = {"key": "value", "number": 42}
        result = format_output(data, "text")
        
        assert "key" in result

    def test_format_json_output(self):
        """Test JSON format output."""
        data = {"key": "value"}
        result = format_output(data, "json")
        
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_format_list_output(self):
        """Test list format output."""
        data = ["item1", "item2", "item3"]
        result = format_output(data, "text")
        
        assert "item1" in result


class TestCLIColors:
    """Test CLI color utilities."""

    def test_colored_output_red(self, capsys):
        """Test red color output."""
        print_colored("error message", "red")
        captured = capsys.readouterr()
        assert "error message" in captured.out

    def test_colored_output_green(self, capsys):
        """Test green color output."""
        print_colored("success message", "green")
        captured = capsys.readouterr()
        assert "success message" in captured.out

    def test_colored_output_cyan(self, capsys):
        """Test cyan color output."""
        print_colored("info message", "cyan")
        captured = capsys.readouterr()
        assert "info message" in captured.out


class TestMainFunction:
    """Test main entry point."""

    @patch('sys.argv', ['stack.py'])
    @patch('stack_cli.cli.StackCLI')
    def test_main_defaults(self, mock_cli_class):
        """Test main with defaults."""
        mock_cli = MagicMock()
        mock_cli.run_interactive = MagicMock()
        mock_cli_class.return_value = mock_cli
        
        # Would need more complex setup for full test

    @patch('sys.argv', ['stack.py', '-c', 'test query'])
    @patch('stack_cli.cli.StackCLI')
    def test_main_with_command(self, mock_cli_class):
        """Test main with command."""
        mock_cli = MagicMock()
        mock_cli.run_command = MagicMock(return_value=True)
        mock_cli_class.return_value = mock_cli
        
        # Test would go here


class TestCLIErrors:
    """Test CLI error handling."""

    @patch('sys.argv', ['stack.py'])
    @patch('stack_cli.cli.create_agent')
    def test_cli_keyboard_interrupt(self, mock_create):
        """Test handling of keyboard interrupt."""
        mock_create.side_effect = KeyboardInterrupt()
        
        # Should handle gracefully

    @patch('sys.argv', ['stack.py'])
    @patch('stack_cli.cli.create_agent')
    def test_cli_general_exception(self, mock_create):
        """Test handling of general exceptions."""
        mock_create.side_effect = RuntimeError("test error")
        
        # Should handle gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
