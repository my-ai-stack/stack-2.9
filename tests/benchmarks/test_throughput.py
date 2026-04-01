#!/usr/bin/env python3
"""
Benchmarks for Stack 2.9 - Throughput Tests
Concurrency and throughput benchmarks.
"""

import pytest
import sys
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent / "stack_cli"))

from stack_cli.agent import StackAgent, create_agent


class TestConcurrentQueries:
    """Test concurrent query handling."""

    def test_sequential_throughput(self):
        """Test sequential query throughput."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                
                for i in range(20):
                    agent.process(f"query {i}")
                
                elapsed = time.time() - start
                throughput = 20 / elapsed
                
                # Should handle at least 5 queries per second
                assert throughput > 5

    def test_rapid_fire_queries(self):
        """Test rapid fire query submission."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Submit quickly
                results = []
                start = time.time()
                
                for i in range(10):
                    results.append(agent.process(f"rapid {i}"))
                
                elapsed = time.time() - start
                
                assert len(results) == 10
                assert elapsed < 3.0


class TestThreadSafety:
    """Test thread safety."""

    def test_concurrent_agent_creation(self):
        """Test concurrent agent creation."""
        agents = []
        
        def create_agent_thread():
            with patch('stack_cli.context.create_context_manager'):
                agents.append(create_agent())
        
        threads = []
        
        for _ in range(5):
            t = threading.Thread(target=create_agent_thread)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(agents) == 5

    def test_concurrent_tool_access(self):
        """Test concurrent tool access."""
        from stack_cli.tools import get_tool, list_tools
        
        results = []
        
        def access_tools():
            for _ in range(10):
                tool = get_tool("read")
                tools = list_tools()
                results.append((tool is not None, len(tools) > 0))
        
        threads = []
        
        for _ in range(3):
            t = threading.Thread(target=access_tools)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All accesses should succeed
        assert all(success for success, _ in results)


class TestBatchProcessing:
    """Test batch processing capabilities."""

    def test_batch_file_operations(self):
        """Test batch file operations."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                files = [f"file{i}.py" for i in range(10)]
                
                start = time.time()
                
                for f in files:
                    get_tool("read")(path=f)
                
                elapsed = time.time() - start
                
                assert elapsed < 2.0

    def test_batch_tool_chains(self):
        """Test batch tool chains."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                chains = [
                    ("read", {"path": "a.py"}),
                    ("write", {"path": "b.py", "content": "x"}),
                    ("grep", {"path": ".", "pattern": "test"}),
                ]
                
                start = time.time()
                
                for tool_name, params in chains * 5:
                    get_tool(tool_name)(**params)
                
                elapsed = time.time() - start
                
                assert elapsed < 2.0


class TestThroughputMetrics:
    """Test throughput metrics."""

    def test_queries_per_second(self):
        """Test queries per second throughput."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                start = time.time()
                query_count = 30
                
                for i in range(query_count):
                    agent.process(f"query {i}")
                
                elapsed = time.time() - start
                qps = query_count / elapsed
                
                # Should achieve reasonable QPS
                assert qps > 3, f"QPS too low: {qps}"

    def test_tools_per_second(self):
        """Test tools per second throughput."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                start = time.time()
                tool_count = 100
                
                for i in range(tool_count):
                    get_tool("read")(path=f"file{i}.py")
                
                elapsed = time.time() - start
                tps = tool_count / elapsed
                
                # Should be very fast
                assert tps > 50


class TestConcurrentContext:
    """Test concurrent context operations."""

    def test_concurrent_context_updates(self):
        """Test concurrent context updates."""
        from stack_cli.context import SessionMemory
        
        session = SessionMemory()
        errors = []
        
        def update_session(i):
            try:
                session.add_message("user", f"message {i}")
                session.add_tool_usage("read", {"success": True})
            except Exception as e:
                errors.append(e)
        
        threads = []
        
        for i in range(10):
            t = threading.Thread(target=update_session, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert len(errors) == 0
        assert len(session.messages) == 10


class TestResourceUtilization:
    """Test resource utilization."""

    def test_memory_usage_stable(self):
        """Test memory usage remains stable."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                
                # Process many queries
                for i in range(100):
                    agent.process(f"query {i}")
                
                # History should not grow unbounded
                # (Old entries may be truncated in real implementation)
                assert len(agent.conversation_history) <= 200

    def test_context_growth_bounded(self):
        """Test context growth is bounded."""
        with patch('stack_cli.context.create_context_manager'):
            with patch('stack_cli.tools.get_tool') as mock_get_tool:
                mock_tool = MagicMock(return_value={"success": True})
                mock_get_tool.return_value = mock_tool
                
                agent = StackAgent()
                session = agent.context_manager.session
                
                # Add many operations
                for i in range(50):
                    session.add_message("user", f"msg {i}")
                    session.add_tool_usage("read", {"success": True})
                
                summary = session.get_summary()
                
                # Counts should be accurate
                assert summary["messages_count"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
