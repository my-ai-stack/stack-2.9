#!/usr/bin/env python3
"""
Stack 2.9 - Pure PyTorch Loading (No safetensors dependency)
"""

import sys
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import FeedbackCollector, PerformanceMonitor


class Stack2_9Local:
    """Stack 2.9 - Pure local loading"""

    def __init__(self, model_path: str = "/Users/walidsobhi/stack-2-9-final-model"):
        self.model_path = Path(model_path)
        self._model = None
        self._tokenizer = None

        print("Loading modules...")
        self.intent_detector = IntentDetector()
        self.entity_recognizer = EntityRecognizer()
        self.rag_engine = RAGEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.conversation_manager = ConversationStateManager()
        self.performance_monitor = PerformanceMonitor()
        print("✓ Done!\n")

    def load_model(self):
        """Load model using pure torch - completely local"""
        if self._model is not None:
            return

        print(f"Loading model from {self.model_path}...")

        import json

        # Load config
        with open(self.model_path / "config.json") as f:
            config = json.load(f)

        # Load tokenizer directly
        with open(self.model_path / "tokenizer.json") as f:
            tok_json = json.load(f)

        from transformers import PreTrainedTokenizerFast
        self._tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(self.model_path / "tokenizer.json"))

        with open(self.model_path / "tokenizer_config.json") as f:
            tok_config = json.load(f)

        self._tokenizer.pad_token = tok_config.get("pad_token", "<|endoftext|>")
        self._tokenizer.eos_token = tok_config.get("eos_token", "<|endoftext|>")

        # Load weights using PURE TORCH (no safetensors, no HF cache)
        print("Loading model.safetensors with torch.load...")

        # Use torch.load with mmap for memory efficiency
        with open(self.model_path / "model.safetensors", "rb") as f:
            # Read the safetensors file directly
            import struct

            # Parse safetensors header
            # Format: [8 bytes magic + 8 bytes header_size + header + weights]
            header_size_bytes = f.read(16)
            _, header_size = struct.unpack("<QQ", header_size_bytes)
            header_bytes = f.read(header_size)
            header = json.loads(header_bytes.decode("utf-8"))

            # Load each tensor
            state_dict = {}
            for name, info in header.items():
                offset = info["data_offsets"][0]
                shape = info["shape"]
                dtype = info["dtype"]

                # Convert safetensors dtype to torch dtype
                dtype_map = {
                    "F32": torch.float32,
                    "F16": torch.float16,
                    "BF16": torch.bfloat16,
                    "I32": torch.int32,
                    "I64": torch.int64,
                }
                torch_dtype = dtype_map.get(dtype, torch.float32)

                # Read tensor data
                numel = 1
                for s in shape:
                    numel *= s
                num_bytes = numel * torch_dtype.itemsize

                f.seek(offset)
                data_bytes = f.read(num_bytes)
                tensor = torch.frombuffer(data_bytes, dtype=torch_dtype).view(shape).clone()
                state_dict[name] = tensor

        print("Building model...")
        from transformers import AutoModelForCausalLM
        self._model = AutoModelForCausalLM.from_config(config)
        self._model.load_state_dict(state_dict, strict=False)
        self._model = self._model.to(torch.float16)

        if torch.cuda.is_available():
            self._model.to("cuda")

        print("✓ Model loaded!\n")

    def chat(self):
        print("=" * 50)
        print("Stack 2.9 - Pure Local")
        print("=" * 50 + "\n")

        self.conversation_manager.create_session()

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                self.load_model()

                prompt = f"You are Stack 2.9.\nUser: {user_input}\nAssistant:"
                inputs = self._tokenizer(prompt, return_tensors='pt')
                if torch.cuda.is_available():
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}

                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=80,
                    temperature=0.4,
                    pad_token_id=self._tokenizer.eos_token_id
                )

                response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
                if "Assistant:" in response:
                    response = response.split("Assistant:")[-1].strip()

                print(f"AI: {response}\n")
                self.performance_monitor.increment_message_count()

            except KeyboardInterrupt:
                break

        print(f"Messages: {self.performance_monitor.get_session_stats()['total_messages']}")


if __name__ == "__main__":
    Stack2_9Local().chat()