#!/usr/bin/env python3
"""
compare_models.py — Compare different Stack 2.9 model versions.

Reads from models/registry.json and produces a side-by-side comparison
of model properties and performance metrics.

Usage:
    python scripts/compare_models.py
    python scripts/compare_models.py --models stack-2.9-1.5B stack-2.9-7B
    python scripts/compare_models.py --metrics hellaswag mmlu humaneval
    python scripts/compare_models.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


REGISTRY_PATH = Path(__file__).parent.parent / "models" / "registry.json"

ALL_METRICS = ["hellaswag", "arc_challenge", "mmlu", "humaneval", "loss"]


def load_registry(registry_path: Path = REGISTRY_PATH) -> dict:
    """Load the model registry JSON."""
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}", file=sys.stderr)
        sys.exit(1)
    with open(registry_path) as f:
        return json.load(f)


def format_params(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.0f}M"
    return str(n)


def compare_params(a: int, b: int) -> str:
    """Compare two parameter counts."""
    ratio = b / a
    if ratio > 1:
        return f"  {ratio:.1f}x larger ({format_params(b)} vs {format_params(a)})"
    else:
        return f"  {1/ratio:.1f}x smaller ({format_params(b)} vs {format_params(a)})"


def build_row(version: str, key: str, value) -> str:
    """Build a comparison table row."""
    if value is None:
        val_str = "—"
    elif isinstance(value, float):
        val_str = f"{value:.4f}"
    elif isinstance(value, int):
        val_str = f"{value:,}"
    else:
        val_str = str(value)
    return f"  {version:<22} {key:<30} {val_str}"


def print_comparison(models: list, metrics: list, verbose: bool = False):
    """Print a side-by-side comparison table."""
    # Header
    versions = [m["version"] for m in models]
    max_ver_len = max(len(v) for v in versions)

    print(f"\n{'='*72}")
    print(f"  Model Comparison — Stack 2.9")
    print(f"{'='*72}")

    # Non-metric fields
    fields = [
        ("Base Model", "base_model"),
        ("Parameters", "parameters"),
        ("Quantization", "quantization"),
        ("Precision", "precision"),
        ("Context Length", "context_length"),
        ("Vocabulary Size", "vocabulary_size"),
        ("Dataset", "dataset"),
        ("LoRA Rank", ("lora", "rank")),
        ("LoRA Alpha", ("lora", "alpha")),
        ("LoRA Dropout", ("lora", "dropout")),
        ("Status", "status"),
        ("Created", "created_at"),
        ("Use Case", "use_case"),
    ]

    print(f"\n  {'Model':<{max_ver_len}}  {'Field':<30}  {'Value'}")
    print(f"  {'-'*max_ver_len}  {'-'*30}  {'-'*20}")

    for label, key in fields:
        row_values = []
        for m in models:
            if isinstance(key, tuple):
                nested = m
                for k in key:
                    nested = nested.get(k, {}) if isinstance(nested, dict) else {}
                row_values.append(nested if nested else None)
            else:
                val = m.get(key)
                # Format parameters as human-readable
                if key == "parameters" and val:
                    val = f"{format_params(val)} ({val:,})"
                row_values.append(val)
        unique = set(str(v) for v in row_values)
        if len(unique) == 1 and row_values[0] is None:
            continue
        print(f"\n  {label}:")
        for i, (ver, val) in enumerate(zip(versions, row_values)):
            if val is None:
                val_str = "—"
            elif isinstance(val, float):
                val_str = f"{val:.4f}"
            elif isinstance(val, int):
                val_str = f"{val:,}"
            else:
                val_str = str(val)
            marker = " →" if i > 0 and row_values[i] != row_values[0] else "  "
            print(f"  {marker} {ver:<{max_ver_len}}  {val_str}")

    # Performance metrics comparison
    has_any_metrics = any(
        any(m.get("performance", {}).get(metric) is not None for m in models)
        for metric in metrics
    )
    if has_any_metrics:
        print(f"\n\n  Performance Benchmarks")
        print(f"  {'-'*max_ver_len}  {'-'*30}  {'-'*10}")

        for metric in metrics:
            metric_name = metric.replace("_", " ").title()
            values = [m.get("performance", {}).get(metric) for m in models]
            if all(v is None for v in values):
                continue
            print(f"\n  {metric_name}:")
            for i, (ver, val) in enumerate(zip(versions, values)):
                if val is None:
                    val_str = "N/A"
                else:
                    val_str = f"{val:.4f}"
                marker = " →" if i > 0 else "  "
                print(f"  {marker} {ver:<{max_ver_len}}  {val_str}")

    # Parameter size comparison (pairwise)
    if len(models) >= 2:
        print(f"\n\n  Parameter Size Comparison:")
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                a, b = models[i], models[j]
                pa = a.get("parameters", 0)
                pb = b.get("parameters", 0)
                if pa and pb:
                    ratio = pb / pa
                    direction = "larger" if ratio > 1 else "smaller"
                    print(f"  {b['version']} is {ratio:.2f}x {direction} than {a['version']}")

    print(f"\n{'='*72}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compare Stack 2.9 model versions side by side."
    )
    parser.add_argument(
        "--models", "-m",
        nargs="+",
        metavar="VERSION",
        help="Model versions to compare (e.g., stack-2.9-1.5B stack-2.9-7B). "
             "If omitted, compares all available models."
    )
    parser.add_argument(
        "--metrics", "-M",
        nargs="+",
        choices=ALL_METRICS,
        default=ALL_METRICS,
        help=f"Benchmark metrics to include (default: all). Choices: {ALL_METRICS}"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output."
    )
    parser.add_argument(
        "--registry",
        default=REGISTRY_PATH,
        metavar="PATH",
        help=f"Path to registry.json (default: {REGISTRY_PATH})."
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    registry = load_registry(registry_path)
    models = registry.get("models", [])

    if args.models:
        selected = []
        for v in args.models:
            found = next((m for m in models if m["version"] == v), None)
            if found:
                selected.append(found)
            else:
                print(f"WARNING: Model '{v}' not found in registry. Skipping.", file=sys.stderr)
                available = ", ".join(m["version"] for m in models)
                print(f"  Available: {available}", file=sys.stderr)
        if not selected:
            print("ERROR: No valid models selected.", file=sys.stderr)
            sys.exit(1)
    else:
        selected = models

    print_comparison(selected, metrics=args.metrics, verbose=args.verbose or args.verbose)


if __name__ == "__main__":
    main()
