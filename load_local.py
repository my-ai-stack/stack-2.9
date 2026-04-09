#!/usr/bin/env python3
"""
Stack 2.9 - 100% Local Loading (No HuggingFace Download)
"""

import sys
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import enhancements
from enhancements import get_config
from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import FeedbackCollector, PerformanceMonitor


class Stack2_9Local:
    """Stack 2.9 with 100% local file loading"""

    def __init__(self, model_path: str = "/Users/walidsobhi/stack-2-9-final-model"):
        self.model_path = Path(model_path)
        self._model = None
        self._tokenizer = None

        # Init enhancement modules
        print("Loading enhancement modules...")
        self.intent_detector = IntentDetector()
        self.entity_recognizer = EntityRecognizer()
        self.rag_engine = RAGEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.conversation_manager = ConversationStateManager()
        self.feedback_collector = FeedbackCollector()
        self.performance_monitor = PerformanceMonitor()

        # Seed RAG
        self.rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant")
        print("✓ Modules loaded!\n")

    def load_model(self):
        """Load model 100% locally - zero HuggingFace access"""
        if self._model is not None:
            return

        print(f"Loading from {self.model_path} (100% local)...")

        # Import only what's needed
        from transformers import PreTrainedModel
        import json

        # Load config.json directly (not via transformers)
        with open(self.model_path / "config.json") as f:
            config_dict = json.load(f)

        # Load tokenizer files directly
        with open(self.model_path / "tokenizer_config.json") as f:
            tok_config = json.load(f)

        # Create tokenizer from tokenizer.json
        from transformers import PreTrainedTokenizerFast
        with open(self.model_path / "tokenizer.json") as f:
            tok_json = json.load(f)

        self._tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(self.model_path / "tokenizer.json"))
        self._tokenizer.pad_token = tok_config.get("pad_token", "<|endoftext|>")
        self._tokenizer.eos_token = tok_config.get("eos_token", "<|endoftext|>")
        self._tokenizer.bos_token = tok_config.get("bos_token", "<|endoftext|>")

        # Load model class directly based on architecture
        model_type = config_dict.get("model_type", "qwen2")

        # Load weights directly with safetensors (NO HUGGINGFACE CACHE)
        print("Loading model.safetensors directly...")
        from safetensors.torch import load_file
        state_dict = load_file(str(self.model_path / "model.safetensors"))

        # Build model from config
        print("Building model...")
        from transformers import PretrainedConfig

        class Qwen2Config(PretrainedConfig):
            model_type = "qwen2"

        config = Qwen2Config(**config_dict)

        # Try to use the actual model class
        try:
            from transformers import Qwen2ForCausalLM
            self._model = Qwen2ForCausalLM.from_config(config)
        except:
            # Fallback: create base model
            from transformers import AutoModelForCausalLM
            self._model = AutoModelForCausalLM.from_config(config)

        # Load weights
        self._model.load_state_dict(state_dict, strict=False)
        self._model = self._model.to(torch.float16)

        if torch.cuda.is_available():
            self._model.to("cuda")
            print("✓ Model loaded to GPU!\n")
        else:
            print("✓ Model loaded to CPU!\n")

    def chat(self):
        print("=" * 50)
        print("Stack 2.9 - 100% Local")
        print("=" * 50)
        print("Commands: quit, exit\n")

        self.conversation_manager.create_session()

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Quick processing
                intent = self.intent_detector.detect_intent(user_input)
                sentiment = self.sentiment_analyzer.analyze_sentiment(user_input)

                # Load model and generate
                self.load_model()

                prompt = f"You are Stack 2.9, an expert AI coding assistant.\n\nUser: {user_input}\nAssistant:"
                inputs = self._tokenizer(prompt, return_tensors='pt')
                if torch.cuda.is_available():
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}

                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.4,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id
                )

                response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
                if "Assistant:" in response:
                    response = response.split("Assistant:")[-1].strip()

                print(f"AI: {response}\n")

                self.performance_monitor.increment_message_count()

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}\n")

        stats = self.performance_monitor.get_session_stats()
        print(f"\nDone! {stats['total_messages']} messages")


if __name__ == "__main__":
    chat = Stack2_9Local()
    chat.chat()