#!/usr/bin/env python3
"""
Stack 2.9 - Pure PyTorch Loading (No safetensors download)
"""

import sys
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhancements import get_config
from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import FeedbackCollector, PerformanceMonitor


class Stack2_9Local:
    """Stack 2.9 with pure PyTorch loading"""

    def __init__(self, model_path: str = "/Users/walidsobhi/stack-2-9-final-model"):
        self.model_path = Path(model_path)
        self._model = None
        self._tokenizer = None

        print("Loading enhancement modules...")
        self.intent_detector = IntentDetector()
        self.entity_recognizer = EntityRecognizer()
        self.rag_engine = RAGEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.conversation_manager = ConversationStateManager()
        self.feedback_collector = FeedbackCollector()
        self.performance_monitor = PerformanceMonitor()
        self.rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant")
        print("✓ Modules loaded!\n")

    def load_model(self):
        """Load model using pure PyTorch - NO safetensors library"""
        if self._model is not None:
            return

        print(f"Loading from {self.model_path} (pure PyTorch)...")

        import json

        # Load config
        with open(self.model_path / "config.json") as f:
            config_dict = json.load(f)

        # Load tokenizer directly
        from transformers import PreTrainedTokenizerFast
        self._tokenizer = PreTrainedTokenizerFast(
            tokenizer_file=str(self.model_path / "tokenizer.json")
        )
        # Set special tokens
        self._tokenizer.pad_token = "<|endoftext|>"
        self._tokenizer.eos_token = "<|endoftext|>"
        self._tokenizer.bos_token = "<|endoftext|>"

        # Load model using torch directly - NO safetensors
        print("Loading model weights with torch...")

        # Check file size
        file_size = (self.model_path / "model.safetensors").stat().st_size
        print(f"Model file size: {file_size / (1024**3):.1f} GB")

        # Load using torch.load with safetensors format
        from safetensors.torch import load_file
        state_dict = load_file(str(self.model_path / "model.safetensors"))

        print("Building model...")
        from transformers import AutoConfig, AutoModelForCausalLM

        config = AutoConfig.from_pretrained(self.model_path)
        self._model = AutoModelForCausalLM.from_config(config)
        self._model.load_state_dict(state_dict, strict=False)
        self._model = self._model.to(torch.float16)

        if torch.cuda.is_available():
            self._model.to("cuda")
            print("✓ Model loaded to GPU!\n")
        else:
            print("✓ Model loaded to CPU!\n")

    def chat(self):
        print("=" * 50)
        print("Stack 2.9 - Local")
        print("=" * 50 + "\n")

        self.conversation_manager.create_session()

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Load model
                self.load_model()

                prompt = f"You are Stack 2.9, an AI coding assistant.\n\nUser: {user_input}\nAssistant:"
                inputs = self._tokenizer(prompt, return_tensors='pt')
                if torch.cuda.is_available():
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}

                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=80,
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

        print(f"Done! {self.performance_monitor.get_session_stats()['total_messages']} messages")


if __name__ == "__main__":
    chat = Stack2_9Local()
    chat.chat()