#!/usr/bin/env python3
"""
Stack 2.9 - Simple Direct Load
"""
import os
# Kill ALL huggingface networking and progress
os.environ['HF_HUB_DISABLE_HTTP'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

model_path = Path("/Users/walidsobhi/stack-2-9-final-model")

print("Loading...")

# Load tokenizer
import io
from tokenizers import Tokenizer
tokenizer = Tokenizer.from_file(str(model_path / "tokenizer.json"))

# Need a PretrainedTokenizer for generation
from transformers import PreTrainedTokenizerFast
fast_tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
fast_tokenizer.pad_token = "<|endoftext|>"
fast_tokenizer.eos_token = "<|endoftext|>"

print("Tokenizer ready")

# Load config
with open(model_path / "config.json") as f:
    cfg = json.load(f)

# Load weights using torch directly (no safetensors lib needed for loading)
print("Loading safetensors...")
import struct

# Read safetensors header
def load_safetensors_torch(path):
    """Load safetensors file using torch only"""
    with open(path, 'rb') as f:
        # Read header size
        header_size_bytes = f.read(8)
        header_size = struct.unpack('<Q', header_size_bytes)[0]

        # Read header
        header_bytes = f.read(header_size)
        import msgpack
        header = msgpack.unpackb(header_bytes, raw=False)

        # Load each tensor
        state_dict = {}
        for name, info in header.items():
            offset = info['dataoffsets'][0]
            n_bytes = info['dataoffsets'][1] - offset
            dtype = info['dtype']
            shape = info['shape']

            # Seek to data
            f.seek(offset)
            data = f.read(n_bytes)

            # Convert dtype string to torch dtype
            dtype_map = {
                'F32': torch.float32,
                'F16': torch.float16,
                'BF16': torch.bfloat16,
                'I32': torch.int32,
                'I16': torch.int16,
                'I8': torch.int8,
                'U8': torch.uint8,
            }
            torch_dtype = dtype_map.get(dtype, torch.float32)

            # Unpack
            tensor = torch.from_numpy(np.frombuffer(data, dtype=torch_dtype)).reshape(shape)
            state_dict[name] = tensor

    return state_dict

import numpy as np
state_dict = load_safetensors_torch(model_path / "model.safetensors")

print("Building model...")

# Create model
from transformers import AutoConfig, AutoModelForCausalLM
config = AutoConfig.from_dict(cfg)

model = AutoModelForCausalLM.from_config(config)
model.load_state_dict(state_dict, strict=False)
model = model.to(torch.float16)

print("Done! Ready to chat.\n")

# Chat loop
while True:
    try:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        prompt = f"You are Stack 2.9.\n\nUser: {user_input}\nAssistant:"
        inputs = fast_tokenizer(prompt, return_tensors='pt')

        outputs = model.generate(**inputs, max_new_tokens=80, temperature=0.4, pad_token_id=fast_tokenizer.eos_token_id)
        response = fast_tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        break

print("Done!")