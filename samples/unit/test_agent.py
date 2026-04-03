#!/usr/bin/env python3
"""
Unit Tests for Stack 2.9 Agent Module
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import (
    QueryIntent,
    ToolCall,
    AgentResponse,
    QueryUnderstanding,
    ToolSelector,
    ResponseGenerator,
    SelfReflection,
    StackAgent,
    create_agent
)


class TestQueryIntent:
    """Test QueryIntent enum."""

    def test_intent_values(self):
        """Verify all intent values."""
        assert QueryIntent.FILE_READ.value == "file_read"
        assert QueryIntent.FILE_WRITE.value == "file_write"
        assert QueryIntent.FILE_EDIT.value == "file_edit"
        assert QueryIntent.FILE_SEARCH.value == "file_search"
        assert QueryIntent.GIT_OPERATION.value == "git_operation"
        assert QueryIntent.CODE_EXECUTION.value == "code_execution"
        assert QueryIntent.WEB_SEARCH.value == "web_search"
        assert QueryIntent.MEMORY.value == "memory"
        assert QueryIntent.TASK.value == "task"
        assert QueryIntent.QUESTION.value == "question"
        assert QueryIntent.GENERAL.value == "general"


class TestToolCall:
    """Test ToolCall dataclass."""

    def test_tool_call_creation(self):
        """Create a basic tool call."""
        call = ToolCall(
            tool_name="read",
            arguments={"path": "test.py"},
            result={"success": True},
            success=True
        )
        
        assert call.tool_name == "read"
        assert call.arguments == {"path": "test.py"}
        assert call.success is True
        assert call.error is None

    def test_tool_call_with_error(self):
        """Create a tool call with error."""
        call = ToolCall(
            tool_name="read",
            arguments={"path": "missing.py"},
            error="File not found",
            success=False
        )
        
        assert call.success is False
        assert call.error == "File not found"


class TestAgentResponse:
    """Test AgentResponse dataclass."""

    def test_agent_response_creation(self):
        """Create a basic agent response."""
        response = AgentResponse(
            content="Test response",
            tool_calls=[],
            confidence=0.9
        )
        
        assert response.content == "Test response"
        assert len(response.tool_calls) == 0
        assert response.confidence == 0.9
        assert response.needs_clarification is False


class TestQueryUnderstanding:
    """Test QueryUnderstanding class."""

    def setup_method(self):
        """Set up test instance."""
        self.qu = QueryUnderstanding()

    def test_parse_file_read(self):
        """Test parsing file read queries."""
        result = self.qu.parse("read README.md")
        
        assert result["intent"] == "file_read"
        assert result["confidence"] > 0

    def test_parse_file_write(self):
        """Test parsing file write queries."""
        result = self.qu.parse("write test.py with content")
        
        assert result["intent"] == "file_write"
        assert result["confidence"] > 0

    def test_parse_git_operation(self):
        """Test parsing git operations."""
        result = self.qu.parse("git status")
        
        assert result["intent"] == "git_operation"
        assert result["confidence"] > 0

    def test_parse_web_search(self):
        """Test parsing web search queries."""
        result = self.qu.parse("search the web for python")
        
        assert result["intent"] == "web_search"
        assert result["confidence"] > 0

    def test_parse_general(self):
        """Test parsing general queries."""
        result = self.qu.parse("hello world")
        
        assert result["intent"] == "general"
        assert result["confidence"] == 0.5

    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        result1 = self.qu.parse("READ README.md")
        result2 = self.qu.parse("read readme.md")
        
        assert result1["intent"] == result2["intent"] == "file_read"

    def test_extract_file_path(self):
        """Test file path extraction."""
        path = self.qu.extract_file_path("read test.py")
        assert path == "test.py"
        
        path = self.qu.extract_file_path("read my_project/src/main.py")
        assert path == "my_project/src/main.py"


class TestToolSelector:
    """Test ToolSelector class."""

    def setup_method(self):
        """Set up test instance."""
        self.ts = ToolSelector()

    def test_select_file_read_tools(self):
        """Test tool selection for file read."""
        tools = self.ts.select("file_read", {})
        
        assert "read" in tools

    def test_select_git_tools(self):
        """Test tool selection for git."""
        tools = self.ts.select("git_operation", {})
        
        assert "git_status" in tools

    def test_select_web_search_tools(self):
        """Test tool selection for web search."""
        tools = self.ts.select("web_search", {})
        
        assert "web_search" in tools

    def test_select_general_tools(self):
        """Test tool selection for general intent."""
        tools = self.ts.select("general", {})
        
        # Should include general tools
        assert "run" in tools
        assert "context_load" in tools

    def test_get_tool_parameters_read(self):
        """Test parameter extraction for read tool."""
        params = self.ts.get_tool_parameters("read", "read test.py", {})
        
        assert "path" in params

    def test_get_tool_parameters_git_commit(self):
        """Test parameter extraction for git commit."""
        params = self.ts.get_tool_parameters("git_commit", 'commit "fix bug"', {})
        
        assert "message" in params


class TestResponseGenerator:
    """Test ResponseGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        with patch('stack_cli.agent.create_context_manager'):
            self.rg = ResponseGenerator()

    def test_generate_empty(self):
        """Test generating response for empty tool calls."""
        result = self.rg.generate([], "general", {})
        
        assert "couldn't find" in result.lower() or "no results" in result.lower()

    def test_generate_with_success(self):
        """Test generating response for successful tool calls."""
        tool_calls = [
            ToolCall(
                tool_name="read",
                arguments={"path": "test.py"},
                result={"success": True, "content": "test content"},
                success=True
            )
        ]
        
        result = self.rg.generate(tool_calls, "file_read", {})
        
        assert "read" in result.lower()
        assert "test content" in result

    def test_generate_with_error(self):
        """Test generating response for failed tool calls."""
        tool_calls = [
            ToolCall(
                tool_name="read",
                arguments={"path": "missing.py"},
                result={"success": False, "error": "File not found"},
                success=False
            )
        ]
        
        result = self.rg.generate(tool_calls, "file_read", {})
        
        assert "error" in result.lower() or "not found" in result.lower()

    def test_generate_clarification(self):
        """Test clarification generation."""
        question = "Which file do you want to read?"
        result = self.rg.generate_clarification(question)
        
        assert "clarification" in result.lower()
        assert question in result


