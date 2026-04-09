#!/usr/bin/env python3
"""
Fuse LoRA adapters from multiple team members into a unified model.

This script demonstrates how to merge multiple LoRA adapters trained on different
codebases or by different team members, enabling collective intelligence while
preserving individual specialization.

Algorithm: Weighted averaging with similarity-based adaptive weights.
"""

import os
import json
import torch
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

def load_lora_adapter(adapter_path: str, device: str = "cpu") -> Dict[str, torch.Tensor]:
    """
    Load a LoRA adapter from a safetensors or pytorch bin file.
    
    Returns: Dict of parameter name -> tensor
    """
    adapter_path = Path(adapter_path)
    
    # Try safetensors first (faster, no pickle)
    safetensors_path = adapter_path / "adapter_model.safetensors"
    if safetensors_path.exists():
        from safetensors import safe_open
        tensors = {}
        with safe_open(safetensors_path, framework="pt", device=device) as f:
            for key in f.keys():
                tensors[key] = f.get_tensor(key)
        return tensors
    
    # Fall back to pytorch bin
    pytorch_path = adapter_path / "adapter_model.bin"
    if pytorch_path.exists():
        tensors = torch.load(pytorch_path, map_location=device, weights_only=True)
        return tensors
    
    raise FileNotFoundError(f"No adapter found at {adapter_path}")

def compute_adapter_metadata(adapter_path: str) -> Dict[str, Any]:
    """
    Load adapter metadata (training stats, performance, etc.) if available.
    """
    metadata_path = Path(adapter_path) / "adapter_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    # Default metadata
    return {
        "training_examples": 0,
        "validation_score": 0.0,
        "domains": [],
        "team_member": "unknown"
    }

def compute_similarity_matrix(
    adapters: List[Tuple[str, Dict[str, torch.Tensor]]],
    sample_keys: Optional[List[str]] = None
) -> np.ndarray:
    """
    Compute pairwise similarity between adapters based on weight distributions.
    
    Uses cosine similarity of normalized weight vectors.
    """
    n = len(adapters)
    similarity = np.zeros((n, n))
    
    # Get parameter names common to all adapters
    if sample_keys is None:
        common_keys = set(adapters[0][1].keys())
        for _, tensors in adapters[1:]:
            common_keys &= set(tensors.keys())
        sample_keys = list(common_keys)[:100]  # Sample up to 100 parameters
    
    # Flatten sampled parameters for each adapter
    vectors = []
    for _, tensors in adapters:
        vec_parts = []
        for key in sample_keys:
            if key in tensors:
                # Flatten and normalize
                t = tensors[key].float().flatten()
                norm = torch.norm(t).item()
                if norm > 1e-8:
                    t = t / norm
                vec_parts.append(t.numpy())
            else:
                # Missing parameter, use zeros
                shape = tensors[sample_keys[0]].shape if sample_keys[0] in tensors else (1,)
                vec_parts.append(np.zeros(shape).flatten())
        vectors.append(np.concatenate(vec_parts))
    
    # Compute cosine similarity
    for i in range(n):
        for j in range(n):
            if i == j:
                similarity[i, j] = 1.0
            else:
                v1, v2 = vectors[i], vectors[j]
                sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
                similarity[i, j] = sim
    
    return similarity

