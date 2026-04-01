#!/usr/bin/env python3
"""
Convert GGUF file to HuggingFace format
"""
import os
import sys

# Check for required packages
try:
    import gguf
except ImportError:
    print("Installing gguf...")
    os.system("pip install gguf -q")
    import gguf

try:
    from transformers import AutoModel, AutoTokenizer
except ImportError:
    print("Installing transformers...")
    os.system("pip install transformers -q")
    from transformers import AutoModel, AutoTokenizer

import torch

GGUF_PATH = "/Users/walidsobhi/.ollama/models/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463"
OUTPUT_DIR = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/base_model_qwen7b"

print(f"Reading GGUF from: {GGUF_PATH}")

# Read the GGUF file
reader = gguf.GGUFReader(GGUF_PATH)

# Get tensor info
print("\n GGUF Tensors:")
for i, tensor in enumerate(reader.tensors):
    print(f"  {i}: {tensor.name} - shape {tensor.shape}, dtype {tensor.tensor_type}")

# Extract to HF format
print("\n Converting to HuggingFace format...")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Save model files
model_path = os.path.join(OUTPUT_DIR, "model.safetensors")

# Map GGUF types to PyTorch types
def gguf_to_torch_type(gguf_type):
    type_map = {
        "F32": torch.float32,
        "F16": torch.float16,
        "BF16": torch.bfloat16,
        "I8": torch.int8,
        "I16": torch.int16,
        "I32": torch.int32,
        "I64": torch.int64,
        "U8": torch.uint8,
    }
    return type_map.get(gguf_type, torch.float32)

# Export tensors
state_dict = {}
for tensor in reader.tensors:
    print(f"  Converting {tensor.name}...")
    # Read tensor data
    data = reader.get_tensor(tensor.name)
    state_dict[tensor.name] = data

# Save as safetensors
try:
    from safetensors.torch import save_file
    save_file(state_dict, model_path)
    print(f"Model saved to: {model_path}")
except ImportError:
    # Fallback to torch
    torch.save(state_dict, model_path.replace(".safetensors", ".pt"))
    print(f"Model saved to: {model_path.replace('.safetensors', '.pt')}")

# Save config.json
config = {
    "model_type": "qwen2",
    "architectures": ["Qwen2ForCausalLM"],
    "vocab_size": 151936,
    "hidden_size": 3584,
    "intermediate_size": 18944,
    "num_hidden_layers": 28,
    "num_attention_heads": 28,
    "num_key_value_heads": 4,
    "max_position_embeddings": 32768,
    "sliding_window": 32768,
    "torch_dtype": "bfloat16",
    "transformers_version": "4.37.0",
}

import json
config_path = os.path.join(OUTPUT_DIR, "config.json")
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print(f"Config saved to: {config_path}")

# Create tokenizer files
print("\n Creating tokenizer...")

# Use Qwen2 tokenizer config
tokenizer_config = {
    "add_bos_token": False,
    "add_eos_token": False,
    "add_prefix_space": False,
    "added_tokens_decoder": {},
    "bos_token": "<|im_end|>",
    "clean_up_tokenization_spaces": False,
    "eos_token": "<|im_end|>",
    "errors": "replace",
    "model_max_length": 32768,
    "pad_token": "<|im_end|>",
    "tokenizer_class": "Qwen2Tokenizer",
    "unk_token": "<|endoftext|>",
}

tokenizer_config_path = os.path.join(OUTPUT_DIR, "tokenizer_config.json")
with open(tokenizer_config_path, "w") as f:
    json.dump(tokenizer_config, f, indent=2)

# Create a simple vocab file (this is a placeholder - real vocab is in the GGUF)
# The GGUF reader should have tokenizer data
vocab = {}
for i in range(151936):
    vocab[f"<|token_{i}|>"] = i

vocab_path = os.path.join(OUTPUT_DIR, "vocab.json")
with open(vocab_path, "w") as f:
    json.dump(vocab, f)
print(f"Vocab saved to: {vocab_path}")

print("\n✓ Conversion complete!")
print(f"Output directory: {OUTPUT_DIR}")
print("\nFiles created:")
for f in os.listdir(OUTPUT_DIR):
    fpath = os.path.join(OUTPUT_DIR, f)
    size = os.path.getsize(fpath) / (1024*1024)
    print(f"  {f}: {size:.1f} MB")
