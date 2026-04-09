#!/usr/bin/env python3
"""
Quick fix - loads model directly without HuggingFace cache
Run this instead of enhanced_chat.py
"""

import sys
import torch
from pathlib import Path
from safetensors.torch import load_file as load_safetensors
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import enhancements
from enhancements import get_config, EnhancementConfig
from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import KnowledgeGraph, RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer, EmpathyEngine
from enhancements.collaboration import ConversationStateManager, MCPIntegration
from enhancements.learning import FeedbackCollector, PerformanceMonitor


class Stack2_9Enhanced:
    """Enhanced Stack 2.9 - Direct file loading (no download)"""

    def __init__(self, model_path: str = "/Users/walidsobhi/stack-2-9-final-model"):
        self.model_path = model_path
        self._model = None
        self._tokenizer = None
        self._init_modules()

    def _init_modules(self):
        print("Loading enhancement modules...")
        config = get_config()

        self.intent_detector = IntentDetector()
        self.entity_recognizer = EntityRecognizer()
        self.knowledge_graph = KnowledgeGraph()
        self.rag_engine = RAGEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.empathy_engine = EmpathyEngine()
        self.conversation_manager = ConversationStateManager()
        self.mcp = MCPIntegration()
        self.feedback_collector = FeedbackCollector()
        self.performance_monitor = PerformanceMonitor()

        # Seed RAG
        self.rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant")
        self.rag_engine.add_document("commands", "Commands: search:<query>, quit, feedback")

        print("✓ All modules loaded!\n")

    def load_model(self):
        """Load model directly from local files - NO DOWNLOAD"""
        if self._model is None:
            print(f"\nLoading model from {self.model_path} (direct load - no download)...")

            model_path = Path(self.model_path)

            # Load config
            config = AutoConfig.from_pretrained(model_path)

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)

            # Load weights directly (bypasses HuggingFace cache entirely)
            print("Loading model.safetensors directly...")
            weights = load_safetensors(str(model_path / "model.safetensors"))

            # Create model and load weights
            self._model = AutoModelForCausalLM.from_config(config)
            self._model.load_state_dict(weights)
            self._model = self._model.to(torch.float16)

            if torch.cuda.is_available():
                self._model.to("cuda")
                print("✓ Model loaded to GPU!\n")
            else:
                print("✓ Model loaded to CPU!\n")

    def chat(self):
        print("=" * 50)
        print("Stack 2.9 Enhanced (Direct Load)")
        print("=" * 50)
        print("\nCommands: search:<query>, feedback, quit\n")

        self.conversation_manager.create_session()
        self.performance_monitor.increment_session_count()

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Process input
                intent = self.intent_detector.detect_intent(user_input)
                sentiment = self.sentiment_analyzer.analyze_sentiment(user_input)
                rag_context = self.rag_engine.retrieve_as_context(user_input, 300)

                # Generate response
                self.load_model()

                system = "You are Stack 2.9, an expert AI coding assistant."
                if rag_context:
                    system += f"\nContext: {rag_context}"
                if sentiment['sentiment'] == 'negative':
                    system += "\nBe empathetic."

                full_prompt = f"{system}\n\nUser: {user_input}\nAssistant:"
                inputs = self._tokenizer(full_prompt, return_tensors='pt')
                if torch.cuda.is_available():
                    inputs = inputs.to("cuda")

                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.4,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id
                )

                response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
                if "Assistant:" in response:
                    response = response.split("Assistant:")[-1].strip()

                print(f"AI: {response}\n")

                self.performance_monitor.increment_message_count()
                self.conversation_manager.add_message("user", user_input)
                self.conversation_manager.add_message("assistant", response)

            except KeyboardInterrupt:
                break

        print(f"\nSession complete. Messages: {self.performance_monitor.get_session_stats()['total_messages']}")


if __name__ == "__main__":
    chat = Stack2_9Enhanced()
    chat.chat()