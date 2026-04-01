#!/usr/bin/env python3
"""
Stack 2.9 Data Preparation Pipeline
Loads, cleans, formats, deduplicates, and filters training data for instruction tuning.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
import pandas as pd
from datasets import Dataset, load_dataset
from transformers import AutoTokenizer


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load training configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "train_config.yaml"
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from JSONL file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Training data file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping line {line_num} - JSON decode error: {e}")
                continue
    
    if not data:
        raise ValueError(f"No valid data found in {file_path}")
    
    return data


def format_for_instruction_tuning(
    example: Dict[str, Any],
    model_name: str = "Qwen/Qwen2.5-Coder-32B"
) -> str:
    """
    Format training example for instruction tuning using chat template.
    Handles multiple data formats: messages, instruction/response, prompt/completion.
    """
    # Format 1: OpenAI-style messages (messages field)
    if "messages" in example:
        messages = example["messages"]
        
        # Extract system, user, assistant messages
        system_msg = None
        user_msg = None
        assistant_msg = None
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                system_msg = content
            elif role == "user":
                user_msg = content
            elif role == "assistant":
                assistant_msg = content
        
        # Build formatted string
        if system_msg:
            return f"### System:\n{system_msg}\n\n### User:\n{user_msg}\n\n### Assistant:\n{assistant_msg}"
        else:
            return f"### User:\n{user_msg}\n\n### Assistant:\n{assistant_msg}"
    
    # Format 2: instruction/response
    if "instruction" in example and "response" in example:
        return f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
    
    # Format 3: prompt/completion
    if "prompt" in example and "completion" in example:
        return f"### Prompt:\n{example['prompt']}\n\n### Completion:\n{example['completion']}"
    
    # Format 4: input/output
    if "input" in example and "output" in example:
        return f"### Input:\n{example['input']}\n\n### Output:\n{example['output']}"
    
    raise ValueError(f"Unknown data format. Expected one of: messages, instruction/response, prompt/completion, input/output. Keys found: {list(example.keys())}")


def deduplicate(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate examples based on content hash.
    """
    seen_hashes = set()
    unique_data = []
    
    for example in data:
        # Create hash from the formatted content
        content = json.dumps(example, sort_keys=True)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_data.append(example)
    
    duplicates_removed = len(data) - len(unique_data)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate examples")
    
    return unique_data


