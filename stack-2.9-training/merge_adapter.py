#!/usr/bin/env python3
"""
Stack 2.9 Merge LoRA Adapter Script
Merges LoRA weights back into base model and exports to HuggingFace format.
Optionally quantizes to AWQ if requested.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load training configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "train_config.yaml"
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def merge_adapter(
    config_path: str = None,
    lora_path: str = None,
    output_path: str = None,
    use_awq: bool = False
) -> None:
    """
    Merge LoRA adapter into base model.
    
    Args:
        config_path: Path to config file
        lora_path: Path to LoRA weights
        output_path: Path for merged output
        use_awq: Whether to apply AWQ quantization
    """
    print("=" * 60)
    print("Stack 2.9 Merge LoRA Adapter")
    print("=" * 60)
    
    # Load configuration
    config = load_config(config_path)
    model_config = config["model"]
    output_config = config["output"]
    quant_config = config["quantization"]
    
    # Set paths
    model_name = model_config["name"]
    
    if lora_path is None:
        lora_path = output_config["lora_dir"]
    
    if output_path is None:
        if use_awq and quant_config.get("enabled", False):
            output_path = output_config["awq_dir"]
        else:
            output_path = output_config["merged_dir"]
    
    # Create output directory
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📋 Configuration:")
    print(f"   Base model: {model_name}")
    print(f"   LoRA path: {lora_path}")
    print(f"   Output path: {output_path}")
    print(f"   AWQ: {use_awq}")
    
    # Load base model
    print(f"\n🤖 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    print(f"   Base model loaded")
    
    # Load LoRA adapter
    print(f"\n📦 Loading LoRA adapter...")
    from peft import PeftModel
    
    lora_adapter = PeftModel.from_pretrained(
        base_model,
        lora_path
    )
    print(f"   LoRA adapter loaded")
    
    # Merge LoRA weights
    print(f"\n🔄 Merging LoRA weights...")
    merged_model = lora_adapter.merge_and_unload()
    print(f"   LoRA weights merged")
    
    # Save tokenizer
    print(f"\n💾 Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    tokenizer.save_pretrained(str(output_dir))
    
    # Quantize if requested
    if use_awq and quant_config.get("enabled", False):
        print(f"\n⚡ Applying AWQ quantization...")
        from awq import AWQ4BitConfig, prepare_model
        
        awq_conf = AWQ4BitConfig(
            num_groups=quant_config.get("group_size", 128),
            min_coeff=0.01,
            max_coeff=1.0
        )
        
        merged_model = prepare_model(merged_model, awq_conf)
        print(f"   AWQ quantization applied")
    
    # Save merged model
    print(f"\n💾 Saving merged model...")
    merged_model.save_pretrained(str(output_dir))
    
    print(f"\n✅ Merge completed!")
    print(f"   Merged model saved to: {output_dir}")
    
    # Print model size
    total_params = sum(p.numel() for p in merged_model.parameters())
    trainable_params = sum(p.numel() for p in merged_model.parameters() if p.requires_grad)
    
    print(f"   Total parameters: {total_params:,}")
    print(f"   Trainable parameters: {trainable_params:,}")
    
    return output_dir


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stack 2.9 Merge LoRA Adapter")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--lora", type=str, default=None, help="Path to LoRA weights")
    parser.add_argument("--output", type=str, default=None, help="Path for merged output")
    parser.add_argument("--awq", action="store_true", help="Apply AWQ quantization")
    args = parser.parse_args()
    
    try:
        merge_adapter(args.config, args.lora, args.output, args.awq)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)