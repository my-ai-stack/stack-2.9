#!/usr/bin/env python3
"""
Data augmentation for training examples.
Increases dataset size by paraphrasing and variations.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Paraphrase templates (rule-based, no LLM)
PARAPHRASES = {
    "Read the file": ["Show me the contents of", "Open", "Display", "Fetch", "Get"],
    "Create a new file": ["Write a file", "Generate", "Make a new file", "Add file"],
    "Run": ["Execute", "Start", "Launch", "Invoke"],
    "Search for": ["Find", "Look for", "Locate", "Grep for"],
    "List all": ["Show all", "Display every", "Get list of"],
    "Can you": ["Please", "Would you", "Kindly"],
    "I need": ["I want", "I require", "Please provide"],
}

def paraphrase_text(text: str) -> str:
    """Apply simple paraphrasing to user prompt."""
    result = text
    for original, alternatives in PARAPHRASES.items():
        if original in result:
            replacement = random.choice(alternatives)
            result = result.replace(original, replacement, 1)
    return result

def augment_example(example: Dict[str, Any], variation_factor: float = 0.3) -> List[Dict[str, Any]]:
    """Generate variations of a single example."""
    variations = [example]  # Keep original

    # Paraphrase user message
    if random.random() < variation_factor:
        new_ex = json.loads(json.dumps(example))  # Deep copy
        original_user = new_ex["messages"][0]["content"]
        new_ex["messages"][0]["content"] = paraphrase_text(original_user)
        new_ex["source"] = "augmented_paraphrase"
        variations.append(new_ex)

    # Vary tool parameters (if any)
    if "tool_use" in example["messages"][1]:
        tool_input = example["messages"][1]["tool_use"]["input"]
        if isinstance(tool_input, dict) and tool_input:
            new_ex = json.loads(json.dumps(example))
            # Randomly change file paths, commands, etc.
            for key, val in new_ex["messages"][1]["tool_use"]["input"].items():
                if key == "file_path" and isinstance(val, str):
                    # Change to a different plausible file
                    new_ex["messages"][1]["tool_use"]["input"][key] = random.choice([
                        "src/main.py", "README.md", "package.json", "config.yaml"
                    ])
                    # Also update result if it contains the old file path
                    result_content = new_ex["messages"][2]["tool_result"]["content"]
                    new_ex["messages"][2]["tool_result"]["content"] = result_content.replace(val, new_ex["messages"][1]["tool_use"]["input"][key])
                    new_ex["source"] = "augmented_params"
                    variations.append(new_ex)

    # Add filler words to user message
    if random.random() < variation_factor * 0.5:
        new_ex = json.loads(json.dumps(example))
        fillers = [" please", " if you can", " when you have time", " thanks"]
        user_msg = new_ex["messages"][0]["content"]
        filler = random.choice(fillers)
        new_ex["messages"][0]["content"] = user_msg + filler
        new_ex["source"] = "augmented_filler"
        variations.append(new_ex)

    return variations

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="training-data/scaled/template_synthetic.jsonl")
    parser.add_argument("--output", type=str, default="training-data/scaled/augmented.jsonl")
    parser.add_argument("--multiplier", type=int, default=3, help="How many times to multiply dataset")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return

    print(f"📈 Augmenting dataset: {input_path}")
    examples = []
    with open(input_path, 'r') as f:
        for line in f:
            examples.append(json.loads(line))

    original_count = len(examples)
    target_count = original_count * args.multiplier
    print(f"   Original: {original_count} examples")
    print(f"   Target: ~{target_count} examples (x{args.multiplier})")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated = 0
    with open(output_path, 'w') as f:
        for ex in examples:
            # Write original and variations
            f.write(json.dumps(ex) + "\n")
            generated += 1

            # Generate variations until we reach multiplier
            variations = augment_example(ex)
            for var in variations[1:]:  # Skip original (already written)
                if generated < target_count:
                    f.write(json.dumps(var) + "\n")
                    generated += 1

            if generated % 1000 == 0:
                print(f"   Generated {generated}/{target_count}...", end='\r')

    print(f"\n✨ Augmented to {generated} examples")
    print(f"   Saved to: {output_path}")
    print(f"   Total dataset now: {original_count} → {generated} (x{generated/original_count:.1f})")

if __name__ == "__main__":
    main()