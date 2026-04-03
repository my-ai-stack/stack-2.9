#!/usr/bin/env python3
"""
Stack 2.9 Model Quantization Script
Applies AWQ/GPTQ quantization to the trained model for efficient inference.
"""

import argparse
import os
import sys
import torch
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_args():
    parser = argparse.ArgumentParser(description="Quantize Stack 2.9 model")
    parser.add_argument(
        "--model-path",
        type=str,
        default="./output/stack-2.9-merged",
        help="Path to merged LoRA model"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="./output/stack-2.9-quantized",
        help="Output path for quantized model"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["awq", "gptq", "bnb"],
        default="bnb",
        help="Quantization method (awq, gptq, or bitsandbytes)"
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=4,
        help="Quantization bits (2, 4, or 8)"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark after quantization"
    )
    return parser.parse_args()


def get_model_size(path: str) -> float:
    """Calculate model size in GB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)


def benchmark_model(model, tokenizer, device="cuda"):
    """Benchmark model inference speed."""
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU benchmark")
        return None
    
    # Warm up
    prompt = "Write a hello world program in Python"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    with torch.no_grad():
        _ = model.generate(**inputs, max_new_tokens=20, do_sample=False)
    
    # Benchmark
    import time
    
    num_runs = 5
    times = []
    
    for _ in range(num_runs):
        torch.cuda.synchronize()
        start = time.perf_counter()
        
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=100, do_sample=False)
        
        torch.cuda.synchronize()
        times.append(time.perf_counter() - start)
    
    avg_time = sum(times) / len(times)
    tokens_generated = 100
    
    return {
        "avg_time": avg_time,
        "tokens_per_sec": tokens_generated / avg_time,
        "memory_allocated": torch.cuda.max_memory_allocated() / (1024 ** 3)
    }


def quantize_awq(args):
    """Apply AWQ quantization."""
    try:
        from awq import AWQ4BitConfig, prepare_model
        from transformers import AutoModelForCausalLM
        
        print(f"Loading model from {args.model_path}...")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        awq_config = AWQ4BitConfig(
            num_groups=32,
            min_coeff=0.01,
            max_coeff=1.0
        )
        
        print("Applying AWQ quantization...")
        quantized_model = prepare_model(model, awq_config)
        
        print(f"Saving to {args.output_path}...")
        os.makedirs(args.output_path, exist_ok=True)
        quantized_model.save_pretrained(args.output_path)
        
        return quantized_model
        
    except ImportError:
        print("AWQ not available, falling back to bitsandbytes")
        return quantize_bnb(args)


def quantize_gptq(args):
    """Apply GPTQ quantization."""
    try:
        from transformers import AutoModelForCausalLM
        from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
        
        print(f"Loading model from {args.model_path}...")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        print("Applying GPTQ quantization...")
        quantize_config = BaseQuantizeConfig(
            bits=args.bits,
            group_size=128,
            desc_act=False
        )
        
        # GPTQ quantization would need calibration data
        # For now, save as is with bitsandbytes fallback
        print("GPTQ requires calibration - using bitsandbytes instead")
        return quantize_bnb(args)
        
    except ImportError:
        print("GPTQ not available, falling back to bitsandbytes")
        return quantize_bnb(args)


def quantize_bnb(args):
    """Apply bitsandbytes quantization (default, most compatible)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    print(f"Loading model from {args.model_path}...")
    
    load_in_4bit = args.bits == 4
    load_in_8bit = args.bits == 8
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.float16,
        load_in_4bit=load_in_4bit,
        load_in_8bit=load_in_8bit,
        device_map="auto",
        trust_remote_code=True
    )
    
    print(f"Saving to {args.output_path}...")
    os.makedirs(args.output_path, exist_ok=True)
    model.save_pretrained(args.output_path)
    
    # Also save tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
        tokenizer.save_pretrained(args.output_path)
    except:
        print("Could not save tokenizer separately")
    
    return model


def main():
    args = parse_args()
    
    # Validate input
    if not os.path.exists(args.model_path):
        print(f"Error: Model path {args.model_path} does not exist")
        print("Please run training first or specify correct path")
        sys.exit(1)
    
    print("=" * 60)
    print("Stack 2.9 Model Quantization")
    print("=" * 60)
    print(f"Input model: {args.model_path}")
    print(f"Output path: {args.output_path}")
    print(f"Method: {args.method}")
    print(f"Bits: {args.bits}")
    print("=" * 60)
    
    # Get original size
    original_size = get_model_size(args.model_path)
    print(f"Original model size: {original_size:.2f} GB")
    
    # Quantize based on method
    if args.method == "awq":
        model = quantize_awq(args)
    elif args.method == "gptq":
        model = quantize_gptq(args)
    else:
        model = quantize_bnb(args)
    
    # Get quantized size
    quantized_size = get_model_size(args.output_path)
    compression_ratio = original_size / quantized_size if quantized_size > 0 else 0
    
    print("=" * 60)
    print("Quantization Complete!")
    print("=" * 60)
    print(f"Original size: {original_size:.2f} GB")
    print(f"Quantized size: {quantized_size:.2f} GB")
    print(f"Compression ratio: {compression_ratio:.2f}x")
    print(f"Output saved to: {args.output_path}")
    
    # Benchmark if requested
    if args.benchmark:
        print("\nRunning benchmark...")
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
            results = benchmark_model(model, tokenizer)
            
            if results:
                print(f"\nBenchmark Results:")
                print(f"  Average time: {results['avg_time']:.2f}s")
                print(f"  Tokens/sec: {results['tokens_per_sec']:.1f}")
                print(f"  GPU memory: {results['memory_allocated']:.2f} GB")
        except Exception as e:
            print(f"Benchmark failed: {e}")
    
    print("\n✓ Quantization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())