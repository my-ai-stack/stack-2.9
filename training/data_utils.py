#!/usr/bin/env python3
"""
Data utilities for Stack 2.9 training.
Handles the messages-format JSONL data with tool_calls.
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from datasets import load_dataset
from transformers import PreTrainedTokenizer


def format_tool_calls(tool_calls: List[Dict[str, Any]]) -> str:
    """Format tool_calls list into the XML string expected by Qwen chat template."""
    if not tool_calls:
        return ""
    parts = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        args_str = func.get("arguments", "")
        # arguments is already a JSON string
        parts.append(
            f"<tool_call>\n<name>{name}</name>\n<args>\n{args_str}\n</args>\n</tool_call>"
        )
    return "".join(parts)


def messages_to_text(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tokenizer: Optional[PreTrainedTokenizer] = None,
) -> str:
    """
    Convert a messages array to a single text string using the tokenizer's chat template.
    
    For Qwen: uses the built-in chat template which handles tool_calls formatting.
    For others: falls back to a simple role/content concatenation.
    
    Args:
        messages: list of message dicts with role/content/tool_calls
        tools: optional list of tool definitions
        tokenizer: tokenizer with chat_template (preferred)
    
    Returns:
        Formatted conversation string ready for tokenization
    """
    if tokenizer is not None and tokenizer.chat_template:
        # Use the tokenizer's chat template
        try:
            # Build the messages dict in the format the template expects
            formatted = tokenizer.apply_chat_template(
                messages,
                tools=tools,
                tokenize=False,
                add_generation_prompt=False,
            )
            return formatted
        except Exception as e:
            # Fallback if template fails
            print(f"[WARN] Chat template failed: {e}, using manual format")
    
    # Manual fallback - simple concatenation
    text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls", [])
        
        if role == "system":
            text += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == "user":
            text += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "assistant":
            # Format tool calls if present
            if tool_calls:
                tc_text = format_tool_calls(tool_calls)
                text += f"<|im_start|>assistant\n{tc_text}"
                if content:
                    text += f"\n{content}"
                text += "<|im_end|>\n"
            else:
                text += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        elif role == "tool":
            # Tool result
            text += f"<|im_start|>tool\n{content}<|im_end|>\n"
    
    # Add generation prompt at end
    text += "<|im_start|>assistant\n"
    return text


def flatten_example(
    example: Dict[str, Any],
    tokenizer: PreTrainedTokenizer,
    max_length: int,
) -> Dict[str, Any]:
    """
    Flatten a single conversation example into training tokens.
    
    The input_ids are the full formatted conversation.
    Labels are the same but with user/system/tool tokens masked out (replaced with -100).
    
    For tool_call examples:
    - The assistant's tool_calls + content are ALL part of labels (model learns to generate both)
    - User and system messages are masked
    """
    messages = example.get("messages", [])
    tools = example.get("tools", None)
    
    if not messages:
        return None
    
    # Format the full conversation using chat template
    try:
        full_text = messages_to_text(messages, tools, tokenizer)
    except Exception as e:
        print(f"[WARN] Failed to format example: {e}")
        return None
    
    # Tokenize
    tokens = tokenizer(
        full_text,
        truncation=True,
        max_length=max_length,
        padding="max_length",
        return_tensors=None,
    )
    
    input_ids = tokens["input_ids"]
    attention_mask = tokens["attention_mask"]
    
    # Create labels - start with input_ids, then mask out non-assistant parts
    labels = list(input_ids)
    
    # Find where each role's content starts in the tokenized sequence
    # We work backwards from the end since we only train on the last assistant response
    
    # Find the last assistant message boundary
    # Strategy: find the last "<|im_start|>assistant" token position
    # Everything AFTER that is training data (assistant's response)
    # Everything BEFORE is masked
    
    assistant_token = tokenizer.encode("<|im_start|>assistant", add_special_tokens=False)
    if not assistant_token:
        # Fallback: mask first half
        labels = [-100] * (len(labels) // 2) + labels[len(labels) // 2:]
    else:
        # Find ALL occurrences of assistant token and take the LAST one
        last_assistant_pos = -1
        for i in range(len(input_ids) - len(assistant_token) + 1):
            if input_ids[i:i+len(assistant_token)] == assistant_token:
                last_assistant_pos = i
        
        if last_assistant_pos >= 0:
            # Mask everything up to and including the last assistant start
            for i in range(last_assistant_pos + len(assistant_token)):
                labels[i] = -100
        else:
            # No clear assistant boundary found - mask first 70%
            mask_until = int(len(labels) * 0.7)
            for i in range(mask_until):
                labels[i] = -100
    
    # Also mask tool role messages (they're responses from the "environment", not model output)
    tool_token = tokenizer.encode("<|im_start|>tool", add_special_tokens=False)
    if tool_token:
        for i in range(len(input_ids) - len(tool_token) + 1):
            if input_ids[i:i+len(tool_token)] == tool_token:
                for j in range(len(tool_token)):
                    labels[i + j] = -100
    
    # Mask padding
    for i, (ids, mask) in enumerate(zip(input_ids, attention_mask)):
        if mask == 0:
            labels[i] = -100
    
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def load_chat_data(
    data_path: str,
    tokenizer: PreTrainedTokenizer,
    max_length: int = 2048,
    train_split: float = 0.9,
) -> Tuple[Any, Any]:
    """
    Load messages-format JSONL and convert to training dataset.
    
    Args:
        data_path: path to .jsonl file with messages-format data
        tokenizer: tokenizer for encoding
        max_length: max sequence length
        train_split: fraction for training (0.9 = 90% train, 10% eval)
    
    Returns:
        Tuple of (train_dataset, eval_dataset) ready for CausalLM training
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    print(f"Loading data from {data_path}")
    
    # Load raw JSONL dataset
    raw_dataset = load_dataset("json", data_files=data_path, split="train")
    print(f"  Loaded {len(raw_dataset)} examples")
    
    # Check first example to validate format
    if len(raw_dataset) > 0:
        first = raw_dataset[0]
        has_messages = "messages" in first
        print(f"  Format check: has_messages={has_messages}")
    
    # Flatten to tokenized dataset
    print(f"  Tokenizing with max_length={max_length}...")
    tokenized = raw_dataset.map(
        lambda ex: flatten_example(ex, tokenizer, max_length),
        remove_columns=raw_dataset.column_names,
        desc="Tokenizing",
    )
    
    # Remove any failed examples
    tokenized = tokenized.filter(
        lambda ex: ex is not None and ex.get("labels") is not None,
        desc="Filtering failed examples",
    )
    print(f"  After filtering: {len(tokenized)} examples")
    
    # Train/eval split
    if train_split >= 1.0:
        # treat as absolute count
        n_train = int(train_split)
        if n_train >= len(tokenized):
            return tokenized, None
        split_ds = tokenized.train_test_split(train_size=n_train)
        return split_ds["train"], split_ds["test"]
    else:
        split_ds = tokenized.train_test_split(train_size=train_split)
        return split_ds["train"], split_ds["test"]


# Backwards compatibility - re-export
__all__ = ["load_chat_data", "messages_to_text", "format_tool_calls"]
