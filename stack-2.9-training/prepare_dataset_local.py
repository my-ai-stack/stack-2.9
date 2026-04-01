#!/usr/bin/env python3
"""
Prepare dataset for LoRA training - Stack 2.9 Local Version
"""
import json
import argparse
from pathlib import Path
from datasets import Dataset

def prepare_dataset(input_path, output_dir, max_length=2048, test_split=0.1):
    """Load JSONL and prepare for training with tokenization."""
    
    from transformers import AutoTokenizer
    
    print(f"Loading data from: {input_path}")
    
    # Load JSONL
    with open(input_path, 'r') as f:
        data = [json.loads(line) for line in f]
    
    print(f"Loaded {len(data)} examples")
    
    # Format as prompt + completion (for causal LM)
    formatted_data = []
    for item in data:
        if 'prompt' in item and 'completion' in item:
            text = item['prompt'] + item['completion']
            formatted_data.append({'text': text})
        elif 'input' in item and 'output' in item:
            text = item['input'] + item['output']
            formatted_data.append({'text': text})
        elif 'instruction' in item and 'output' in item:
            text = item['instruction'] + ' ' + item['output']
            formatted_data.append({'text': text})
    
    print(f"Formatted {len(formatted_data)} examples")
    
    # Create HuggingFace dataset
    dataset = Dataset.from_list(formatted_data)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B", trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=max_length,
            return_tensors=None
        )
    
    dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=['text']
    )
    
    # Split train/eval
    split = dataset.train_test_split(test_size=test_split)
    train_data = split['train']
    eval_data = split['test']
    
    # Save
    output_path = Path(output_dir)
    train_path = output_path / "train"
    eval_path = output_path / "eval"
    
    train_data.save_to_disk(str(train_path))
    eval_data.save_to_disk(str(eval_path))
    
    print(f"Saved to: {output_dir}")
    print(f"  Train: {len(train_data)} examples")
    print(f"  Eval: {len(eval_data)} examples")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="training-data/generated/synthetic_50k.jsonl")
    parser.add_argument("--output", type=str, default="stack-2.9-training/data")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--test-split", type=float, default=0.1)
    args = parser.parse_args()
    
    # Resolve paths relative to workspace
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path("/Users/walidsobhi/.openclaw/workspace/stack-2.9") / input_path
    
    prepare_dataset(
        str(input_path),
        args.output,
        args.max_length,
        args.test_split
    )