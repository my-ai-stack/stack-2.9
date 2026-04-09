#!/usr/bin/env python3
"""
Stack 2.9 Enhanced Chat Interface

Integrates all enhancement modules:
- NLP: Contextual embeddings, entity recognition, intent detection
- Knowledge Graph: RAG-based context retrieval
- Emotional Intelligence: Sentiment analysis, empathetic responses
- Collaboration: Multi-session conversation management
- Learning: Feedback collection, performance monitoring
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import enhancements
from enhancements import (
    get_config,
    EnhancementConfig,
    NLPConfig,
    KnowledgeGraphConfig,
    EmotionalIntelligenceConfig,
    CollaborationConfig,
    LearningConfig,
)

# Import enhancement modules
from enhancements.nlp import ContextualEmbedder, EntityRecognizer, IntentDetector
from enhancements.knowledge_graph import KnowledgeGraph, RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer, EmpathyEngine
from enhancements.collaboration import ConversationStateManager, MCPIntegration
from enhancements.learning import FeedbackCollector, PerformanceMonitor


class Stack2_9Enhanced:
    """Enhanced Stack 2.9 with all enhancement modules."""

    def __init__(
        self,
        model_path: str = "/Users/walidsobhi/stack-2-9-final-model",
        config: Optional[EnhancementConfig] = None,
    ):
        """
        Initialize enhanced Stack 2.9.

        Args:
            model_path: Path to the model
            config: Enhancement configuration (uses default if not provided)
        """
        self.model_path = model_path
        self.config = config or get_config()

        # Initialize model (loaded lazily)
        self._model = None
        self._tokenizer = None

        # Initialize enhancement modules
        self._init_modules()

        print("=" * 50)
        print("Stack 2.9 - Enhanced Edition")
        print("=" * 50)
        print("\nEnhancements loaded:")
        print(f"  • NLP: Intent Detection, Entity Recognition")
        print(f"  • Knowledge Graph: RAG Enabled")
        print(f"  • Emotional Intelligence: Sentiment + Empathy")
        print(f"  • Collaboration: Multi-session Support")
        print(f"  • Learning: Feedback + Performance Monitoring")
        print("\n" + "=" * 50)

    def _init_modules(self):
        """Initialize all enhancement modules."""
        # NLP Modules
        if self.config.nlp.use_bert_embeddings:
            self.embedder = ContextualEmbedder(
                model_name=self.config.nlp.bert_model,
                cache_size=self.config.nlp.embedding_cache_size,
            )
            print("  ✓ BERT Embeddings loaded")
        else:
            self.embedder = None

        if self.config.nlp.use_entity_recognition:
            self.entity_recognizer = EntityRecognizer()
            print("  ✓ Entity Recognition loaded")
        else:
            self.entity_recognizer = None

        if self.config.nlp.use_intent_detection:
            self.intent_detector = IntentDetector()
            print("  ✓ Intent Detection loaded")
        else:
            self.intent_detector = None

        # Knowledge Graph
        if self.config.knowledge_graph.enabled:
            self.knowledge_graph = KnowledgeGraph(
                max_nodes=self.config.knowledge_graph.max_nodes,
                max_edges=self.config.knowledge_graph.max_edges,
            )
            print("  ✓ Knowledge Graph initialized")
        else:
            self.knowledge_graph = None

        if self.config.knowledge_graph.rag_enabled:
            self.rag_engine = RAGEngine(
                top_k=self.config.knowledge_graph.rag_top_k,
                similarity_threshold=self.config.knowledge_graph.similarity_threshold,
            )
            # Add some seed documents
            self._seed_rag()
            print("  ✓ RAG Engine initialized")
        else:
            self.rag_engine = None

        # Emotional Intelligence
        if self.config.emotional_intelligence.enabled:
            self.sentiment_analyzer = SentimentAnalyzer()
            self.empathy_engine = EmpathyEngine()
            print("  ✓ Emotional Intelligence loaded")
        else:
            self.sentiment_analyzer = None
            self.empathy_engine = None

        # Collaboration
        if self.config.collaboration.conversation_state_enabled:
            self.conversation_manager = ConversationStateManager(
                max_sessions=self.config.collaboration.max_sessions,
                session_timeout_minutes=self.config.collaboration.session_timeout_minutes,
            )
            print("  ✓ Conversation Manager loaded")
        else:
            self.conversation_manager = None

        if self.config.collaboration.mcp_enabled:
            self.mcp = MCPIntegration()
            print("  ✓ MCP Integration loaded")
        else:
            self.mcp = None

        # Learning
        if self.config.learning.enabled:
            self.feedback_collector = FeedbackCollector(
                storage_path=self.config.learning.feedback_storage_path,
            )
            self.performance_monitor = PerformanceMonitor()
            print("  ✓ Learning System loaded")
        else:
            self.feedback_collector = None
            self.performance_monitor = None

    def _seed_rag(self):
        """Add seed documents to RAG engine."""
        seed_docs = [
            {
                "id": "intro",
                "content": "Stack 2.9 is an expert AI coding assistant. It helps with programming, debugging, and technical questions.",
            },
            {
                "id": "commands",
                "content": "Available commands: search:<query> for web search, quit/exit to end session, feedback to rate response.",
            },
            {
                "id": "capabilities",
                "content": "Stack 2.9 can: write code, debug errors, explain concepts, refactor code, analyze projects, and more.",
            },
        ]
        for doc in seed_docs:
            self.rag_engine.add_document(doc["id"], doc["content"])

    def load_model(self):
        """Lazy load the model from local files only."""
        if self._model is None:
            import os
            from pathlib import Path

            model_dir = Path(self.model_path)

            # Check local files exist
            required_files = ["model.safetensors", "config.json", "tokenizer.json"]
            missing = [f for f in required_files if not (model_dir / f).exists()]

            if missing:
                print(f"\n❌ Missing files: {missing}")
                print(f"   Model path: {self.model_path}")
                return

            print(f"\nLoading model from {self.model_path}...")
            print(f"   Found: {required_files}")
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Load from local files only - force no network
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(model_dir),
                local_files_only=True,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                str(model_dir),
                torch_dtype=torch.float16,
                device_map="auto",
                local_files_only=True,
            )
            print("✓ Model loaded from local files!\n")

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input with all enhancements.

        Returns:
            Dictionary with processed data
        """
        result = {
            "original_input": user_input,
            "entities": [],
            "intent": None,
            "sentiment": None,
            "rag_context": "",
            "response": None,
            "emotion_tone": "neutral",
        }

        # 1. Intent Detection
        if self.intent_detector:
            intent_result = self.intent_detector.detect_intent(user_input)
            result["intent"] = intent_result

        # 2. Entity Recognition
        if self.entity_recognizer:
            entities = self.entity_recognizer.recognize_entities(user_input)
            result["entities"] = entities

            # Add entities to knowledge graph
            if self.knowledge_graph:
                for entity in entities:
                    self.knowledge_graph.add_entity(
                        entity["text"],
                        entity["type"],
                        {"confidence": entity.get("score", 1.0)}
                    )

        # 3. Sentiment Analysis
        if self.sentiment_analyzer:
            sentiment = self.sentiment_analyzer.analyze_sentiment(user_input)
            result["sentiment"] = sentiment
            result["emotion_tone"] = self.sentiment_analyzer.get_tone_adjustment(user_input)

        # 4. RAG Context Retrieval
        if self.rag_engine:
            result["rag_context"] = self.rag_engine.retrieve_as_context(
                user_input,
                max_context_length=500
            )

        # 5. Conversation State
        if self.conversation_manager:
            self.conversation_manager.add_message("user", user_input)
            # Store context
            self.conversation_manager.update_context("last_intent", result["intent"]["intent"] if result["intent"] else None)

        return result

    def generate_response(
        self,
        user_input: str,
        processed_data: Dict[str, Any],
    ) -> str:
        """Generate model response with enhancements."""
        self.load_model()

        # Build enhanced prompt
        system_parts = ["You are Stack 2.9, an expert AI coding assistant."]

        # Add RAG context if available
        if processed_data.get("rag_context"):
            system_parts.append(f"\nContext: {processed_data['rag_context']}")

        # Add emotional tone guidance
        emotion_tone = processed_data.get("emotion_tone", "neutral")
        if emotion_tone == "empathetic":
            system_parts.append("\nBe empathetic and understanding.")
        elif emotion_tone == "enthusiastic":
            system_parts.append("\nBe enthusiastic and positive.")
        elif emotion_tone == "supportive":
            system_parts.append("\nBe supportive and reassuring.")

        system_prompt = " ".join(system_parts)

        # Build full prompt
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"

        # Generate
        start_time = time.time()
        inputs = self._tokenizer(full_prompt, return_tensors='pt').to(self._model.device)

        outputs = self._model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.4,
            top_p=0.9,
            repetition_penalty=1.2,
            do_sample=True,
            pad_token_id=self._tokenizer.eos_token_id
        )

        response_time = time.time() - start_time

        # Decode response
        full_response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract assistant response
        if "Assistant:" in full_response:
            response = full_response.split("Assistant:")[-1].strip()
        else:
            response = full_response[len(full_prompt):].strip()

        # Clean up response
        for stop in ['\n\n\n', 'User:', 'You:']:
            if stop in response:
                response = response.split(stop)[0].strip()

        # Apply empathy if emotional intelligence enabled
        if self.empathy_engine and processed_data.get("sentiment"):
            response = self.empathy_engine.generate_empathetic_response(
                user_input,
                response
            )

        # Record performance
        if self.performance_monitor:
            self.performance_monitor.record_response_time(response_time)
            self.performance_monitor.record_successful_interaction()
            self.performance_monitor.increment_message_count()

        # Add to conversation history
        if self.conversation_manager:
            self.conversation_manager.add_message("assistant", response)

        return response

    def chat_loop(self):
        """Run interactive chat loop."""
        print("\n" + "=" * 50)
        print("Chat Commands:")
        print("  • Type your message to chat")
        print("  • 'search:<query>' - Web search")
        print("  • 'feedback' - Rate last response")
        print("  • 'quit' or 'exit' - End session")
        print("=" * 50 + "\n")

        # Create session
        if self.conversation_manager:
            session_id = self.conversation_manager.create_session()
            self.performance_monitor.increment_session_count()
            print(f"Session started: {session_id[:8]}...\n")

        last_response = None
        last_user_input = None

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nEnding session...")
                    if self.feedback_collector and last_user_input and last_response:
                        print("Thanks for chatting!")
                    break

                # Handle feedback command
                if user_input.lower() == 'feedback' and self.feedback_collector:
                    print("\nRate last response (1-5): ", end="")
                    rating_input = input().strip()
                    try:
                        rating = int(rating_input)
                        if 1 <= rating <= 5:
                            self.feedback_collector.add_feedback(
                                feedback_type="rating",
                                message=last_user_input or "",
                                response=last_response or "",
                                rating=rating,
                            )
                            print("✓ Thanks for your feedback!")
                    except ValueError:
                        print("Invalid rating.")
                    continue

                # Handle search command
                if user_input.lower().startswith("search:"):
                    query = user_input[7:].strip()
                    print("🔍 Searching...")
                    result = self._mcp_search(query)
                    if result["success"]:
                        print(f"\n✅ Results for '{result['query']}':\n")
                        for i, r in enumerate(result["results"], 1):
                            print(f"  {i}. {r}")
                    else:
                        print(f"❌ Search failed: {result['error']}")
                    continue

                # Process and generate response
                processed = self.process_input(user_input)

                # Show intent detection (debug)
                if processed.get("intent") and processed["intent"]["confidence"] > 0.5:
                    intent = processed["intent"]["intent"]
                    print(f"  [Intent: {intent}]")

                response = self.generate_response(user_input, processed)

                print(f"AI: {response}\n")

                last_user_input = user_input
                last_response = response

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break

        # Show session stats
        if self.performance_monitor:
            stats = self.performance_monitor.get_session_stats()
            print(f"\nSession Stats: {stats['total_messages']} messages")

    def _mcp_search(self, query: str) -> Dict[str, Any]:
        """Simple web search using MCP tool."""
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(r['body'][:200])
                    if len(results) >= 5:
                        break

            if results:
                return {"success": True, "results": results, "query": query}
            return {"success": False, "error": "No results found"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Stack 2.9 Enhanced Chat")
    parser.add_argument("--model", "-m", type=str,
                        default="/Users/walidsobhi/stack-2-9-final-model",
                        help="Path to model")
    parser.add_argument("--no-bert", action="store_true",
                        help="Disable BERT embeddings")
    parser.add_argument("--no-rag", action="store_true",
                        help="Disable RAG")
    parser.add_argument("--no-empathy", action="store_true",
                        help="Disable emotional intelligence")

    args = parser.parse_args()

    # Build config from args
    config = EnhancementConfig()
    config.nlp.use_bert_embeddings = not args.no_bert
    config.knowledge_graph.rag_enabled = not args.no_rag
    config.emotional_intelligence.empathetic_responses = not args.no_empathy

    # Create enhanced instance
    stack = Stack2_9Enhanced(model_path=args.model, config=config)

    # Run chat
    stack.chat_loop()


if __name__ == "__main__":
    main()