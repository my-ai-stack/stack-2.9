"""Stack 2.9 CLI and Agent Interface."""

__version__ = "2.9.0"
__author__ = "Stack Team"

from .agent import create_agent, StackAgent
from .tools import TOOLS, list_tools, get_tool, get_tool_schemas
from .context import create_context_manager, ContextManager

__all__ = [
    "create_agent",
    "StackAgent",
    "TOOLS",
    "list_tools",
    "get_tool",
    "get_tool_schemas",
    "create_context_manager",
    "ContextManager"
]
