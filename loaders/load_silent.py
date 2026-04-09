#!/usr/bin/env python3
"""
Stack 2.9 - Silent Loading (No Progress Bar)
"""
import os
import sys

# Disable progress bars
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'

import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhancements.nlp import IntentDetector
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import PerformanceMonitor


def load_model_silently():
    """Load model completely silently"""
    model_path = Path("/Users/walidsobhi/stack-2-9-final-model")
    import json

    # Load tokenizer
    from transformers import PreTrainedTokenizerFast
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
    tokenizer.pad_token = "<|endoftext|>"
    tokenizer.eos_token = "<|endoftext|>"

    # Load config
    with open(model_path / "config.json") as f:
        config_dict = json.load(f)

    # Create model config
    from transformers import AutoConfig
    config = AutoConfig.from_json_file(str(model_path / "config.json"))

    # Load weights silently using torch directly
    print("Loading weights...", flush=True)

    # Use torch.load_file which is silent
    with open(model_path / "model.safetensors", 'rb') as f:
        import io
        # Read entire file into memory first (silently)
        buffer = io.BytesIO(f.read())

    # Load using safetensors (no progress bar)
    from safetensors.torch import load_file
    state_dict = load_file(str(model_path / "model.safetensors"))

    # Build model
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_config(config)
    model.load_state_dict(state_dict, strict=False)
    model = model.to(torch.float16)

    if torch.cuda.is_available():
        model.to("cuda")

    print("Done loading!\n", flush=True)
    return model, tokenizer


def main():
    print("Stack 2.9 - Silent Mode")
    print("=" * 40 + "\n")

    # Init modules
    intent_detector = IntentDetector()
    rag_engine = RAGEngine()
    sentiment_analyzer = SentimentAnalyzer()
    conv_manager = ConversationStateManager()
    perf_monitor = PerformanceMonitor()

    rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant")

    conv_manager.create_session()
    perf_monitor.increment_session_count()

    # Load model once
    model, tokenizer = load_model_silently()

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            # Generate
            prompt = f"You are Stack 2.9, expert coder.\n\nUser: {user_input}\nAssistant:"
            inputs = tokenizer(prompt, return_tensors='pt')
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            outputs = model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.4,
                pad_token_id=tokenizer.eos_token_id
            )

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()

            print(f"AI: {response}\n")
            perf_monitor.increment_message_count()

        except KeyboardInterrupt:
            break

    print(f"Session complete: {perf_monitor.get_session_stats()['total_messages']} messages")


if __name__ == "__main__":
    main()