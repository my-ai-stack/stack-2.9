"""
Collaboration Module

Provides collaboration features and conversational flow management.
"""

from .conversation_state import ConversationStateManager
from .mcp_integration import MCPIntegration

__all__ = [
    "ConversationStateManager",
    "MCPIntegration",
]