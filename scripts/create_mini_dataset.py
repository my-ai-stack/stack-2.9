#!/usr/bin/env python3
"""
Create a minimal training dataset for rapid prototyping.
Samples N examples from the full data/final/train.jsonl ensuring tool diversity.
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict
from collections import defaultdict, Counter

def load_full_dataset(train_path: str = "data/final/train.jsonl") -> List[Dict]:
    """Load the full dataset."""
    path = Path(train_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data not found at {path}. Please ensure data/final/train.jsonl exists.")

    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def extract_tool_calls(example: Dict) -> List[str]:
    """Extract tool names used in an example."""
    tools = []
    messages = example.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                name = func.get("name", "")
                if name:
                    tools.append(name)
    return tools

def create_mini_dataset(
    output_path: str,
    n_samples: int = 5000,
    train_source: str = "data/final/train.jsonl",
    seed: int = 42
):
    """Create a stratified mini dataset."""
    random.seed(seed)

    print(f"Loading full dataset from {train_source}...")
    full_data = load_full_dataset(train_source)
    print(f"Loaded {len(full_data)} total examples")

    # Group by tool usage
    tool_groups = defaultdict(list)
    unknown_tools = []

    for ex in full_data:
        tools = extract_tool_calls(ex)
        if tools:
            # Use first tool as primary category
            primary_tool = tools[0]
            tool_groups[primary_tool].append(ex)
        else:
            unknown_tools.append(ex)

    print(f"\nTool distribution in full dataset:")
    total_tool_examples = sum(len(v) for v in tool_groups.values())
    for tool, examples in sorted(tool_groups.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
        pct = len(examples) / len(full_data) * 100
        print(f"  {tool}: {len(examples)} examples ({pct:.1f}%)")

    print(f"  No-tool examples: {len(unknown_tools)} ({len(unknown_tools)/len(full_data)*100:.1f}%)")

    # Determine sampling strategy
    # Allocate samples proportionally, but ensure minimum 3 examples per tool
    samples_per_tool = {}
    min_per_tool = 3
    remaining = n_samples

    # First pass: assign minimum to all tools that have enough
    for tool, examples in tool_groups.items():
        if len(examples) >= min_per_tool:
            samples_per_tool[tool] = min_per_tool
            remaining -= min_per_tool

    # Second pass: distribute remaining proportionally
    if remaining > 0:
        total_weight = sum(len(v) for v in tool_groups.values() if len(v) >= min_per_tool)
        for tool, examples in tool_groups.items():
            if len(examples) >= min_per_tool:
                weight = len(examples) / total_weight
                extra = int(remaining * weight)
                samples_per_tool[tool] += extra
                remaining -= extra

    # Fill any leftover with no-tool examples
    if remaining > 0 and unknown_tools:
        samples_per_tool["__notool__"] = min(remaining, len(unknown_tools))
        remaining -= min(remaining, len(unknown_tools))

    # If we still have remaining, just take from the largest tool groups
    if remaining > 0:
        sorted_tools = sorted(tool_groups.items(), key=lambda x: len(x[1]), reverse=True)
        for tool, examples in sorted_tools:
            if remaining <= 0:
                break
            can_take = min(remaining, len(examples) - samples_per_tool.get(tool, 0))
            if can_take > 0:
                samples_per_tool[tool] = samples_per_tool.get(tool, 0) + can_take
                remaining -= can_take

    print(f"\nSampling plan (target {n_samples}):")
    total_sampled = 0
    for tool, n in sorted(samples_per_tool.items(), key=lambda x: x[1], reverse=True):
        if n > 0:
            available = len(tool_groups.get(tool, [])) if tool != "__notool__" else len(unknown_tools)
            pct = n / n_samples * 100
            print(f"  {tool}: {n} examples ({pct:.1f}%) from {available} available")
            total_sampled += n

    # Perform sampling
    mini_dataset = []
    for tool, n_to_sample in samples_per_tool.items():
        if n_to_sample <= 0:
            continue

        source_pool = tool_groups[tool] if tool != "__notool__" else unknown_tools
        if len(source_pool) < n_to_sample:
            n_to_sample = len(source_pool)

        sampled = random.sample(source_pool, n_to_sample)
        mini_dataset.extend(sampled)

    # Shuffle the final dataset
    random.shuffle(mini_dataset)

    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for ex in mini_dataset:
            f.write(json.dumps(ex) + '\n')

    print(f"\n✅ Mini dataset created: {len(mini_dataset)} examples")
    print(f"   Saved to: {output_path}")

    # Stats
    tool_counts = Counter()
    for ex in mini_dataset:
        tools = extract_tool_calls(ex)
        if tools:
            tool_counts[tools[0]] += 1
        else:
            tool_counts["__notool__"] += 1

    print(f"\nFinal tool distribution:")
    for tool, count in tool_counts.most_common(15):
        pct = count / len(mini_dataset) * 100
        print(f"  {tool}: {count} ({pct:.1f}%)")

    return mini_dataset

def main():
    parser = argparse.ArgumentParser(description="Create mini dataset for fast prototyping")
    parser.add_argument("--size", type=int, default=5000, help="Number of examples in mini dataset")
    parser.add_argument("--output", type=str, default="./data_mini/train_mini.jsonl", help="Output file path")
    parser.add_argument("--source", type=str, default="data/final/train.jsonl", help="Source full dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")

    args = parser.parse_args()

    create_mini_dataset(
        output_path=args.output,
        n_samples=args.size,
        train_source=args.source,
        seed=args.seed
    )

if __name__ == "__main__":
    main()