def quality_filter(
    data: List[Dict[str, Any]],
    min_length: int = 10,
    max_length: int = 128000,
    require_response: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter training data based on quality criteria.
    
    Args:
        data: List of training examples
        min_length: Minimum response length
        max_length: Maximum total length
        require_response: Whether to require non-empty response
    
    Returns:
        Filtered list of examples
    """
    filtered_data = []
    
    for example in data:
        try:
            # Extract response content
            response = ""
            
            if "messages" in example:
                for msg in example["messages"]:
                    if msg.get("role") == "assistant":
                        response = msg.get("content", "")
                        break
            elif "response" in example:
                response = example["response"]
            elif "completion" in example:
                response = example["completion"]
            elif "output" in example:
                response = example["output"]
            
            # Skip if no response
            if require_response and not response:
                continue
            
            # Skip if response too short
            if len(response) < min_length:
                continue
            
            # Skip if total content too long
            if len(json.dumps(example)) > max_length:
                continue
            
            filtered_data.append(example)
            
        except Exception as e:
            print(f"Warning: Skipping example due to error: {e}")
            continue
    
    filtered_count = len(data) - len(filtered_data)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} low-quality examples")
    
    return filtered_data


def tokenize_dataset(
    texts: List[str],
    tokenizer: AutoTokenizer,
    max_length: int = 131072,
    add_special_tokens: bool = True
) -> Dataset:
    """
    Tokenize text dataset with proper encoding.
    """
    def tokenize_batch(batch):
        return tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors=None,
            add_special_tokens=add_special_tokens
        )
    
    # Create dataset from texts
    df = pd.DataFrame({"text": texts})
    dataset = Dataset.from_pandas(df)
    
    # Tokenize
    dataset = dataset.map(
        tokenize_batch,
        batched=True,
        remove_columns=["text"],
        desc="Tokenizing dataset"
    )
    
    return dataset


def prepare_data(
    config_path: str = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Main data preparation pipeline.
    
    Args:
        config_path: Path to config file
        force: Force re-creation even if data exists
    
    Returns:
        Dictionary with dataset info
    """
    print("=" * 60)
    print("Stack 2.9 Data Preparation Pipeline")
    print("=" * 60)
    
    # Load config
    config = load_config(config_path)
    data_config = config["data"]
    
    # Set paths
    input_path = Path(data_config["input_path"])
    train_dir = Path(data_config["train_dir"])
    eval_dir = Path(data_config["eval_dir"])
    max_length = data_config["max_length"]
    train_split = data_config["train_split"]
    
    # Check if data already exists
    if not force and train_dir.exists() and eval_dir.exists():
        print(f"Data already exists at {train_dir} and {eval_dir}")
        print("Use force=True to re-create")
        
        # Load and return stats
        train_ds = load_dataset(str(train_dir))
        eval_ds = load_dataset(str(eval_dir))
        
        return {
            "train_samples": len(train_ds["train"]),
            "eval_samples": len(eval_ds["test"]),
            "train_dir": str(train_dir),
            "eval_dir": str(eval_dir)
        }
    
    # Create directories
    train_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load raw data
    print(f"\n📁 Loading data from: {input_path}")
    raw_data = load_jsonl(input_path)
    print(f"   Loaded {len(raw_data)} examples")
    
    # Step 2: Format for instruction tuning
    print("\n📝 Formatting examples for instruction tuning...")
    model_name = config["model"]["name"]
    formatted_texts = []
    
    for i, example in enumerate(raw_data):
        try:
            text = format_for_instruction_tuning(example, model_name)
            formatted_texts.append(text)
        except ValueError as e:
            print(f"   Warning: Skipping example {i}: {e}")
    
    print(f"   Formatted {len(formatted_texts)} examples")
    
    # Step 3: Deduplicate
    print("\n🔄 Deduplicating...")
    unique_texts = deduplicate(formatted_texts)
    print(f"   Unique examples: {len(unique_texts)}")
    
    # Step 4: Quality filter
    print("\n🧹 Quality filtering...")
    quality_data = quality_filter(unique_texts)
    print(f"   After quality filter: {len(quality_data)}")
    
    # Step 5: Re-format for tokenization
    print("\n🔢 Tokenizing...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    
    # Handle chat template
    if tokenizer.chat_template is None:
        print("   Warning: No chat template found, using raw text")
    
    # Split into train/eval
    print(f"\n📊 Splitting data ({train_split*100:.0f}% train / {(1-train_split)*100:.0f}% eval)...")
    
    import numpy as np
    indices = np.random.permutation(len(quality_data))
    split_idx = int(len(quality_data) * train_split)
    
    train_indices = indices[:split_idx]
    eval_indices = indices[split_idx:]
    
    train_texts = [quality_data[i] for i in train_indices]
    eval_texts = [quality_data[i] for i in eval_indices]
    
    # Tokenize datasets
    train_dataset = tokenize_dataset(train_texts, tokenizer, max_length)
    eval_dataset = tokenize_dataset(eval_texts, tokenizer, max_length)
    
    # Save datasets
    print(f"\n💾 Saving datasets...")
    train_dataset.save_to_disk(str(train_dir))
    eval_dataset.save_to_disk(str(eval_dir))
    
    print(f"   Train: {len(train_dataset)} examples -> {train_dir}")
    print(f"   Eval: {len(eval_dataset)} examples -> {eval_dir}")
    
    print("\n" + "=" * 60)
    print("✅ Data preparation completed!")
    print("=" * 60)
    
    return {
        "train_samples": len(train_dataset),
        "eval_samples": len(eval_dataset),
        "train_dir": str(train_dir),
        "eval_dir": str(eval_dir)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stack 2.9 Data Preparation")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--force", action="store_true", help="Force re-create data")
    args = parser.parse_args()
    
    try:
        result = prepare_data(args.config, args.force)
        
        print(f"\n📊 Summary:")
        print(f"   Training samples: {result['train_samples']}")
        print(f"   Evaluation samples: {result['eval_samples']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)