class TestSelfReflection:
    """Test SelfReflection class."""

    def setup_method(self):
        """Set up test instance."""
        self.sr = SelfReflection()

    def test_reflect_high_confidence(self):
        """Test reflection with high confidence."""
        tool_calls = [
            ToolCall(tool_name="read", arguments={}, result={"success": True}, success=True),
            ToolCall(tool_name="write", arguments={}, result={"success": True}, success=True)
        ]
        
        result = self.sr.reflect("test query", tool_calls, "Good response content here")
        
        assert result["needs_reflection"] is False
        assert result["confidence"] >= 0.7

    def test_reflect_low_confidence(self):
        """Test reflection with failed tool calls."""
        tool_calls = [
            ToolCall(tool_name="read", arguments={}, error="Failed", success=False)
        ]
        
        result = self.sr.reflect("test query", tool_calls, "Short")
        
        assert result["needs_reflection"] is True
        assert result["failed_calls"] > 0

    def test_reflect_empty_response(self):
        """Test reflection with empty response."""
        tool_calls = []
        
        result = self.sr.reflect("test query", tool_calls, "")
        
        assert result["needs_reflection"] is True
        assert result["response_length"] == 0


class TestStackAgent:
    """Test StackAgent class."""

    def setup_method(self):
        """Set up test instance."""
        with patch('stack_cli.context.create_context_manager'):
            self.agent = StackAgent()

    def test_agent_creation(self):
        """Test agent is created correctly."""
        assert self.agent is not None
        assert self.agent.query_understanding is not None
        assert self.agent.tool_selector is not None
        assert self.agent.response_generator is not None
        assert self.agent.self_reflection is not None

    def test_process_simple_query(self):
        """Test processing a simple query."""
        with patch('stack_cli.tools.get_tool') as mock_get_tool:
            mock_tool = MagicMock(return_value={"success": True, "content": "test"})
            mock_get_tool.return_value = mock_tool
            
            response = self.agent.process("read test.py")
            
            assert response is not None
            assert response.content is not None
            assert isinstance(response, AgentResponse)

    def test_process_with_tools(self):
        """Test processing with forced tools."""
        with patch('stack_cli.tools.get_tool') as mock_get_tool:
            mock_tool = MagicMock(return_value={"success": True})
            mock_get_tool.return_value = mock_tool
            
            response = self.agent.process_with_tools("test", ["read"])
            
            assert response is not None
            assert isinstance(response, AgentResponse)

    def test_get_context(self):
        """Test getting context."""
        context = self.agent.get_context()
        
        assert context is not None
        assert isinstance(context, str)

    def test_get_schemas(self):
        """Test getting tool schemas."""
        schemas = self.agent.get_schemas()
        
        assert isinstance(schemas, list)
        if schemas:
            assert "name" in schemas[0]
            assert "description" in schemas[0]


class TestCreateAgent:
    """Test create_agent factory function."""

    def test_create_agent_default(self):
        """Test creating agent with defaults."""
        with patch('stack_cli.context.create_context_manager'):
            agent = create_agent()
            
            assert agent is not None
            assert isinstance(agent, StackAgent)

    def test_create_agent_custom_workspace(self):
        """Test creating agent with custom workspace."""
        with patch('stack_cli.context.create_context_manager'):
            agent = create_agent("/custom/path")
            
            assert agent is not None
            assert isinstance(agent, StackAgent)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
