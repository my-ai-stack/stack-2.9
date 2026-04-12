#!/usr/bin/env python3
"""
Gemma 3 7B Fine-tuning for Stack 2.9
Uses Gemma chat template format, Gemma LoRA modules, and tuned hyperparameters.
Run on cloud GPU (A10G).
"""
import argparse
import os
import random
import json
import subprocess
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset, Dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Gemma 3 7B fine-tuning")
    parser.add_argument("--model-path", type=str, required=True,
                        help="Model ID or path")
    parser.add_argument("--data-path", type=str, required=True,
                        help="Path to training data (JSONL with messages format)")
    parser.add_argument("--output-dir", type=str, default="./output/stack-2.9-gemma",
                        help="Output directory")
    parser.add_argument("--context-length", type=int, default=2048,
                        help="Max sequence length (default: 2048)")
    parser.add_argument("--lora-rank", type=int, default=32,
                        help="LoRA rank (default: 32)")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Per-device batch size (default: 1)")
    parser.add_argument("--grad-accum", type=int, default=32,
                        help="Gradient accumulation steps (default: 32)")
    parser.add_argument("--lr", type=float, default=5e-5,
                        help="Learning rate (default: 5e-5)")
    parser.add_argument("--max-examples", type=int, default=-1,
                        help="Max examples to load (-1 = all)")
    parser.add_argument("--push-to-hub", action="store_true",
                        help="Push final model to HuggingFace")
    parser.add_argument("--hub-model-id", type=str, default=None,
                        help="HF model ID for push")
    parser.add_argument("--use-packing", action="store_true", default=True,
                        help="Pack short examples into sequences (default: True)")
    return parser.parse_args()


def format_gemma_conversation(example):
    """Convert messages-array format to Gemma chat template."""
    messages = example.get("messages", [])
    text = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "") or ""
        tool_calls = msg.get("tool_calls", [])

        if role == "system":
            text += f"<start_of_turn>user\n{content}<end_of_turn>\n"
        elif role == "user":
            text += f"<start_of_turn>user\n{content}<end_of_turn>\n"
        elif role == "assistant":
            if tool_calls:
                for tc in tool_calls:
                    fn = tc["function"]
                    args_str = fn["arguments"]
                    text += f"<start_of_turn>model\n<tool_call>\n"
                    text += f'{{"name": "{fn["name"]}", "arguments": {args_str}}}\n'
                    text += f"</tool_call>\n<end_of_turn>\n"
                if content:
                    text += f"<start_of_turn>model\n{content}<end_of_turn>\n"
            else:
                text += f"<start_of_turn>model\n{content}<end_of_turn>\n"
        elif role == "tool":
            text += f"<start_of_turn>tool\n{content}<end_of_turn>\n"

    if not text.endswith("<start_of_turn>model\n"):
        text += "<start_of_turn>model\n"
    return {"text": text}


def mask_user_and_tool_tokens(labels, input_ids, tokenizer):
    """
    Mask user, system, and tool tokens so only assistant tokens are trained.
    Replaces non-assistant token IDs with -100 (ignore index).
    """
    masked_labels = labels.clone()
    
    # Find the special tokens
    user_tok_ids = []
    tool_tok_ids = []
    model_tok_ids = []
    
    # Get individual tokens that may appear in user/tool/model content
    # We'll use a heuristic: after <start_of_turn>user or <start_of_turn>tool,
    # content tokens should be masked. The assistant content after 
    # <start_of_turn>model should NOT be masked.
    
    # Tokenize the markers to find their IDs
    user_start = tokenizer.encode("<start_of_turn>user", add_special_tokens=False)
    tool_start = tokenizer.encode("<start_of_turn>tool", add_special_tokens=False)
    model_start = tokenizer.encode("<start_of_turn>model", add_special_tokens=False)
    
    # Scan through and mask appropriately
    i = 0
    current_role_is_assistant = False
    
    while i < len(input_ids):
        # Check if we're at a role marker
        matched_role = None
        
        # Check for user marker
        if i <= len(input_ids) - len(user_start):
            if input_ids[i:i+len(user_start)] == user_start:
                matched_role = "user"
        
        # Check for tool marker  
        if i <= len(input_ids) - len(tool_start):
            if input_ids[i:i+len(tool_start)] == tool_start:
                matched_role = "tool"
        
        # Check for model marker
        if i <= len(input_ids) - len(model_start):
            if input_ids[i:i+len(model_start)] == model_start:
                matched_role = "assistant"
        
        if matched_role == "assistant":
            # Mark the model start tokens, but then skip past them
            # and DON'T mask the actual assistant response content
            i += len(model_start)
            current_role_is_assistant = True
            continue
        elif matched_role in ("user", "tool"):
            # Mask all content until next role marker
            i += len(user_start if matched_role == "user" else tool_start)
            current_role_is_assistant = False
            # Now mask tokens until we see a role change
            while i < len(input_ids):
                # Check for next role marker
                next_is_model = (i <= len(input_ids) - len(model_start) and 
                                input_ids[i:i+len(model_start)] == model_start)
                next_is_user = (i <= len(input_ids) - len(user_start) and 
                               input_ids[i:i+len(user_start)] == user_start)
                next_is_tool = (i <= len(input_ids) - len(tool_start) and 
                               input_ids[i:i+len(tool_start)] == tool_start)
                
                if next_is_model or next_is_user or next_is_tool:
                    break
                if labels[i] != -100:  # Don't overwrite already masked
                    masked_labels[i] = -100
                i += 1
        else:
            i += 1
    
    return masked_labels


