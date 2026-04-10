#!/usr/bin/env python3
"""
Extended Context Fine-tuning for Stack 2.9
Extends Qwen2.5-Coder-1.5B from 32K to 128K context using RoPE scaling.
Run on cloud GPU (T4/A100).
"""
import argparse
import os
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
                        help="Path to base Qwen2.5-Coder-1.5B model")
    parser.add_argument("--data-path", type=str, required=True,
                        help="Path to training data (jsonl)")
    parser.add_argument("--output-dir", type=str, default="./output/stack-2.9-128k",
                        help="Output directory")
    parser.add_argument("--context-length", type=int, default=131072,
                        help="Target context length (default: 128K)")
    parser.add_argument("--lora-rank", type=int, default=64,
                        help="LoRA rank (default: 64)")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Per-device batch size (default: 1)")
    parser.add_argument("--grad-accum", type=int, default=16,
                        help="Gradient accumulation steps (default: 16)")
    parser.add_argument("--lr", type=float, default=5e-5,
                        help="Learning rate (default: 5e-5)")
    parser.add_argument("--push-to-hub", action="store_true",
                        help="Push final model to HuggingFace")
    parser.add_argument("--hub-model-id", type=str, default=None,
                        help="HF model ID for push")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print(f"Loading model from {args.model_path}")
    print(f"Target context: {args.context_length}")
    
    # Load tokenizer and update its max length
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    tokenizer.model_max_length = args.context_length
    
    # Load model with extended context config
    # The model's config.json should already have rope_scaling set
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    
    # Verify context extension
    print(f"Model max_position_embeddings: {model.config.max_position_embeddings}")
    if hasattr(model.config, 'rope_scaling'):
        print(f"RoPE scaling: {model.config.rope_scaling}")
    
    # Attach LoRA for efficient fine-tuning
    lora_config = LoraConfig(
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
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load dataset
    print(f"Loading data from {args.data_path}")
    dataset = load_dataset("json", data_files=args.data_path, split="train")
    
    # Tokenize with long context
    def tokenize(example):
        text = example.get("text", "")
        encoding = tokenizer(
            text,
            truncation=True,
            max_length=args.context_length,
            padding="max_length",
            return_special_tokens_mask=True
        )
        encoding["labels"] = encoding["input_ids"].copy()
        return encoding
    
    dataset = dataset.map(tokenize, remove_columns=dataset.column_names)
    
    # Training args
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        max_grad_norm=0.3,
        fp16=True,
        bf16=False,
        gradient_checkpointing=True,
        logging_steps=10,
        save_steps=500,
        eval_steps=500,
        save_total_limit=3,
        optim="paged_adamw_32bit",
        report_to="none",
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
        hub_strategy="save",
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked
    )
    
    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )
    
    print("Starting extended context fine-tuning...")
    trainer.train()
    
    # Save
    merged_dir = os.path.join(args.output_dir, "merged")
    print(f"Saving merged model to {merged_dir}")
    trainer.model.merge_and_unload()
    trainer.save_model(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    
    if args.push_to_hub and args.hub_model_id:
        print(f"Pushing to HuggingFace: {args.hub_model_id}")
        trainer.push_to_hub(args.hub_model_id)

if __name__ == "__main__":
    main()
