"""
Stack 2.9 Enhancement Modules

This package provides comprehensive enhancements for the Stack 2.9 model:
- NLP: Contextual embeddings, entity recognition, intent detection
- Knowledge Graph: Graph-based knowledge with RAG support
- Emotional Intelligence: Sentiment analysis and empathetic responses
- Collaboration: MCP integration, conversation state management
- Learning: Feedback collection, continuous improvement
"""

from .config import (
    EnhancementConfig,
    NLPConfig,
    KnowledgeGraphConfig,
    EmotionalIntelligenceConfig,
    CollaborationConfig,
    LearningConfig,
    get_config,
    set_config,
)

__version__ = "2.9.0"

__all__ = [
    "EnhancementConfig",
    "NLPConfig",
    "KnowledgeGraphConfig",
    "EmotionalIntelligenceConfig",
    "CollaborationConfig",
    "LearningConfig",
    "get_config",
    "set_config",
]