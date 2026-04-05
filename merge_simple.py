#!/usr/bin/env python3
"""
Simple LoRA merge script.
Usage: python merge_simple.py --base-model Qwen/Qwen2.5-Coder-7B --adapter-path adapters/lora --output-path merged_model
"""

import argparse
import os
from pathlib import Path

import torch
# Disable LoFTQ to avoid bitsandbytes import
os.environ['PEFT_DISABLE_LOFTQ'] = '1'
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=str, required=True, help="Base model name or path")
    parser.add_argument("--adapter-path", type=str, required=True, help="LoRA adapter directory")
    parser.add_argument("--output-path", type=str, required=True, help="Output directory for merged model")
    parser.add_argument("--use-safetensors", action="store_true", help="Use safetensors format")
    args = parser.parse_args()

    print("="*60)
    print("Merging LoRA Adapter")
    print("="*60)
    print(f"Base model: {args.base_model}")
    print(f"Adapter: {args.adapter_path}")
    print(f"Output: {args.output_path}")

    # Load base model
    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)

    # Load and merge adapter
    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, args.adapter_path)

    print("Merging weights...")
    model = model.merge_and_unload()

    # Save
    os.makedirs(args.output_path, exist_ok=True)
    print(f"Saving to {args.output_path}...")
    model.save_pretrained(args.output_path, safe_serialization=args.use_safetensors)
    tokenizer.save_pretrained(args.output_path)

    print("="*60)
    print("✅ Merge complete!")
    print("="*60)
    files = list(Path(args.output_path).glob("*"))
    print(f"Files saved ({len(files)}):")
    for f in files:
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
