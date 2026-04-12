"""
Stack 2.9 Enhancement Configuration
Central configuration for all enhancement features.
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class NLPConfig:
    """Configuration for NLP enhancements."""
    use_bert_embeddings: bool = True
    bert_model: str = "bert-base-uncased"
    use_entity_recognition: bool = True
    use_intent_detection: bool = True
    max_context_length: int = 512
    embedding_cache_size: int = 1000


@dataclass
class KnowledgeGraphConfig:
    """Configuration for knowledge graph."""
    enabled: bool = True
    backend: str = "networkx"  # or "neo4j"
    max_nodes: int = 10000
    max_edges: int = 50000
    similarity_threshold: float = 0.7
    rag_enabled: bool = True
    rag_top_k: int = 5


@dataclass
class EmotionalIntelligenceConfig:
    """Configuration for emotional intelligence."""
    enabled: bool = True
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    detect_emotions: bool = True
    empathetic_responses: bool = True
    emotion_sensitivity: float = 0.5


@dataclass
class CollaborationConfig:
    """Configuration for collaboration features."""
    mcp_enabled: bool = True
    conversation_state_enabled: bool = True
    max_sessions: int = 10
    session_timeout_minutes: int = 60


@dataclass
class LearningConfig:
    """Configuration for learning and adaptation."""
    enabled: bool = True
    feedback_storage_path: str = "data/feedback"
    auto_finetune: bool = False
    finetune_every_n_feedback: int = 100
    performance_monitoring: bool = True


@dataclass
class EnhancementConfig:
    """Main configuration for all enhancements."""
    nlp: NLPConfig = field(default_factory=NLPConfig)
    knowledge_graph: KnowledgeGraphConfig = field(default_factory=KnowledgeGraphConfig)
    emotional_intelligence: EmotionalIntelligenceConfig = field(default_factory=EmotionalIntelligenceConfig)
    collaboration: CollaborationConfig = field(default_factory=CollaborationConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)

    # Global enable/disable
    all_enabled: bool = True

    @classmethod
    def from_env(cls) -> "EnhancementConfig":
        """Create config from environment variables."""
        config = cls()

        # NLP settings
        if os.getenv("NLP_USE_BERT"):
            config.nlp.use_bert_embeddings = os.getenv("NLP_USE_BERT").lower() == "true"
        if os.getenv("NLP_BERT_MODEL"):
            config.nlp.bert_model = os.getenv("NLP_BERT_MODEL")

        # Knowledge graph settings
        if os.getenv("KG_ENABLED"):
            config.knowledge_graph.enabled = os.getenv("KG_ENABLED").lower() == "true"
        if os.getenv("KG_RAG_ENABLED"):
            config.knowledge_graph.rag_enabled = os.getenv("KG_RAG_ENABLED").lower() == "true"

        # Emotional intelligence settings
        if os.getenv("EI_ENABLED"):
            config.emotional_intelligence.enabled = os.getenv("EI_ENABLED").lower() == "true"

        # Learning settings
        if os.getenv("LEARNING_ENABLED"):
            config.learning.enabled = os.getenv("LEARNING_ENABLED").lower() == "true"

        return config


# Global config instance
_default_config: Optional[EnhancementConfig] = None


def get_config() -> EnhancementConfig:
    """Get the global enhancement config instance."""
    global _default_config
    if _default_config is None:
        _default_config = EnhancementConfig.from_env()
    return _default_config


def set_config(config: EnhancementConfig) -> None:
    """Set the global enhancement config instance."""
    global _default_config
    _default_config = config