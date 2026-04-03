#!/usr/bin/env python3
"""
Stack 2.9 Dataset Preparation Script
Loads JSONL training data, applies Qwen chat template, tokenizes, and saves for training.
Supports multiple input files for combining datasets.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import argparse

from datasets import Dataset, load_dataset, load_from_disk, DatasetDict
from transformers import AutoTokenizer


SUPPORTED_MODELS = [
    "Qwen/Qwen2.5-Coder-32B",
    "Qwen/Qwen2.5-Coder-14B",
    "Qwen/Qwen2.5-Coder-7B",
    "Qwen/Qwen2.5-Coder-1.5B",
]


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of dicts."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping line {line_num} in {file_path}: {e}")
    return data


def format_sample(item: Dict[str, Any]) -> str:
    """
    Format a sample for causal LM training.
    Supports multiple data formats.
    """
    # Format 1: instruction + response
    if 'instruction' in item and 'response' in item:
        return f"### Instruction:\n{item['instruction']}\n\n### Response:\n{item['response']}"

    # Format 2: prompt + completion
    if 'prompt' in item and 'completion' in item:
        return f"### Prompt:\n{item['prompt']}\n\n### Completion:\n{item['completion']}"

    # Format 3: input + output
    if 'input' in item and 'output' in item:
        return f"### Input:\n{item['input']}\n\n### Output:\n{item['output']}"

    # Format 4: messages (chat format)
    if 'messages' in item:
        # Convert messages to text format
        messages = item['messages']
        text = ""
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                text += f"### User:\n{content}\n\n"
            elif role == 'assistant':
                text += f"### Assistant:\n{content}\n\n"
            elif role == 'system':
                text += f"### System:\n{content}\n\n"
        return text.strip()

    # Format 5: text field only
    if 'text' in item:
        return item['text']

    # Unknown format - return empty string
    print(f"Warning: Unknown format for item: {list(item.keys())}")
    return ""


def tokenize_function(examples, tokenizer, max_length: int):
    """Tokenize text examples."""
    return tokenizer(
        examples['text'],
        padding='max_length',
        truncation=True,
        max_length=max_length,
        return_tensors=None
    )


def prepare_dataset(
    input_files: List[str],
    output_dir: str,
    model_name: str = "Qwen/Qwen2.5-Coder-32B",
    max_length: int = 4096,
    test_split: float = 0.1,
    use_chat_template: bool = True,
    val_file: Optional[str] = None,
) -> None:
    """
    Prepare dataset for training.

    Args:
        input_files: List of JSONL files to combine for training
        output_dir: Directory to save processed datasets
        model_name: Model name for tokenizer
        max_length: Maximum sequence length
        test_split: Fraction for validation split
        use_chat_template: Whether to apply chat template
        val_file: Optional separate validation file
    """
    print("=" * 60)
    print("Stack 2.9 Dataset Preparation")
    print("=" * 60)

    # Validate model
    if model_name not in SUPPORTED_MODELS:
        print(f"Warning: Model {model_name} not in known models, attempting anyway")

    print(f"\n📋 Configuration:")
    print(f"   Model: {model_name}")
    print(f"   Max length: {max_length}")
    print(f"   Test split: {test_split}")

    # Load tokenizer
    print(f"\n🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right"  # Required for causal LM
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(f"   Set pad_token to eos_token")

    # Load and combine training data
    all_train_data = []
    for input_file in input_files:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Warning: File not found: {input_file}, skipping")
            continue

        print(f"\n📂 Loading: {input_file}")
        data = load_jsonl(str(input_path))
        print(f"   Loaded {len(data)} examples")
        all_train_data.extend(data)

    if not all_train_data:
        raise ValueError("No training data loaded!")

    print(f"\n📊 Total training examples: {len(all_train_data)}")

    # Format data
    print(f"\n✏️ Formatting examples...")
    formatted_data = []
    for i, item in enumerate(all_train_data):
        text = format_sample(item)
        if text:  # Only add non-empty
            formatted_data.append({'text': text})

    print(f"   Formatted {len(formatted_data)} examples")

    if not formatted_data:
        raise ValueError("No valid training samples after formatting!")

    # Create dataset
    dataset = Dataset.from_list(formatted_data)

    # Tokenize
    print(f"\n🔢 Tokenizing...")
    dataset = dataset.map(
        lambda examples: tokenize_function(examples, tokenizer, max_length),
        batched=True,
        remove_columns=['text'],
        desc="Tokenizing"
    )

    print(f"   Tokenized dataset: {len(dataset)} examples")

    # Split train/val
    if val_file and Path(val_file).exists():
        # Use separate validation file
        print(f"\n📂 Loading separate validation file: {val_file}")
        val_data = load_jsonl(val_file)
        val_formatted = []
        for item in val_data:
            text = format_sample(item)
            if text:
                val_formatted.append({'text': text})

        val_dataset = Dataset.from_list(val_formatted)
        val_dataset = val_dataset.map(
            lambda examples: tokenize_function(examples, tokenizer, max_length),
            batched=True,
            remove_columns=['text'],
            desc="Tokenizing validation"
        )

        # Use all of dataset for training, val_dataset for eval
        train_data = dataset
        eval_data = val_dataset
    else:
        # Split from main dataset
        print(f"\n✂️ Splitting dataset...")
        split = dataset.train_test_split(test_size=test_split)
        train_data = split['train']
        eval_data = split['test']

    print(f"   Train: {len(train_data)} examples")
    print(f"   Eval: {len(eval_data)} examples")

    # Save
    output_path = Path(output_dir)
    train_path = output_path / "train"
    eval_path = output_path / "eval"

    print(f"\n💾 Saving to: {output_dir}")
    train_data.save_to_disk(str(train_path))
    eval_data.save_to_disk(str(eval_path))

    print(f"   ✅ Done!")
    print(f"   Train saved to: {train_path}")
    print(f"   Eval saved to: {eval_path}")


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 Dataset Preparation")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file (optional)"
    )
    parser.add_argument(
        "--input",
        type=str,
        nargs="+",
        default=None,
        help="Input JSONL files (space-separated)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/data",
        help="Output directory for processed datasets"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-Coder-32B",
        help="Model name for tokenizer"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=4096,
        help="Maximum sequence length"
    )
    parser.add_argument(
        "--test-split",
        type=float,
        default=0.1,
        help="Validation split ratio"
    )
    parser.add_argument(
        "--val-file",
        type=str,
        default=None,
        help="Separate validation file (optional)"
    )

    args = parser.parse_args()

    # Determine input files
    if args.input:
        input_files = args.input
    else:
        # Default to final training data
        input_files = [
            "/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/final/train.jsonl"
        ]

    try:
        prepare_dataset(
            input_files=input_files,
            output_dir=args.output,
            model_name=args.model,
            max_length=args.max_length,
            test_split=args.test_split,
            val_file=args.val_file
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()