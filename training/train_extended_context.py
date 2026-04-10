#!/usr/bin/env python3
"""
Extended Context Fine-tuning for Stack 2.9
Extends Qwen2.5-Coder-1.5B from 32K to 128K context using RoPE scaling.
Run on cloud GPU (T4/A100).

FIXED: Handles messages-array format, uses packing for efficient 128K training,
enables bitsandbytes 4-bit quantization for T4 compatibility.
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
from datasets import load_dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Extended context fine-tuning")
    parser.add_argument("--model-path", type=str, required=True,
                        help="Path to base Qwen2.5-Coder-1.5B model or HF model ID")
    parser.add_argument("--data-path", type=str, required=True,
                        help="Path to training data (JSONL with messages format)")
    parser.add_argument("--output-dir", type=str, default="./output/stack-2.9-128k",
                        help="Output directory")
    parser.add_argument("--context-length", type=int, default=131072,
                        help="Target context length (default: 128K)")
    parser.add_argument("--lora-rank", type=int, default=32,
                        help="LoRA rank (default: 32)")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Per-device batch size (default: 1)")
    parser.add_argument("--grad-accum", type=int, default=16,
                        help="Gradient accumulation steps (default: 16)")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="Learning rate (default: 2e-4)")
    parser.add_argument("--max-examples", type=int, default=-1,
                        help="Max examples to load (-1 = all)")
    parser.add_argument("--push-to-hub", action="store_true",
                        help="Push final model to HuggingFace")
    parser.add_argument("--hub-model-id", type=str, default=None,
                        help="HF model ID for push")
    parser.add_argument("--use-packing", action="store_true", default=True,
                        help="Pack short examples into 128K windows (default: True)")
    return parser.parse_args()


def messages_to_text(example):
    """Convert messages-array format to text for LM training."""
    messages = example.get("messages", [])
    parts = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content") or ""
        if role == "system":
            parts.append(f"<|system|>\n{content}")
        elif role == "user":
            parts.append(f"<|user|>\n{content}")
        elif role == "assistant":
            parts.append(f"<|assistant|>\n{content}")
        elif role == "tool":
            parts.append(f"<|tool|>\n{content}")
    text = "\n".join(parts)
    if not text.endswith("<|assistant|>"):
        text += "\n<|assistant|>"
    return text


def pack_examples(tokenizer, examples, max_length=131072, separator="<|separator|>"):
    """
    Pack multiple short examples into one long sequence.
    Returns list of {'input_ids': [...], 'labels': [...]} dicts.
    """
    sep_id = tokenizer.encode(separator, add_special_tokens=False)[0]

    packed = []
    current = []

    for ex in examples:
        tokens = ex  # already tokenized
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


def main():
    args = parse_args()

    print("=" * 60)
    print("Stack 2.9 — 128K Extended Context Fine-tune")
    print("=" * 60)
    print(f"Model:       {args.model_path}")
    print(f"Data:        {args.data_path}")
    print(f"Output:      {args.output_dir}")
    print(f"Context:     {args.context_length // 1024}K tokens")
    print(f"LoRA r:      {args.lora_rank}")
    print(f"Epochs:      {args.epochs}")
    print(f"Batch:       {args.batch_size} x {args.grad_accum} grad accum = {args.batch_size * args.grad_accum}")
    print(f"LR:          {args.lr}")
    print(f"Packing:     {args.use_packing}")
    print("=" * 60)

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("/tmp/stack29_pack", exist_ok=True)

    # ── 1. Load Tokenizer ──────────────────────────────────────────────
    print("\n[1/6] Loading tokenizer...")
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

    # ── 3. Tokenize ───────────────────────────────────────────────────
    print("\n[3/6] Tokenizing dataset...")

    if args.use_packing:
        # FAST path: encode all, then pack
        all_tokens = []
        for i, ex in enumerate(raw_ds):
            text = messages_to_text(ex)
            tokens = tokenizer.encode(text, add_special_tokens=False)
            all_tokens.append(tokens)
            if (i + 1) % 500 == 0:
                print(f"   Tokenized {i+1}/{len(raw_ds)}...")

        print(f"   Packing {len(all_tokens)} examples into 128K sequences...")
        packed = pack_examples(tokenizer, all_tokens, max_length=args.context_length)
        print(f"   Created {len(packed)} packed sequences")

        # Build dataset
        from datasets import Dataset
        train_ds = Dataset.from_list(packed)

        # Split
        split = train_ds.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
        print(f"   Train: {len(train_ds)} | Val: {len(val_ds)} packed seqs")

        # Stats
        lens = [len(s["input_ids"]) for s in packed]
        print(f"   Avg tokens/sequence: {sum(lens)//len(lens):,}")

        # Custom collator — sequences already packed, just pad
        class PackedCollator:
            def __init__(self, tokenizer):
                self.tokenizer = tokenizer
            def __call__(self, features):
                max_len = max(len(f["input_ids"]) for f in features)
                batch = {
                    "input_ids": torch.tensor([
                        f["input_ids"] + [self.tokenizer.pad_token_id] * (max_len - len(f["input_ids"]))
                        for f in features
                    ], dtype=torch.long),
                    "labels": torch.tensor([
                        f["labels"] + [-100] * (max_len - len(f["labels"]))
                        for f in features
                    ], dtype=torch.long),
                    "attention_mask": torch.tensor([
                        [1] * len(f["input_ids"]) + [0] * (max_len - len(f["input_ids"]))
                        for f in features
                    ], dtype=torch.long),
                }
                return batch
        data_collator = PackedCollator(tokenizer)
    else:
        # SLOW path: tokenize with padding to context_length
        def tokenize(example):
            text = messages_to_text(example)
            enc = tokenizer(
                text,
                truncation=True,
                max_length=args.context_length,
                padding="max_length",
                return_special_tokens_mask=True,
            )
            enc["labels"] = enc["input_ids"].copy()
            return enc

        tokenized = raw_ds.map(tokenize, remove_columns=raw_ds.column_names, desc="Tokenizing")
        split = tokenized.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
        print(f"   Train: {len(train_ds)} | Val: {len(val_ds)}")
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # ── 4. Load Model ─────────────────────────────────────────────────
    print("\n[4/6] Loading model...")

    # Try bitsandbytes 4-bit first (T4 compatible)
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
        print(f"   4-bit failed ({e}), falling back to fp16")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        use_quant = False

    # Apply RoPE scaling for 128K context
    if hasattr(model.config, 'max_position_embeddings'):
        print(f"   Original max_position_embeddings: {model.config.max_position_embeddings}")
    model.config.max_position_embeddings = args.context_length
    if hasattr(model.config, 'rope_scaling'):
        print(f"   RoPE scaling: {model.config.rope_scaling}")

    # LoRA
    lora_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_rank,
        lora_alpha=args.lora_rank * 2,
        lora_dropout=0.05,
        bias="none",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    mem = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    print(f"   GPU memory: {mem:.2f} GB")

    # ── 5. Training Args ──────────────────────────────────────────────
    print("\n[5/6] Setting up training...")
    total_steps = (len(train_ds) // (args.batch_size * args.grad_accum)) * args.epochs
    warmup = max(10, int(total_steps * 0.05))
    print(f"   Total steps: {total_steps} | Warmup: {warmup}")

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        warmup_steps=warmup,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        max_grad_norm=0.3,
        weight_decay=0.01,
        fp16=True,
        bf16=False,
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
        hub_strategy="save",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # ── 6. Train ──────────────────────────────────────────────────────
    print("\n[6/6] Starting training...")
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
