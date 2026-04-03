#!/usr/bin/env python3
"""
Merge Multiple LoRA Adapters

Combines multiple LoRA adapters using weighted averaging based on success rates.
The merged adapter can be used to combine patterns learned by different users
or from different sources.

Usage:
    python merge_lora_adapters.py \
        --adapters adapter1.safetensors adapter2.safetensors \
        --weights 0.6 0.4 \
        --output merged.safetensors

    # Or with success rates (auto-computes weights proportional to success)
    python merge_lora_adapters.py \
        --adapters adapter1.safetensors adapter2.safetensors \
        --success-rates 0.85 0.65 \
        --output merged.safetensors
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Try to import required libraries
try:
    import torch
    import torch.nn as nn
    from safetensors.torch import load_file, save_file
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


def load_adapter(path: str) -> dict:
    """Load a LoRA adapter from a safetensors file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Adapter not found: {path}")
    
    return load_file(path)


def compute_weights_from_success_rates(success_rates: list[float]) -> list[float]:
    """Compute normalized weights proportional to success rates."""
    total = sum(success_rates)
    if total == 0:
        # Equal weights if all success rates are 0
        return [1.0 / len(success_rates)] * len(success_rates)
    return [rate / total for rate in success_rates]


def merge_adapters_weighted(
    adapters: list[dict],
    weights: list[float],
    output_path: str
) -> dict:
    """
    Merge multiple LoRA adapters using weighted averaging.
    
    Algorithm: merged_weight = Σ(adapter_i.weight * adapter_i.success_rate) / Σ(success_rate)
    
    For simplicity, we use the provided weights directly.
    """
    if len(adapters) != len(weights):
        raise ValueError("Number of adapters must match number of weights")
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Sum of weights cannot be zero")
    normalized_weights = [w / total_weight for w in weights]
    
    print(f"Merging {len(adapters)} adapters with weights: {normalized_weights}")
    
    # Get all keys from the first adapter
    sample_adapter = adapters[0]
    all_keys = set(sample_adapter.keys())
    
    # Verify all adapters have the same keys
    for i, adapter in enumerate(adapters[1:], 1):
        adapter_keys = set(adapter.keys())
        if adapter_keys != all_keys:
            print(f"Warning: Adapter {i} has different keys. Taking union.", file=sys.stderr)
            all_keys = all_keys.union(adapter_keys)
    
    # Merge each tensor
    merged = {}
    for key in all_keys:
        # Collect tensors from all adapters
        tensors = []
        valid_weights = []
        
        for i, (adapter, weight) in enumerate(zip(adapters, normalized_weights)):
            if key in adapter:
                tensors.append(adapter[key])
                valid_weights.append(weight)
        
        if not tensors:
            continue
        
        # Normalize weights for available tensors
        total_valid = sum(valid_weights)
        if total_valid == 0:
            continue
        norm_weights = [w / total_valid for w in valid_weights]
        
        # Weighted average
        merged[key] = sum(t * w for t, w in zip(tensors, norm_weights))
    
    # Save merged adapter
    save_file(merged, output_path)
    print(f"Merged adapter saved to: {output_path}")
    
    return merged


def compute_adapter_stats(adapter: dict) -> dict:
    """Compute statistics about an adapter for debugging."""
    stats = {
        "num_tensors": len(adapter),
        "total_params": 0,
        "dtype_counts": {},
        "shape_counts": {}
    }
    
    for key, tensor in adapter.items():
        num_params = tensor.numel()
        stats["total_params"] += num_params
        
        dtype = str(tensor.dtype)
        stats["dtype_counts"][dtype] = stats["dtype_counts"].get(dtype, 0) + 1
        
        shape = tuple(tensor.shape)
        shape_key = str(shape)
        stats["shape_counts"][shape_key] = stats["shape_counts"].get(shape_key, 0) + 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple LoRA adapters using weighted averaging"
    )
    parser.add_argument(
        "--adapters",
        type=str,
        nargs="+",
        required=True,
        help="Paths to LoRA adapter safetensors files"
    )
    parser.add_argument(
        "--weights",
        type=float,
        nargs="+",
        default=None,
        help="Manual weights for each adapter (must sum to 1 or will be normalized)"
    )
    parser.add_argument(
        "--success-rates",
        type=float,
        nargs="+",
        default=None,
        help="Success rates for each adapter (weights computed proportionally)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for merged adapter"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print adapter statistics"
    )
    
    args = parser.parse_args()
    
    if not HAS_LIBS:
        print("Error: Required libraries not found.", file=sys.stderr)
        print("Install with: pip install torch safetensors", file=sys.stderr)
        sys.exit(1)
    
    # Validate inputs
    if args.weights and args.success_rates:
        print("Error: Cannot specify both --weights and --success-rates", file=sys.stderr)
        sys.exit(1)
    
    if args.weights:
        if len(args.adapters) != len(args.weights):
            print("Error: Number of --adapters must match number of --weights", file=sys.stderr)
            sys.exit(1)
        weights = args.weights
    elif args.success_rates:
        if len(args.adapters) != len(args.success_rates):
            print("Error: Number of --adapters must match number of --success-rates", file=sys.stderr)
            sys.exit(1)
        weights = compute_weights_from_success_rates(args.success_rates)
        print(f"Computed weights from success rates: {weights}")
    else:
        # Equal weights
        weights = [1.0 / len(args.adapters)] * len(args.adapters)
    
    # Load adapters
    print(f"Loading {len(args.adapters)} adapters...")
    adapters = []
    for i, path in enumerate(args.adapters):
        print(f"  Loading {i+1}: {path}")
        adapter = load_adapter(path)
        adapters.append(adapter)
        
        if args.stats:
            stats = compute_adapter_stats(adapter)
            print(f"    Stats: {stats['num_tensors']} tensors, {stats['total_params']:,} params")
    
    # Merge
    merge_adapters_weighted(adapters, weights, args.output)
    
    # Print merge info
    print(f"\nMerge complete!")
    print(f"  Output: {args.output}")
    print(f"  Adapters merged: {len(args.adapters)}")
    
    # Save merge metadata
    metadata_path = args.output + ".meta.json"
    metadata = {
        "adapters": args.adapters,
        "weights": weights,
        "num_adapters": len(args.adapters)
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