def compute_adaptive_weights(
    similarities: np.ndarray,
    metadata: List[Dict[str, Any]],
    base_config: Dict[str, float]
) -> np.ndarray:
    """
    Compute fusion weights using adaptive strategy:
    
    w_i = (performance_i * domain_overlap_i) / (sum(performance_j * domain_overlap_j) + epsilon)
    
    With similarity-based adjustments:
    - Higher weight adapters that are similar to each other get boosted
    - Diverse adapters get balanced contributions
    """
    n = len(metadata)
    weights = np.zeros(n)
    
    # Base weights from performance
    base_weights = np.array([
        meta.get("validation_score", 0.0) * 
        meta.get("training_examples", 1) / 1000.0  # Normalize by dataset size
        for meta in metadata
    ])
    
    # Domain overlap weights
    domain_weights = np.zeros(n)
    all_domains = defaultdict(int)
    for i, meta in enumerate(metadata):
        for domain in meta.get("domains", []):
            all_domains[domain] += 1
    
    for i, meta in enumerate(metadata):
        overlap = 0.0
        for domain in meta.get("domains", []):
            # Rare domains get higher weight
            overlap += 1.0 / all_domains[domain]
        domain_weights[i] = overlap if overlap > 0 else 1.0
    
    # Combine base weights with domain weights
    raw_weights = base_weights * domain_weights
    
    # Apply similarity-based smoothing
    # If two adapters are very similar, distribute weight more evenly
    similarity_threshold = base_config.get("similarity_threshold", 0.9)
    similarity_damping = base_config.get("similarity_damping", 0.3)
    
    for i in range(n):
        for j in range(i+1, n):
            if similarities[i, j] > similarity_threshold:
                # Too similar, dampen differences
                avg_weight = (raw_weights[i] + raw_weights[j]) / 2
                raw_weights[i] = raw_weights[i] * (1 - similarity_damping) + avg_weight * similarity_damping
                raw_weights[j] = raw_weights[j] * (1 - similarity_damping) + avg_weight * similarity_damping
    
    # Normalize
    total = np.sum(raw_weights)
    if total > 0:
        weights = raw_weights / total
    else:
        weights = np.ones(n) / n
    
    return weights

def fuse_adapters(
    adapter_paths: List[str],
    output_path: str,
    config: Optional[Dict] = None
) -> Tuple[Path, Dict]:
    """
    Fuse multiple LoRA adapters into a single adapter.
    
    Args:
        adapter_paths: List of paths to adapter directories
        output_path: Where to save the fused adapter
        config: Fusion configuration (weights, similarity thresholds, etc.)
    
    Returns:
        Path to fused adapter, fusion metadata
    """
    if config is None:
        config = {
            "fusion_method": "weighted_average",
            "similarity_threshold": 0.9,
            "similarity_damping": 0.3,
            "normalize_weights": True,
            "clip_diff": 2.0  # Clip weight differences to avoid extreme values
        }
    
    print(f"🔗 Fusing {len(adapter_paths)} adapters...")
    
    # Load all adapters
    adapters = []
    metadata_list = []
    
    for path in adapter_paths:
        print(f"   Loading: {Path(path).name}")
        try:
            tensors = load_lora_adapter(path)
            meta = compute_adapter_metadata(path)
            adapters.append((path, tensors))
            metadata_list.append(meta)
        except Exception as e:
            print(f"   ⚠️  Skipped {path}: {e}")
    
    if len(adapters) < 2:
        raise ValueError("Need at least 2 adapters to fuse")
    
    # Get common parameter keys
    common_keys = set(adapters[0][1].keys())
    for _, tensors in adapters[1:]:
        common_keys &= set(tensors.keys())
    
    print(f"   Common parameters: {len(common_keys)}")
    
    # Compute similarities
    print("   Computing adapter similarities...")
    # Sample parameters for similarity computation
    sample_keys = list(common_keys)[:min(100, len(common_keys))]
    similarities = compute_similarity_matrix(adapters, sample_keys)
    
    # Compute adaptive weights
    weights = compute_adaptive_weights(similarities, metadata_list, config)
    
    print("   Fusion weights:")
    for i, (path, _) in enumerate(adapters):
        member = metadata_list[i].get("team_member", f"adapter_{i}")
        print(f"      {member}: {weights[i]:.3f}")
    
    # Fuse weights
    print("   Fusing weights...")
    fused_tensors = {}
    
    for key in common_keys:
        # Start with zero tensor
        fused = None
        
        for idx, (_, tensors) in enumerate(adapters):
            weight = weights[idx]
            tensor = tensors[key].float()
            
            if fused is None:
                fused = tensor * weight
            else:
                fused += tensor * weight
        
        # Apply clipping if configured
        if config["clip_diff"] > 0:
            # Clip extreme values relative to first adapter
            reference = adapters[0][1][key].float()
            max_diff = torch.max(torch.abs(fused - reference)) * config["clip_diff"]
            # This is a simple heuristic - could be improved
            fused = torch.clamp(fused, 
                                reference - max_diff, 
                                reference + max_diff)
        
        fused_tensors[key] = fused.half()  # Convert back to half precision
    
    # Save fused adapter
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save tensors
    fused_file = output_path / "adapter_model.safetensors"
    try:
        from safetensors import save_file
        save_file(fused_tensors, str(fused_file))
    except ImportError:
        # Fallback to pytorch
        torch.save(fused_tensors, output_path / "adapter_model.bin")
    
    # Save metadata
    fusion_metadata = {
        "fusion_date": "2025-04-03",  # Would use datetime.now()
        "source_adapters": [
            {
                "path": path,
                "team_member": meta.get("team_member", "unknown"),
                "validation_score": meta.get("validation_score", 0.0),
                "domains": meta.get("domains", []),
                "weight": float(weights[i])
            }
            for i, (path, meta) in enumerate(zip([p for p, _ in adapters], metadata_list))
        ],
        "fusion_config": config,
        "similarity_matrix": similarities.tolist(),
        "total_parameters": len(common_keys)
    }
    
    with open(output_path / "fusion_metadata.json", 'w') as f:
        json.dump(fusion_metadata, f, indent=2)
    
    print(f"\n✅ Fused adapter saved to: {output_path}")
    print(f"   Parameters: {len(common_keys)}")
    print(f"   Used samples: {sum(m.get('training_examples', 0) for m in metadata_list)}")
    
    return output_path, fusion_metadata

