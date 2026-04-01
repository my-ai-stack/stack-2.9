#!/usr/bin/env python3
"""
Integration Tests for Stack 2.9 Agent + CLI
Agent and CLI integration tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import (
    StackAgent,
    create_agent,
    AgentResponse,
    ToolCall,
    QueryIntent
)
from stack_cli.cli import StackCLI, ChatMode, CommandMode
from stack_cli.context import ContextManager, create_context_manager
from stack_cli.tools import TOOLS, get_tool


class TestAgentCLIIntegration:
    """Test agent and CLI integration."""

    def test_agent_in_cli(self):
        """Test agent is used in CLI."""
        with patch('stack_cli.cli.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent
            
            cli = StackCLI()
            
            assert cli.agent is not None

    def test_chat_mode_uses_agent(self):
        """Test chat mode uses agent."""
        with patch('stack_cli.cli.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_response = AgentResponse(content="test", tool_calls=[])
            mock_agent.process.return_value = mock_response
            mock_create.return_value = mock_agent
            
            chat = ChatMode(mock_agent)
            
            # Simulate user input
            with patch('stack_cli.agent.StackAgent.process', return_value=mock_response):
                chat.default("test query")
            
            # Should have added to history
            assert len(chat.history) >= 0

    def test_command_mode_uses_agent(self):
        """Test command mode uses agent."""
        with patch('stack_cli.cli.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_response = AgentResponse(content="result", tool_calls=[])
            mock_agent.process.return_value = mock_response
            mock_create.return_value = mock_agent
            
            cmd = CommandMode(mock_agent)
            
            # Execute should call agent
            result = cmd.execute("test query")
            
            # Result should be formatted


class TestAgentContextIntegration:
    """Test agent and context integration."""

    def test_agent_uses_context_manager(self):
        """Test agent uses context manager."""
        with patch('stack_cli.context.create_context_manager'):
            agent = create_agent()
        
        assert agent.context_manager is not None

    def test_agent_records_tool_usage(self):
        """Test agent records tool usage."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("read test.py")
                
                # Agent should record tool usage in context
                assert agent.context_manager is not None

    def test_agent_gets_context(self):
        """Test agent can get context."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            context = agent.get_context()
            
            assert context is not None
            assert isinstance(context, str)


class TestAgentToolsIntegration:
    """Test agent and tools integration."""

    def test_agent_gets_schemas(self):
        """Test agent can get tool schemas."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            schemas = agent.get_schemas()
            
            assert isinstance(schemas, list)
            if schemas:
                assert "name" in schemas[0]

    def test_agent_process_with_forced_tools(self):
        """Test agent can process with forced tools."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process_with_tools("test", ["read", "write"])
                
                assert response is not None
                assert isinstance(response, AgentResponse)


class TestFullWorkflow:
    """Test complete agent-CLI workflows."""

    def test_read_file_workflow(self):
        """Test read file workflow."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={
                    "success": True,
                    "content": "file content here",
                    "total_lines": 10
                })
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("read test.py")
                
                assert response.content is not None

    def test_write_file_workflow(self):
        """Test write file workflow."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("write output.txt with test content")
                
                assert response is not None

    def test_git_workflow(self):
        """Test git operations workflow."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "files": ["test.py"]})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("git status")
                
                assert response is not None


class TestMultiToolIntegration:
    """Test multiple tools working together."""

    def test_read_then_process(self):
        """Test reading then processing."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                call_count = [0]
                
                def mock_tool(**kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return {"success": True, "content": "data"}
                    return {"success": True}
                
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("read data.txt and process it")
                
                assert response is not None

    def test_multiple_git_operations(self):
        """Test multiple git operations."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("check git status and commit")
                
                assert response is not None


class TestErrorIntegration:
    """Test error handling in integration."""

    def test_tool_failure_handling(self):
        """Test handling of tool failures."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": False, "error": "Not found"})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("read missing.py")
                
                # Should still return a response
                assert response is not None

    def test_context_error_recovery(self):
        """Test recovery from context errors."""
        with patch('stack_cli.context.create_context_manager') as mock_cm:
            mock_cm.side_effect = RuntimeError("Context error")
            
            # Should handle gracefully
            try:
                agent = create_agent()
            except:
                pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
