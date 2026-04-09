#!/usr/bin/env python3
"""
Stack 2.9 - Pure Torch Loading
"""
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from pathlib import Path
import json

model_path = Path("/Users/walidsobhi/stack-2-9-final-model")

print("Loading tokenizer...")
from transformers import PreTrainedTokenizerFast
tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
tokenizer.pad_token = "<|endoftext|>"
tokenizer.eos_token = "<|endoftext|>"

print("Loading config...")
with open(model_path / "config.json") as f:
    config_dict = json.load(f)

# Try loading with AutoModelForCausalLM
print("Loading model with from_pretrained...")
from transformers import AutoModelForCausalLM, AutoTokenizer

# Use from_pretrained with local_files_only but let it handle everything
model = AutoModelForCausalLM.from_pretrained(
    str(model_path),
    torch_dtype=torch.float16,
    device_map="cpu",  # Load to CPU first
    local_files_only=True
)

tokenizer = AutoTokenizer.from_pretrained(
    str(model_path),
    local_files_only=True
)
tokenizer.pad_token = "<|endoftext|>"

if torch.cuda.is_available():
    model = model.to("cuda")

print("Ready!\n")

# Chat
while True:
    try:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        prompt = f"You are Stack 2.9.\n\nUser: {user_input}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors='pt')
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        outputs = model.generate(**inputs, max_new_tokens=80, temperature=0.4, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        break

print("Done!")