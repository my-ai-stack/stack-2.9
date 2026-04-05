#!/usr/bin/env python3
"""
Data augmentation script for tool_examples.jsonl.
Generates 2x-5x more training examples from existing data through:
- Paraphrasing user prompts
- Difficulty scaling (simpler/complex variations)
- Edge case generation
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from itertools import product
import copy

# Random seed for reproducibility
random.seed(42)

# Paraphrase templates
PARAPHRASES = {
    "Can you": ["Please", "Would you kindly", "Could you", "Kindly"],
    "I need": ["I'd like", "I require", "I want", "I must have"],
    "show me": ["display", "show", "reveal", "let me see"],
    "the file": ["this file", "that file", "a file"],
    "run": ["execute", "launch", "start", "run"],
    "create": ["make", "generate", "add", "write"],
    "delete": ["remove", "erase", "drop", "destroy"],
    "list": ["show", "display", "enumerate", "get"],
    "search": ["find", "look for", "grep", "locate"],
    "help me": ["assist me", "I need help", "please assist", "support"],
}

# Difficulty modifiers
EASY_MODIFIERS = [
    "quickly",
    "simply",
    "just",
    "easily",
]

COMPLEX_MODIFIERS = [
    "carefully",
    "thoroughly",
    "in detail",
    "completely",
    "with all options",
]

# Edge case patterns
EDGE_CASE_PATTERNS = [
    ("empty_input", lambda ex: _create_empty_variant(ex)),
    ("multi_step", lambda ex: _create_multistep_variant(ex)),
    ("error_handling", lambda ex: _create_error_variant(ex)),
]


def _deep_copy(obj: Any) -> Any:
    """Create a deep copy of a JSON-serializable object."""
    return json.loads(json.dumps(obj))


def _create_empty_variant(example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create variant with empty/blank user input."""
    new_ex = _deep_copy(example)
    # Keep system message, empty user message
    for msg in new_ex["messages"]:
        if msg["role"] == "user":
            msg["content"] = " "
            break
    new_ex["source"] = "augmented_edge_empty"
    return new_ex


