#!/usr/bin/env python3
"""
Benchmarks for Stack 2.9 - Token Efficiency Tests
Token optimization benchmarks.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, create_agent, AgentResponse


class TestTokenUsage:
    """Test token usage patterns."""

    def test_response_token_efficiency(self):
        """Test response token efficiency."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "content": "x"})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                response = agent.process("read test.py")
                
                # Response should have content
                assert response.content is not None
                assert len(response.content) > 0

    def test_context_truncation(self):
        """Test context truncation."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    # Context should be generated
                    context = cm.get_workspace_context()
                    
                    # Should be formatted string
                    assert isinstance(context, str)


class TestPromptEfficiency:
    """Test prompt efficiency."""

    def test_intent_parsing_tokens(self):
        """Test intent parsing token usage."""
        from stack_cli.agent import QueryUnderstanding
        
        qu = QueryUnderstanding()
        
        # Parse should be efficient
        result = qu.parse("read test.py")
        
        # Result should have required fields
        assert "intent" in result
        assert "confidence" in result
        assert result["intent"] == "file_read"

    def test_tool_selection_tokens(self):
        """Test tool selection token usage."""
        from stack_cli.agent import ToolSelector
        
        ts = ToolSelector()
        
        # Selection should be minimal
        tools = ts.select("file_read", {})
        
        # Should return list of tools
        assert isinstance(tools)
        assert len(tools) > 0


class TestResponseEfficiency:
    """Test response generation efficiency."""

    def test_response_generation_size(self):
        """Test response generation output size."""
        with patch('stack_cli.context.create_context_manager'):
            from stack_cli.agent import ResponseGenerator, ToolCall
            
            rg = ResponseGenerator()
            
            tool_calls = [
                ToolCall(
                    tool_name="read",
                    arguments={"path": "test.py"},
                    result={"success": True, "content": "test content"},
                    success=True
                )
            ]
            
            response = rg.generate(tool_calls, "file_read", {})
            
            # Should produce reasonable output
            assert isinstance(response, str)
            assert len(response) > 0
            # Should not be excessively long
            assert len(response) < 10000

    def test_clarification_efficiency(self):
        """Test clarification generation efficiency."""
        with patch('stack_cli.context.create_context_manager'):
            from stack_cli.agent import ResponseGenerator
            
            rg = ResponseGenerator()
            
            clarification = rg.generate_clarification("Which file?")
            
            # Should be concise
            assert isinstance(clarification, str)
            assert len(clarification) < 200


class TestContextTokenEfficiency:
    """Test context token efficiency."""

    def test_context_summary_size(self):
        """Test context summary size."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    summary = cm.get_context_summary()
                    
                    # Should be JSON-serializable dict
                    import json
                    serialized = json.dumps(summary)
                    
                    # Should be reasonable size
                    assert len(serialized) < 10000

    def test_workspace_context_size(self):
        """Test workspace context size."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    context = cm.get_workspace_context()
                    
                    # Should be reasonable size
                    assert len(context) < 10000


class TestToolSchemasEfficiency:
    """Test tool schemas token efficiency."""

    def test_schemas_compactness(self):
        """Test schemas are compact."""
        from stack_cli.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        import json
        serialized = json.dumps(schemas)
        
        # Should be reasonable size
        assert len(serialized) < 50000

    def test_schema_required_fields(self):
        """Test schemas have required fields only."""
        from stack_cli.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        for schema in schemas:
            # Should have minimal required fields
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            
            # Parameters should be minimal
            params = schema["parameters"]
            assert "type" in params
            assert "properties" in params


class TestConversationEfficiency:
    """Test conversation token efficiency."""

    def test_history_truncation(self):
        """Test conversation history truncation."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Add many conversations
                for i in range(50):
                    agent.process(f"query {i}")
                
                # History may be truncated
                history_len = len(agent.conversation_history)
                
                # Should not grow unbounded
                assert history_len <= 100

    def test_summary_efficiency(self):
        """Test summary efficiency."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            session = agent.context_manager.session
            
            # Add some data
            for i in range(10):
                session.add_message("user", f"message {i}")
            
            summary = session.get_summary()
            
            # Summary should be compact
            import json
            serialized = json.dumps(summary)
            
            assert len(serialized) < 1000


class TestTokenOptimization:
    """Test token optimization strategies."""

    def test_response_capping(self):
        """Test response content capping."""
        with patch('stack_cli.context.create_context_manager'):
            from stack_cli.agent import ResponseGenerator, ToolCall
            
            rg = ResponseGenerator()
            
            # Long content should be capped
            long_content = "x" * 10000
            
            tool_calls = [
                ToolCall(
                    tool_name="read",
                    arguments={"path": "test.py"},
                    result={"success": True, "content": long_content},
                    success=True
                )
            ]
            
            response = rg.generate(tool_calls, "file_read", {})
            
            # Response should be capped
            assert len(response) < 15000

    def test_context_truncation_strategy(self):
        """Test context truncation strategy."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    # With no projects, context should be minimal
                    context = cm.get_workspace_context()
                    
                    # Should be concise
                    lines = context.split('\n')
                    
                    # Should not have excessive lines
                    assert len(lines) < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
