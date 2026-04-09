#!/usr/bin/env python3
"""
Stack 2.9 - Convert & Load (No progress bar)
"""
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from pathlib import Path
import json
import sys

model_path = Path("/Users/walidsobhi/stack-2.9-final-model")
cache_path = Path("/Users/walidsobhi/stack-2.9/weights_cache.pt")

print("Loading...", flush=True)

# Load tokenizer
from transformers import PreTrainedTokenizerFast
tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
tokenizer.pad_token = "<|endoftext|>"
tokenizer.eos_token = "<|endoftext|>"

print("Tokenizer ready", flush=True)

# Check if cached conversion exists
if cache_path.exists():
    print("Loading cached weights...", flush=True)
    state_dict = torch.load(cache_path, map_location='cpu')
else:
    # Convert without progress bar
    print("Converting weights (one-time)...", flush=True)

    # Use lower-level loading
    import io
    from safetensors.torch import load_file

    # Read file into memory first
    with open(model_path / "model.safetensors", "rb") as f:
        data = f.read()

    # Write to temp and load
    temp_path = Path("/tmp/weights.pt")
    with open(temp_path, "wb") as f:
        f.write(data)

    # Load with torch (silent)
    state_dict = torch.load(temp_path, map_location='cpu')
    temp_path.unlink()

    # Cache for next time
    torch.save(state_dict, cache_path)

print("Weights ready", flush=True)

# Load config
with open(model_path / "config.json") as f:
    config_dict = json.load(f)

# Build model
from transformers import Qwen2ForCausalLM, Qwen2Config

config = Qwen2Config()
for k, v in config_dict.items():
    setattr(config, k, v)

print("Building model...", flush=True)
model = Qwen2ForCausalLM(config)
model.load_state_dict(state_dict, strict=False)
model = model.to(torch.float16)

if torch.cuda.is_available():
    model.to("cuda")

print("Ready!\n", flush=True)

# Chat
print("=" * 40)
print("Stack 2.9 Ready! (Type 'quit' to exit)")
print("=" * 40)

while True:
    try:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        prompt = f"You are Stack 2.9.\n\nUser: {user_input}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors='pt')
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        outputs = model.generate(**inputs, max_new_tokens=80, temperature=0.4, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        print(f"AI: {response}")

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")

print("\nDone!")