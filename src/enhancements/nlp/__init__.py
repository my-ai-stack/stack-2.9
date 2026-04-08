"""
NLP Enhancement Module

Provides:
- Contextual embeddings (BERT, RoBERTa)
- Entity recognition
- Intent detection
"""

from .contextual_embeddings import ContextualEmbedder
from .entity_recognition import EntityRecognizer
from .intent_detection import IntentDetector

__all__ = [
    "ContextualEmbedder",
    "EntityRecognizer",
    "IntentDetector",
]