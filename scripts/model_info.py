#!/usr/bin/env python3
"""
model_info.py — Extract and report Stack 2.9 model metadata.

Reads from models/registry.json and optionally from a model checkpoint
directory to extract/verify metadata.

Usage:
    python scripts/model_info.py                     # Show all models
    python scripts/model_info.py --model stack-2.9-1.5B
    python scripts/model_info.py --model stack-2.9-7B-QLoRA --verbose
    python scripts/model_info.py --export-json /path/to/output.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


REGISTRY_PATH = Path(__file__).parent.parent / "models" / "registry.json"


def load_registry(registry_path: Path = REGISTRY_PATH) -> dict:
    """Load the model registry JSON."""
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}", file=sys.stderr)
        sys.exit(1)
    with open(registry_path) as f:
        return json.load(f)


def format_params(n: int) -> str:
    """Format parameter count as human-readable string."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.0f}M"
    return str(n)


def format_lora(config: Optional[dict]) -> str:
    """Format LoRA config as readable string."""
    if not config:
        return "N/A (full model)"
    lines = [
        f"  Rank (r):         {config.get('rank', 'N/A')}",
        f"  Alpha:            {config.get('alpha', 'N/A')}",
        f"  Dropout:          {config.get('dropout', 'N/A')}",
        f"  Target Modules:   {', '.join(config.get('target_modules', []))}",
    ]
    if config.get("modules_to_save"):
        lines.append(f"  Modules to Save:  {', '.join(config['modules_to_save'])}")
    return "\n".join(lines)


def format_performance(metrics: dict) -> str:
    """Format performance metrics."""
    benchmarks = {
        "HellaSwag": metrics.get("hellaswag"),
        "ARC-Challenge": metrics.get("arc_challenge"),
        "MMLU": metrics.get("mmlu"),
        "HumanEval": metrics.get("humaneval"),
        "Training Loss": metrics.get("loss"),
    }
    lines = []
    for name, value in benchmarks.items():
        if value is not None:
            lines.append(f"  {name:20s} {value}")
        else:
            lines.append(f"  {name:20s} N/A")
    return "\n".join(lines) if lines else "  No benchmarks yet"


def status_emoji(status: str) -> str:
    """Return emoji for model status."""
    return {
        "in_training": "🟡 IN TRAINING",
        "planned": "🔴 PLANNED",
        "released": "🟢 RELEASED",
        "deprecated": "⚠️  DEPRECATED",
    }.get(status, f"({status})")


def print_model(model: dict, verbose: bool = False):
    """Print a single model's info."""
    print(f"\n{'='*60}")
    print(f"  {model['version']}  [{status_emoji(model['status'])}]")
    print(f"{'='*60}")

    print(f"\n  Base Model:      {model['base_model']}")
    print(f"  Parameters:      {format_params(model['parameters'])} ({model['parameters']:,})")
    print(f"  Quantization:    {model.get('quantization') or 'None (full precision)'}")
    print(f"  Precision:       {model.get('precision', 'N/A')}")
    print(f"  Context Length:  {model.get('context_length', 'N/A'):,} tokens")
    print(f"  Vocab Size:      {model.get('vocabulary_size', 'N/A'):,}")
    print(f"  Dataset:         {model['dataset']}")
    print(f"  Created:         {model.get('created_at') or 'TBD'}")

    print(f"\n  LoRA Config:")
    print(f"  {format_lora(model.get('lora'))}")

    print(f"\n  Performance Metrics:")
    print(f"  {format_performance(model.get('performance', {}))}")

    print(f"\n  Use Case:        {model['use_case']}")
    if model.get("notes"):
        print(f"  Notes:           {model['notes']}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract and report Stack 2.9 model metadata."
    )
    parser.add_argument(
        "--model", "-m",
        help="Specific model version to show (e.g., stack-2.9-1.5B). "
             "If omitted, shows all models."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output (same as default)."
    )
    parser.add_argument(
        "--export-json", "-o",
        metavar="PATH",
        help="Export selected model(s) as JSON to a file."
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

    if args.model:
        selected = [m for m in models if m["version"] == args.model]
        if not selected:
            print(f"ERROR: Model '{args.model}' not found in registry.", file=sys.stderr)
            print("Available models:", ", ".join(m["version"] for m in models))
            sys.exit(1)
    else:
        selected = models

    for model in selected:
        print_model(model, verbose=args.verbose)

    # Export to JSON if requested
    if args.export_json:
        output = {"registry_version": registry.get("registry_version"), "models": selected}
        with open(args.export_json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n✓ Exported to {args.export_json}")

    print()


if __name__ == "__main__":
    main()
