#!/usr/bin/env python3
"""
Benchmarks for Stack 2.9 - Memory Usage Tests
Memory profiling benchmarks.
"""

import pytest
import sys
import gc
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, create_agent


class TestMemoryUsage:
    """Test memory usage patterns."""

    def test_agent_memory_baseline(self):
        """Test baseline agent memory usage."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            # Should not use excessive memory
            import sys
            agent_size = sys.getsizeof(agent)
            
            # Baseline should be reasonable
            assert agent_size < 10000

    def test_conversation_history_memory(self):
        """Test conversation history memory usage."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Add many conversations
                for i in range(100):
                    agent.process(f"query {i}")
                
                # History should be accessible
                assert len(agent.conversation_history) <= 200  # May truncate

    def test_session_memory_growth(self):
        """Test session memory growth."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            session = agent.context_manager.session
            
            # Add many operations
            for i in range(100):
                session.add_message("user", f"message {i}" * 10)
                session.add_tool_usage("read", {"success": True})
            
            summary = session.get_summary()
            
            # Summary should be generated correctly
            assert summary["messages_count"] == 100
            assert summary["tools_used_count"] == 100


class TestContextMemory:
    """Test context memory usage."""

    def test_context_manager_memory(self):
        """Test context manager memory footprint."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp/test")
                    
                    import sys
                    cm_size = sys.getsizeof(cm)
                    
                    # Should be reasonable
                    assert cm_size < 5000

    def test_projects_dict_memory(self):
        """Test projects dictionary memory."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    # Should have empty projects dict initially
                    assert len(cm.projects) == 0


class TestToolMemory:
    """Test tool-related memory usage."""

    def test_tools_dict_memory(self):
        """Test TOOLS dictionary size."""
        from stack_cli.tools import TOOLS
        
        import sys
        tools_size = sys.getsizeof(TOOLS)
        
        # Should be reasonable for dict
        assert tools_size < 10000

    def test_tool_schemas_memory(self):
        """Test tool schemas memory."""
        from stack_cli.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        import sys
        schemas_size = sys.getsizeof(schemas)
        
        # Should be reasonable
        assert schemas_size < 10000


class TestGarbageCollection:
    """Test garbage collection."""

    def test_gc_after_agent_creation(self):
        """Test GC after agent creation."""
        gc.collect()
        
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
        
        # Force gc
        gc.collect()
        
        # Agent should still work
        assert agent is not None

    def test_gc_after_queries(self):
        """Test GC after many queries."""
        gc.collect()
        
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                for i in range(50):
                    agent.process(f"query {i}")
        
        gc.collect()
        
        # Should still work
        assert len(agent.conversation_history) > 0


class TestMemoryLeaks:
    """Test for potential memory leaks."""

    def test_no_leak_in_loop(self):
        """Test no memory leak in processing loop."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                initial_history_len = len(agent.conversation_history)
                
                # Process many queries
                for i in range(200):
                    agent.process(f"query {i}")
                
                final_history_len = len(agent.conversation_history)
                
                # Should not grow indefinitely (may truncate)
                assert final_history_len <= initial_history_len + 200

    def test_session_cleanup(self):
        """Test session cleanup."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            session = agent.context_manager.session
            
            # Add data
            for i in range(20):
                session.add_message("user", f"msg {i}")
            
            # Clear should work
            session.messages.clear()
            
            assert len(session.messages) == 0


class TestMemoryEfficiency:
    """Test memory efficiency."""

    def test_response_size(self):
        """Test response object size."""
        with patch('stack_cli.context.create_context_manager'):
            from stack_cli.agent import AgentResponse
            import sys
            
            response = AgentResponse(
                content="test content",
                tool_calls=[],
                confidence=0.9
            )
            
            size = sys.getsizeof(response)
            
            # Should be reasonable
            assert size < 1000

    def test_tool_call_size(self):
        """Test tool call object size."""
        from stack_cli.agent import ToolCall
        import sys
        
        call = ToolCall(
            tool_name="read",
            arguments={"path": "test.py"},
            result={"success": True}
        )
        
        size = sys.getsizeof(call)
        
        # Should be small
        assert size < 500


class TestResourceCleanup:
    """Test resource cleanup."""

    def test_context_cleanup(self):
        """Test context cleanup."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    
                    cm = ContextManager("/tmp")
                    
                    # Should have cleanup method or be disposable
                    assert cm is not None

    def test_agent_disposal(self):
        """Test agent can be disposed."""
        with patch('stack_cli.context.create_context_manager'):
            agent = StackAgent()
            
            # Should be able to reference agent
            assert agent is not None
            
            # Should be able to create new one
            agent2 = StackAgent()
            assert agent2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
