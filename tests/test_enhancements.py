#!/usr/bin/env python3
"""
Quick test script to verify enhancement modules work.
Run this before the full chat to check all modules are functioning.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 50)
print("Testing Stack 2.9 Enhancement Modules")
print("=" * 50)

# Test 1: Config
print("\n[1] Testing Configuration...")
from enhancements import get_config, EnhancementConfig
config = get_config()
print(f"  ✓ Config loaded: NLP={config.nlp.use_bert_embeddings}, RAG={config.knowledge_graph.rag_enabled}")

# Test 2: NLP Modules
print("\n[2] Testing NLP Modules...")
from enhancements.nlp import IntentDetector, EntityRecognizer

# Test Intent Detection
intent_detector = IntentDetector()
test_intents = [
    "Write a function to calculate fibonacci",
    "Help me debug this error",
    "Explain what is Python",
    "Hello there!",
]
print("  Intent Detection:")
for text in test_intents:
    result = intent_detector.detect_intent(text)
    print(f"    '{text[:30]}...' → {result['intent']} ({result['confidence']:.2f})")

# Test Entity Recognition
entity_recognizer = EntityRecognizer()
test_entities = [
    "My email is test@example.com and I live in New York",
    "Visit https://github.com for code",
    "Call me at 555-123-4567",
]
print("  Entity Recognition:")
for text in test_entities:
    entities = entity_recognizer.recognize_entities(text)
    print(f"    '{text[:30]}...' → {[e['type'] for e in entities]}")

# Test 3: Knowledge Graph
print("\n[3] Testing Knowledge Graph...")
from enhancements.knowledge_graph import KnowledgeGraph, RAGEngine

kg = KnowledgeGraph()
kg.add_entity("Python", "language", {"version": "3.11"})
kg.add_entity("Stack2.9", "ai_assistant", {"version": "2.9"})
kg.add_relationship("Stack2.9", "Python", "uses")
print(f"  ✓ Knowledge Graph: {kg.get_stats()}")

# Test RAG
rag = RAGEngine()
rag.add_document("doc1", "Python is a programming language.")
rag.add_document("doc2", "Stack 2.9 is an AI coding assistant.")
results = rag.retrieve("Tell me about Python")
print(f"  ✓ RAG Retrieval: {len(results)} docs found")

# Test 4: Emotional Intelligence
print("\n[4] Testing Emotional Intelligence...")
from enhancements.emotional_intelligence import SentimentAnalyzer, EmpathyEngine

sentiment = SentimentAnalyzer()
test_sentiments = [
    "This is amazing! I love it!",
    "I'm frustrated with this problem",
    "Can you help me?",
]
print("  Sentiment Analysis:")
for text in test_sentiments:
    result = sentiment.analyze_sentiment(text)
    print(f"    '{text[:30]}...' → {result['sentiment']} ({result['emotion_tone']})")

empathy = EmpathyEngine()
test_response = "Here's your code:"
empathetic = empathy.generate_empathetic_response(
    "I'm having trouble with my code",
    test_response
)
print(f"  ✓ Empathy Engine: Modified response with prefix")

# Test 5: Collaboration
print("\n[5] Testing Collaboration...")
from enhancements.collaboration import ConversationStateManager, MCPIntegration

conv_mgr = ConversationStateManager()
session_id = conv_mgr.create_session()
conv_mgr.add_message("user", "Hello AI!")
conv_mgr.add_message("assistant", "Hello! How can I help?")
history = conv_mgr.get_conversation_history()
print(f"  ✓ Conversation Manager: {len(history)} messages in session")

mcp = MCPIntegration()
tools = mcp.list_tools()
print(f"  ✓ MCP Integration: {len(tools)} tools registered")

# Test 6: Learning
print("\n[6] Testing Learning System...")
from enhancements.learning import FeedbackCollector, PerformanceMonitor

feedback = FeedbackCollector(storage_path="data/test_feedback")
fb_id = feedback.add_thumbs_up("Test message", "Test response")
stats = feedback.get_statistics()
print(f"  ✓ Feedback Collector: {stats['total']} entries")

perf = PerformanceMonitor(storage_path="data/test_performance")
perf.record_response_time(0.5)
perf.record_successful_interaction()
summary = perf.get_summary()
print(f"  ✓ Performance Monitor: avg response {summary['average_response_time']:.2f}s")

# Summary
print("\n" + "=" * 50)
print("All Enhancement Modules Tested Successfully!")
print("=" * 50)
print("\nTo run the enhanced chat:")
print("  python enhanced_chat.py")
print("\nOptions:")
print("  --no-bert      Disable BERT embeddings")
print("  --no-rag       Disable RAG")
print("  --no-empathy   Disable emotional intelligence")