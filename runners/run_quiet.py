#!/usr/bin/env python3
"""
Stack 2.9 - Silent Loading (Fixed)
"""
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

import torch
from pathlib import Path
import json

model_path = Path("/Users/walidsobhi/stack-2-9-final-model")

print("Loading...")

# Load tokenizer directly
from transformers import PreTrainedTokenizerFast
tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
tokenizer.pad_token = "<|endoftext|>"
tokenizer.eos_token = "<|endoftext|>"

print("Tokenizer loaded")

# Load config
with open(model_path / "config.json") as f:
    config_dict = json.load(f)

# Create config directly
from transformers import PretrainedConfig
class LocalConfig(PretrainedConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

config = LocalConfig(**config_dict)

# Load weights
print("Loading weights...")
from safetensors.torch import load_file
state_dict = load_file(str(model_path / "model.safetensors"))

# Build model
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_config(config)
model.load_state_dict(state_dict, strict=False)
model = model.to(torch.float16)

if torch.cuda.is_available():
    model.to("cuda")

print("Model ready!\n")

# Chat
print("Stack 2.9 Ready!")
print("=" * 40)

while True:
    try:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        prompt = f"You are Stack 2.9.\n\nUser: {user_input}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors='pt')
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        outputs = model.generate(**inputs, max_new_tokens=100, temperature=0.4, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        print(f"AI: {response}")

    except KeyboardInterrupt:
        break

print("\nDone!")