def validate_fusion(
    fused_adapter_path: str,
    test_cases_path: Optional[str] = None,
    base_model: str = "Qwen/Qwen2.5-Coder-32B"
) -> Dict[str, float]:
    """
    Validate the fused adapter against test cases.
    
    Returns: Dictionary with validation metrics
    """
    print("🔍 Validating fused adapter...")
    
    # This would integrate with the evaluation framework
    # For now, return mock metrics
    metrics = {
        "score": 0.0,
        "test_cases": 0,
        "passed": 0
    }
    
    if test_cases_path:
        # Load and run test cases
        test_cases_path = Path(test_cases_path)
        if test_cases_path.exists():
            # Would implement actual validation
            pass
    
    print(f"   Validation complete (placeholder)")
    return metrics

def main():
    parser = argparse.ArgumentParser(
        description="Fuse LoRA adapters from multiple team members."
    )
    parser.add_argument(
        "--adapters",
        nargs='+',
        required=True,
        help="Paths to adapter directories (each with adapter_model.safetensors)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="fused-adapter",
        help="Output directory for fused adapter"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="JSON config file with fusion parameters"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation after fusion"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="Qwen/Qwen2.5-Coder-32B",
        help="Base model identifier"
    )
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Fuse adapters
    try:
        output_path, metadata = fuse_adapters(
            args.adapters,
            args.output,
            config or {}
        )
        
        # Validate if requested
        if args.validate:
            metrics = validate_fusion(str(output_path), base_model=args.base_model)
            print("\n📊 Validation Metrics:")
            for k, v in metrics.items():
                print(f"   {k}: {v}")
        
        # Print summary
        print("\n📈 Fusion Summary:")
        print(f"   Total adapters: {len(args.adapters)}")
        print(f"   Output: {output_path}")
        print(f"   Members:", ", ".join(
            m["team_member"] for m in metadata["source_adapters"]
        ))
        
    except Exception as e:
        print(f"❌ Fusion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