def pack_examples(tokenizer, examples, max_length=2048, separator="<end_of_turn>"):
    """
    Pack multiple short examples into one long sequence.
    Returns list of {'input_ids': [...], 'labels': [...]} dicts.
    """
    # Use eos as separator
    sep_id = tokenizer.encode(separator, add_special_tokens=False)
    if sep_id:
        sep_id = sep_id[0]
    else:
        sep_id = tokenizer.eos_token_id

    packed = []
    current = []

    for ex in examples:
        tokens = ex
        if current and len(current) + len(tokens) + 2 > max_length:
            packed.append({"input_ids": current, "labels": current.copy()})
            current = []
        if current:
            current.append(sep_id)
        current.extend(tokens)
        if len(current) > max_length:
            current = current[:max_length]

    if current:
        packed.append({"input_ids": current, "labels": current.copy()})

    return packed


class GemmaCollator:
    """Custom collator that masks user/system/tool tokens for Gemma."""
    def __init__(self, tokenizer, mask_user_tokens=True):
        self.tokenizer = tokenizer
        self.mask_user_tokens = mask_user_tokens
        
    def __call__(self, features):
        max_len = max(len(f["input_ids"]) for f in features)
        batch_input_ids = []
        batch_labels = []
        batch_attention_mask = []
        
        for f in features:
            input_ids = f["input_ids"]
            labels = f["labels"]
            
            # Pad
            pad_len = max_len - len(input_ids)
            input_ids = input_ids + [self.tokenizer.pad_token_id] * pad_len
            labels = labels + [-100] * pad_len
            attention_mask = [1] * len(f["input_ids"]) + [0] * pad_len
            
            batch_input_ids.append(input_ids)
            batch_labels.append(labels)
            batch_attention_mask.append(attention_mask)
        
        result = {
            "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(batch_attention_mask, dtype=torch.long),
        }
        
        # Apply label masking (mask user/tool tokens, train only on assistant)
        if self.mask_user_tokens:
            labels_tensor = torch.tensor(batch_labels, dtype=torch.long)
            # For Gemma, we need to mask user/tool content tokens
            # This is a simplified approach - masks content between role markers
            for i in range(labels_tensor.shape[0]):
                labels_tensor[i] = mask_user_and_tool_tokens(
                    labels_tensor[i],
                    result["input_ids"][i],
                    self.tokenizer
                )
            result["labels"] = labels_tensor
        else:
            result["labels"] = torch.tensor(batch_labels, dtype=torch.long)
        
        return result