def _create_multistep_variant(example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create variant simulating multi-step reasoning."""
    new_ex = _deep_copy(example)
    # Add reasoning step before tool call
    for i, msg in enumerate(new_ex["messages"]):
        if msg.get("tool_calls"):
            reasoning = {
                "role": "assistant",
                "content": "Let me think about this step by step. First, I need to understand what the user is asking for."
            }
            new_ex["messages"].insert(i, reasoning)
            break
    new_ex["source"] = "augmented_edge_multistep"
    return new_ex


def _create_error_variant(example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create variant simulating error handling."""
    new_ex = _deep_copy(example)
    for msg in new_ex["messages"]:
        if msg.get("role") == "tool":
            # Simulate an error in tool result
            if "Successfully" in msg.get("content", ""):
                msg["content"] = msg["content"].replace("Successfully", "Error occurred:")
            elif "error" not in msg.get("content", "").lower():
                msg["content"] = "Operation failed: Permission denied"
            break
    new_ex["source"] = "augmented_edge_error"
    return new_ex


def paraphrase_text(text: str) -> str:
    """Apply simple paraphrasing to text."""
    if not text:
        return text
    result = text
    for original, alternatives in PARAPHRASES.items():
        if original.lower() in result.lower():
            # Case-insensitive replace, preserve original case pattern
            idx = result.lower().find(original.lower())
            prefix = result[:idx]
            suffix = result[idx + len(original):]
            replacement = random.choice(alternatives)
            # Preserve case
            if result[idx].isupper():
                replacement = replacement.capitalize()
            result = prefix + replacement + suffix
            break
    return result


def apply_difficulty(example: Dict[str, Any], level: str) -> Dict[str, Any]:
    """Apply difficulty scaling to an example."""
    new_ex = _deep_copy(example)
    modifiers = EASY_MODIFIERS if level == "easy" else COMPLEX_MODIFIERS
    
    for msg in new_ex["messages"]:
        if msg["role"] == "user" and msg.get("content"):
            content = msg["content"]
            if level == "easy":
                # Simplify the request
                content = content.replace("please", "").replace("kindly", "")
                content = content.strip()
            elif level == "complex":
                # Add complexity
                modifier = random.choice(modifiers)
                content = f"{content} {modifier}"
            msg["content"] = content
            break
    
    new_ex["source"] = f"augmented_difficulty_{level}"
    return new_ex


def vary_tool_parameters(example: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate variations with different tool parameters."""
    variations = []
    
    for msg in example.get("messages", []):
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except (json.JSONDecodeError, TypeError):
                    continue
                
                if not isinstance(args, dict):
                    continue
                
                # Common parameter variations
                param_variations = [
                    ("file_path", ["src/main.py", "README.md", "config.yaml", "package.json", "tests/test.py"]),
                    ("command", ["ls -la", "echo hello", "pwd", "whoami"]),
                    ("pattern", ["*.py", "*.js", "*.md", "*.json"]),
                    ("path", ["src", "lib", "docs", "."]),
                ]
                
                for param_name, alternatives in param_variations:
                    if param_name in args:
                        original_val = args[param_name]
                        for alt_val in alternatives:
                            if alt_val != original_val:
                                new_ex = _deep_copy(example)
                                for new_msg in new_ex["messages"]:
                                    if new_msg.get("tool_calls"):
                                        for new_tc in new_msg["tool_calls"]:
                                            new_func = new_tc.get("function", {})
                                            new_args = json.loads(new_func.get("arguments", "{}"))
                                            if param_name in new_args:
                                                new_args[param_name] = alt_val
                                                new_func["arguments"] = json.dumps(new_args)
                                new_ex["source"] = "augmented_params"
                                variations.append(new_ex)
                                break
    
    return variations


def add_filler_variant(example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Add polite filler words to user message."""
    fillers = [" please", " if you could", " when you get a chance", " thanks"]
    
    new_ex = _deep_copy(example)
    for msg in new_ex["messages"]:
        if msg["role"] == "user" and msg.get("content"):
            filler = random.choice(fillers)
            msg["content"] = msg["content"].rstrip() + filler
            break
    
    new_ex["source"] = "augmented_filler"
    return new_ex


def generate_edge_cases(example: Dict[str, Any], num_cases: int = 2) -> List[Dict[str, Any]]:
    """Generate edge case variations."""
    cases = []
    selected_patterns = random.sample(EDGE_CASE_PATTERNS, min(num_cases, len(EDGE_CASE_PATTERNS)))
    
    for name, generator in selected_patterns:
        try:
            variant = generator(example)
            if variant:
                cases.append(variant)
        except Exception:
            continue
    
    return cases


def augment_example(example: Dict[str, Any], target_multiplier: int = 3) -> List[Dict[str, Any]]:
    """Generate multiple augmented variations of a single example."""
    variations = [example]  # Always keep original
    
    # 1. Paraphrase variant
    if random.random() < 0.7:
        new_ex = _deep_copy(example)
        for msg in new_ex["messages"]:
            if msg["role"] == "user" and msg.get("content"):
                msg["content"] = paraphrase_text(msg["content"])
                break
        new_ex["source"] = "augmented_paraphrase"
        variations.append(new_ex)
    
    # 2. Difficulty variants (easy and complex)
    if random.random() < 0.5:
        variations.append(apply_difficulty(example, "easy"))
    if random.random() < 0.5:
        variations.append(apply_difficulty(example, "complex"))
    
    # 3. Filler variant
    if random.random() < 0.3:
        filler_ex = add_filler_variant(example)
        if filler_ex:
            variations.append(filler_ex)
    
    # 4. Tool parameter variations
    param_variations = vary_tool_parameters(example)
    variations.extend(param_variations[:2])  # Limit to 2
    
    # 5. Edge cases
    if random.random() < 0.3:
        edge_cases = generate_edge_cases(example)
        variations.extend(edge_cases[:1])
    
    return variations[:target_multiplier]  # Limit total variations


def main():
    parser = argparse.ArgumentParser(description="Augment training data for Stack 2.9")
    parser.add_argument("--input", type=str, 
                        default="training-data/tool_examples.jsonl",
                        help="Input JSONL file")
    parser.add_argument("--output", type=str, 
                        default="training-data/augmented_tool_examples.jsonl",
                        help="Output JSONL file")
    parser.add_argument("--multiplier", type=int, default=3,
                        help="Target multiplication factor (2-5)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    print(f"Loading data from: {input_path}")
    examples = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    examples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    original_count = len(examples)
    print(f"Loaded {original_count} examples")
    
    # Generate augmented examples
    all_variations = []
    for ex in examples:
        variations = augment_example(ex, target_multiplier=args.multiplier)
        all_variations.extend(variations)
    
    total_count = len(all_variations)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for var in all_variations:
            f.write(json.dumps(var, ensure_ascii=False) + "\n")
    
    print(f"\nAugmentation complete!")
    print(f"  Original: {original_count} examples")
    print(f"  Augmented: {total_count} examples")
    print(f"  Multiplier: {total_count/original_count:.1f}x")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()
