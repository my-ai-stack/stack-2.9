#!/usr/bin/env python3
"""
Benchmarks for Stack 2.9 - Latency Tests
Response time benchmarks.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, create_agent
from stack_cli.tools import get_tool


class TestQueryLatency:
    """Test query processing latency."""

    def test_simple_query_latency(self):
        """Test latency of simple query."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                agent.process("simple query")
                elapsed = time.time() - start
                
                assert elapsed < 1.0  # Should complete in under 1 second

    def test_file_read_latency(self):
        """Test file read operation latency."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True, "content": "x"})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                agent.process("read test.py")
                elapsed = time.time() - start
                
                assert elapsed < 0.5

    def test_git_operation_latency(self):
        """Test git operation latency."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                agent.process("git status")
                elapsed = time.time() - start
                
                assert elapsed < 1.0


class TestToolLatency:
    """Test individual tool latencies."""

    def test_get_tool_latency(self):
        """Test get_tool lookup latency."""
        start = time.time()
        
        for _ in range(1000):
            get_tool("read")
        
        elapsed = time.time() - start
        
        # 1000 lookups should be very fast
        assert elapsed < 0.1

    def test_list_tools_latency(self):
        """Test list_tools latency."""
        from stack_cli.tools import list_tools
        
        start = time.time()
        
        for _ in range(100):
            tools = list_tools()
        
        elapsed = time.time() - start
        
        assert elapsed < 0.1
        assert len(tools) > 30

    def test_schemas_lookup_latency(self):
        """Test tool schemas lookup latency."""
        from stack_cli.tools import get_tool_schemas
        
        start = time.time()
        
        for _ in range(100):
            schemas = get_tool_schemas()
        
        elapsed = time.time() - start
        
        assert elapsed < 0.1


class TestContextLatency:
    """Test context operation latencies."""

    def test_context_summary_latency(self):
        """Test getting context summary latency."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    cm = ContextManager("/tmp")
                    
                    start = time.time()
                    
                    for _ in range(100):
                        cm.get_context_summary()
                    
                    elapsed = time.time() - start
                    
                    assert elapsed < 0.5

    def test_workspace_context_latency(self):
        """Test workspace context generation latency."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.context.Path') as mock_path:
                with patch.object(Path, 'exists', return_value=False):
                    from stack_cli.context import ContextManager
                    cm = ContextManager("/tmp")
                    
                    start = time.time()
                    
                    for _ in range(100):
                        cm.get_workspace_context()
                    
                    elapsed = time.time() - start
                    
                    assert elapsed < 0.5


class TestAgentLatency:
    """Test agent operation latencies."""

    def test_intent_parsing_latency(self):
        """Test intent parsing latency."""
        from stack_cli.agent import QueryUnderstanding
        
        qu = QueryUnderstanding()
        
        start = time.time()
        
        for _ in range(1000):
            qu.parse("read test.py")
        
        elapsed = time.time() - start
        
        assert elapsed < 0.5

    def test_tool_selection_latency(self):
        """Test tool selection latency."""
        from stack_cli.agent import ToolSelector
        
        ts = ToolSelector()
        
        start = time.time()
        
        for _ in range(1000):
            ts.select("file_read", {})
        
        elapsed = time.time() - start
        
        assert elapsed < 0.5


class TestMemoryLatency:
    """Test memory operation latencies."""

    def test_session_memory_latency(self):
        """Test session memory operations."""
        from stack_cli.context import SessionMemory
        
        session = SessionMemory()
        
        start = time.time()
        
        for i in range(1000):
            session.add_message("user", f"message {i}")
        
        elapsed = time.time() - start
        
        assert elapsed < 0.5

    def test_summary_generation_latency(self):
        """Test summary generation latency."""
        from stack_cli.context import SessionMemory
        
        session = SessionMemory()
        
        for i in range(100):
            session.add_message("user", f"message {i}")
            session.add_tool_usage("read", {"success": True})
        
        start = time.time()
        
        for _ in range(1000):
            session.get_summary()
        
        elapsed = time.time() - start
        
        assert elapsed < 0.5


class TestOverallLatency:
    """Test overall system latency."""

    def test_full_query_cycle_latency(self):
        """Test full query processing cycle."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                latencies = []
                
                for i in range(10):
                    start = time.time()
                    agent.process(f"query {i}")
                    latencies.append(time.time() - start)
                
                avg_latency = sum(latencies) / len(latencies)
                
                # Average should be reasonable
                assert avg_latency < 0.5

    def test_batch_query_latency(self):
        """Test batch query processing."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                
                for i in range(50):
                    agent.process(f"batch query {i}")
                
                elapsed = time.time() - start
                
                # 50 queries should complete reasonably fast
                assert elapsed < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
