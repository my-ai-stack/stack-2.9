#!/usr/bin/env python3
"""
Stack 2.9 - Test Configuration and Fixtures
Pytest fixtures, mocks, and configuration.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass, field
from datetime import datetime

import pytest

# Add stack_cli to path
stack_cli_dir = Path(__file__).parent.parent / "stack_cli"
sys.path.insert(0, str(stack_cli_dir))


# ============================================================================
# FIXTURES: TEMP DIRECTORIES & FILES
# ============================================================================

@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    yield workspace
    # Cleanup handled by tmp_path


@pytest.fixture
def temp_project(temp_workspace):
    """Create a temporary project with files."""
    project = temp_workspace / "test_project"
    project.mkdir()
    
    # Create some test files
    (project / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["requests", "click"]
""")
    
    (project / "main.py").write_text("""
#!/usr/bin/env python3
\"\"\"Main module.\"\"\"

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
    
    (project / "README.md").write_text("# Test Project\n\nA test project.")
    
    (project / ".env.example").write_text("API_KEY=xxx")
    
    yield project


@pytest.fixture
def temp_file(temp_workspace):
    """Create a temporary file for testing."""
    file_path = temp_workspace / "test.txt"
    file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
    yield file_path


@pytest.fixture
def temp_git_repo(temp_project):
    """Create a temp git repo."""
    os.system(f"cd {temp_project} && git init -q")
    os.system(f"cd {temp_project} && git config user.email 'test@test.com'")
    os.system(f"cd {temp_project} && git config user.name 'Test User'")
    yield temp_project


# ============================================================================
# FIXTURES: MOCKS
# ============================================================================

@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    from stack_cli.agent import StackAgent, create_agent
    
    with patch('stack_cli.agent.create_context_manager') as mock_cm:
        mock_cm.return_value = MagicMock()
        agent = create_agent("/tmp")
    
    return agent


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    from stack_cli.context import ContextManager, SessionMemory, ProjectContext
    
    cm = MagicMock(spec=ContextManager)
    cm.session = MagicMock(spec=SessionMemory)
    cm.session.messages = []
    cm.session.tools_used = []
    cm.session.files_touched = []
    cm.session.commands_run = []
    cm.get_workspace_context.return_value = "# Mock Context"
    cm.get_context_summary.return_value = {"workspace": "/tmp", "projects": []}
    
    return cm


@pytest.fixture
def mock_tool():
    """Create a mock tool function."""
    def tool_func(**kwargs):
        return {"success": True, "result": "mocked"}
    return tool_func


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_path():
    """Mock Path operations."""
    with patch('pathlib.Path') as mock_path_class:
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.read_text.return_value = "mocked content"
        mock_path.write_text.return_value = None
        mock_path.rglob.return_value = []
        mock_path.__enter__ = MagicMock(return_value=mock_path)
        mock_path.__exit__ = MagicMock(return_value=False)
        
        mock_path_class.return_value = mock_path
        mock_path_class.exists.return_value = True
        
        yield mock_path_class


# ============================================================================
# FIXTURES: CONFIG OVERRIDES
# ============================================================================

@pytest.fixture
def config_override():
    """Override configuration values."""
    original_env = os.environ.copy()
    
    test_config = {
        "WORKSPACE_PATH": "/tmp/test_workspace",
        "MAX_CONTEXT_TOKENS": "4000",
        "ENABLE_SELF_REFLECTION": "true",
        "MAX_REFLECTION_ITERATIONS": "3"
    }
    
    os.environ.update(test_config)
    
    yield test_config
    
    # Restore original
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def fake_model():
    """Create a fake model for testing."""
    from dataclasses import dataclass
    
    @dataclass
    class FakeModelResponse:
        content: str = "Mocked response"
        tool_calls: list = field(default_factory=list)
        confidence: float = 1.0
    
    return FakeModelResponse


# ============================================================================
# FIXTURES: STACK CLI COMPONENTS
# ============================================================================

@pytest.fixture
def sample_tools():
    """Return list of all tool names."""
    return [
        # File ops
        "read", "write", "edit", "search", "grep", "copy", "move", "delete",
        # Git
        "git_status", "git_commit", "git_push", "git_pull", "git_branch", "git_log", "git_diff",
        # Code execution
        "run", "test", "lint", "format", "typecheck", "server", "install",
        # Web
        "web_search", "fetch", "download", "check_url", "screenshot",
        # Memory
        "memory_recall", "memory_save", "memory_list", "context_load", "project_scan",
        # Tasks
        "create_task", "list_tasks", "update_task", "delete_task", "create_plan", "execute_plan"
    ]


@pytest.fixture
def sample_agent_response():
    """Create a sample agent response."""
    from stack_cli.agent import AgentResponse, ToolCall
    
    tool_calls = [
        ToolCall(tool_name="read", arguments={"path": "test.py"}, result={"success": True}, success=True),
        ToolCall(tool_name="run", arguments={"command": "echo hello"}, result={"success": True}, success=True)
    ]
    
    return AgentResponse(
        content="Test response with tool results",
        tool_calls=tool_calls,
        context_used=["context1"],
        confidence=0.9,
        needs_clarification=False
    )


# ============================================================================
# FIXTURES: TEST DATA
# ============================================================================

@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return """#!/usr/bin/env python3
\"\"\"Sample module for testing.\"\"\"

def hello(name: str) -> str:
    \"\"\"Say hello.\"\"\"
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

class Calculator:
    \"\"\"Simple calculator.\"\"\"
    
    def __init__(self):
        self.value = 0
    
    def add(self, n):
        self.value += n
        return self
"""

@pytest.fixture
def sample_query_intents():
    """Sample queries and their expected intents."""
    return [
        ("read README.md", "file_read"),
        ("write test.py with content", "file_write"),
        ("edit config.json", "file_edit"),
        ("find files named *.py", "file_search"),
        ("git status", "git_operation"),
        ("run pytest", "code_execution"),
        ("search the web for python", "web_search"),
        ("remember this important thing", "memory"),
        ("create task to fix bug", "task"),
        ("what is python?", "question"),
    ]


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmark tests")
    config.addinivalue_line("markers", "asyncio: marks tests as async tests")


# Auto-use fixtures
@pytest.fixture(autouse=True)
def reset_sys_path():
    """Ensure sys.path is properly set."""
    stack_cli_dir = Path(__file__).parent.parent / "stack_cli"
    if str(stack_cli_dir) not in sys.path:
        sys.path.insert(0, str(stack_cli_dir))
    yield