def main():
    args = parse_args()

    print("=" * 60)
    print("Stack 2.9 — Gemma 3 7B Fine-tune")
    print("=" * 60)
    print(f"Model:       {args.model_path}")
    print(f"Data:        {args.data_path}")
    print(f"Output:      {args.output_dir}")
    print(f"Context:     {args.context_length} tokens")
    print(f"LoRA r:      {args.lora_rank}")
    print(f"Epochs:      {args.epochs}")
    print(f"Batch:       {args.batch_size} x {args.grad_accum} grad accum = {args.batch_size * args.grad_accum}")
    print(f"LR:          {args.lr}")
    print(f"Packing:     {args.use_packing}")
    print("=" * 60)

    os.makedirs(args.output_dir, exist_ok=True)

    # ── 1. Load Tokenizer ──────────────────────────────────────────────
    print("\n[1/6] Loading Gemma 3 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    tokenizer.padding_side = "right"
    tokenizer.pad_token = tokenizer.eos_token
    print(f"   Vocab size: {len(tokenizer)}")

    # ── 2. Load Raw Data ───────────────────────────────────────────────
    print("\n[2/6] Loading dataset...")
    raw_ds = load_dataset("json", data_files=args.data_path, split="train")
    if args.max_examples > 0:
        raw_ds = raw_ds.select(range(min(args.max_examples, len(raw_ds))))
    print(f"   Total examples: {len(raw_ds)}")

    # ── 3. Format to Gemma template ────────────────────────────────────
    print("\n[3/6] Converting to Gemma chat template...")
    formatted_ds = raw_ds.map(format_gemma_conversation, remove_columns=raw_ds.column_names)
    print(f"   Formatted: {len(formatted_ds)} examples")

    # ── 4. Tokenize ───────────────────────────────────────────────────
    print("\n[4/6] Tokenizing dataset...")

    if args.use_packing:
        # Encode all, then pack
        all_tokens = []
        for i, ex in enumerate(formatted_ds):
            text = ex["text"]
            tokens = tokenizer.encode(text, add_special_tokens=False)
            all_tokens.append(tokens)
            if (i + 1) % 500 == 0:
                print(f"   Tokenized {i+1}/{len(formatted_ds)}...")

        print(f"   Packing {len(all_tokens)} examples into {args.context_length} token sequences...")
        packed = pack_examples(tokenizer, all_tokens, max_length=args.context_length)
        print(f"   Created {len(packed)} packed sequences")

        train_ds = Dataset.from_list(packed)
        split = train_ds.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
        print(f"   Train: {len(train_ds)} | Val: {len(val_ds)} packed seqs")

        lens = [len(s["input_ids"]) for s in packed]
        print(f"   Avg tokens/sequence: {sum(lens)//len(lens):,}")

        data_collator = GemmaCollator(tokenizer, mask_user_tokens=True)
    else:
        def tokenize(example):
            enc = tokenizer(
                example["text"],
                truncation=True,
                max_length=args.context_length,
                padding="max_length",
            )
            enc["labels"] = enc["input_ids"].copy()
            return enc

        tokenized = formatted_ds.map(tokenize, remove_columns=formatted_ds.column_names, desc="Tokenizing")
        split = tokenized.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
        data_collator = GemmaCollator(tokenizer, mask_user_tokens=True)

    # ── 5. Load Model ─────────────────────────────────────────────────
    print("\n[5/6] Loading Gemma 3 model...")

    # Try bitsandbytes 4-bit first (A10G compatible)
    try:
        from transformers import BitsAndBytesConfig
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        print("   Using 4-bit quantization (bitsandbytes)")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            quantization_config=bnb_cfg,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model)
        use_quant = True
    except Exception as e:
        print(f"   4-bit failed ({e}), falling back to bf16")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        use_quant = False

    # LoRA with Gemma-specific target modules
    # CRITICAL: Gemma uses qkv_proj (NOT q_proj, k_proj, v_proj separately)
    lora_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_rank,
        lora_alpha=args.lora_rank * 2,
        lora_dropout=0.05,
        bias="none",
        target_modules=[
            "qkv_proj", "o_proj", "gate_proj", "up_proj", "down_proj"
        ]
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    mem = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    print(f"   GPU memory: {mem:.2f} GB")

    # ── 6. Training Args ──────────────────────────────────────────────
    print("\n[6/6] Setting up training...")
    total_steps = (len(train_ds) // (args.batch_size * args.grad_accum)) * args.epochs
    warmup = int(total_steps * 0.05)  # 5% warmup for Gemma
    print(f"   Total steps: {total_steps} | Warmup: {warmup}")

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        max_grad_norm=1.0,  # Gemma benefits from higher grad norm
        weight_decay=0.01,
        fp16=False,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        save_total_limit=2,
        optim="adamw_torch",
        report_to="none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
        seed=42,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
        hub_strategy="every_save",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
    )

    # ── 7. Train ──────────────────────────────────────────────────────
    print("\n[7/7] Starting training...")
    print("=" * 60)
    trainer.train()
    print("=" * 60)
    print("Training complete!")

    # Save
    final_path = os.path.join(args.output_dir, "final")
    trainer.save_model(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"\n✅ Adapter saved to: {final_path}")

    if args.push_to_hub and args.hub_model_id:
        print(f"Pushing to HuggingFace: {args.hub_model_id}")
        trainer.push_to_hub(args.hub_model_id)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
