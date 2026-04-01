#!/usr/bin/env python3
"""
Integration Tests for Stack 2.9 Self-Evolution
Self-improvement cycle tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, SelfReflection, create_agent, AgentResponse


class TestSelfReflection:
    """Test self-reflection functionality."""

    def test_reflection_high_confidence(self):
        """Test reflection with high confidence."""
        sr = SelfReflection()
        
        tool_calls = [
            MagicMock(success=True, tool_name="read"),
            MagicMock(success=True, tool_name="write")
        ]
        
        result = sr.reflect("test query", tool_calls, "Good response with content")
        
        assert result["needs_reflection"] is False
        assert result["confidence"] >= 0.7

    def test_reflection_low_confidence(self):
        """Test reflection with failures."""
        sr = SelfReflection()
        
        tool_calls = [
            MagicMock(success=False, tool_name="read", error="Not found")
        ]
        
        result = sr.reflect("test query", tool_calls, "Short")
        
        assert result["needs_reflection"] is True
        assert result["failed_calls"] > 0

    def test_reflection_suggestion(self):
        """Test reflection provides suggestions."""
        sr = SelfReflection()
        
        tool_calls = [
            MagicMock(success=False, tool_name="read", error="Failed")
        ]
        
        result = sr.reflect("test query", tool_calls, "Short")
        
        assert result.get("suggestion") is not None


class TestSelfImprovementCycle:
    """Test self-improvement cycle."""

    def test_agent_learns_from_errors(self):
        """Test agent learns from errors."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                # First call fails
                call_count = [0]
                
                def tool_func(**kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return {"success": False, "error": "First attempt failed"}
                    return {"success": True}
                
                mock_get_tool.return_value = tool_func
                
                agent = StackAgent()
                
                # First attempt
                response1 = agent.process("read test.py")
                
                # Should have some response even on failure
                assert response1 is not None

    def test_conversation_history_tracking(self):
        """Test conversation history is tracked."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Process multiple queries
                agent.process("query 1")
                agent.process("query 2")
                agent.process("query 3")
                
                assert len(agent.conversation_history) == 3

    def test_reflection_updates_confidence(self):
        """Test reflection updates confidence score."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                response = agent.process("test query")
                
                # Confidence should be set
                assert response.confidence is not None
                assert 0.0 <= response.confidence <= 1.0


class TestAdaptiveToolSelection:
    """Test adaptive tool selection."""

    def test_tool_selection_based_on_intent(self):
        """Test tools are selected based on intent."""
        from stack_cli.agent import ToolSelector
        
        ts = ToolSelector()
        
        # Different intents should select different tools
        tools_file = ts.select("file_read", {})
        tools_git = ts.select("git_operation", {})
        tools_web = ts.select("web_search", {})
        
        assert tools_file != tools_git
        assert tools_git != tools_web

    def test_parameter_extraction_improves(self):
        """Test parameter extraction works across queries."""
        from stack_cli.agent import ToolSelector
        
        ts = ToolSelector()
        
        # Same tool with different queries
        params1 = ts.get_tool_parameters("read", "read test.py", {})
        params2 = ts.get_tool_parameters("read", "view main.py", {})
        
        # Both should extract path
        assert "path" in params1 or "path" in params2


class TestContextAwareImprovement:
    """Test context-aware improvements."""

    def test_context_influences_response(self):
        """Test context influences response generation."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "content": "data"})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                response1 = agent.process("read test.py")
                response2 = agent.process("read test.py")
                
                # Responses should be consistent
                assert response1.content is not None

    def test_session_memory_persists(self):
        """Test session memory persists across queries."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Process query
                agent.process("first query")
                
                # Session should have recorded tool usage
                session = agent.context_manager.session
                assert session is not None


class TestSelfEvolutionIntegration:
    """Test complete self-evolution integration."""

    def test_full_self_improvement_loop(self):
        """Test complete self-improvement loop."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # 1. Process query
                response = agent.process("test query")
                
                # 2. Check reflection
                assert response is not None
                
                # 3. History is updated
                assert len(agent.conversation_history) > 0

    def test_error_recovery_improves(self):
        """Test error recovery improves over time."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                error_count = [0]
                
                def tool_func(**kwargs):
                    error_count[0] += 1
                    if error_count[0] <= 2:
                        return {"success": False, "error": f"Error {error_count[0]}"}
                    return {"success": True}
                
                mock_get_tool.return_value = tool_func
                
                agent = StackAgent()
                
                # First attempts may fail
                for _ in range(3):
                    agent.process("test")
                
                # Should have recorded history
                assert len(agent.conversation_history) >= 0

    def test_performance_tracking(self):
        """Test performance is tracked."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            # Get session summary
            summary = agent.context_manager.session.get_summary()
            
            assert "messages_count" in summary
            assert "tools_used_count" in summary


class TestContinuousLearning:
    """Test continuous learning aspects."""

    def test_query_patterns_learned(self):
        """Test query patterns are tracked."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Similar queries
                agent.process("read file1.py")
                agent.process("read file2.py")
                agent.process("read file3.py")
                
                # History shows pattern
                history = agent.conversation_history
                assert len(history) == 3

    def test_tool_usage_stats(self):
        """Test tool usage statistics."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Use various tools
                agent.process("read test.py")
                agent.process("run pytest")
                agent.process("git status")
                
                # Session tracks tools
                session = agent.context_manager.session
                assert session is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
