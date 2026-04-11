#!/usr/bin/env python3
"""
Simple standalone training script for Stack 2.9.
Uses bfloat16 with optional 4-bit quantization via bitsandbytes.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np  # Ensure numpy is available (Kaggle pip installs can break it)

import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from data_utils import load_chat_data
from peft import LoraConfig, get_peft_model, TaskType
import torch


def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_model_and_tokenizer(
    model_name: str,
    trust_remote_code: bool = True,
    use_4bit: bool = False,
    use_8bit: bool = False,
    use_fp16: bool = True,
):
    """Load base model with explicit GPU placement for single-GPU training."""
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, trust_remote_code=trust_remote_code
    )

    if use_4bit:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            trust_remote_code=trust_remote_code,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
    elif use_8bit:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_has_fp16_weight=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            trust_remote_code=trust_remote_code,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
    else:
        # No quantization - load in FP32 for AMP compatibility
        # Trainer with fp16=True will handle casting during training
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            trust_remote_code=trust_remote_code,
            device_map="auto",
            use_cache=False,
        )

    return model, tokenizer


def load_data(
    data_path: str,
    tokenizer,
    max_length: int = 2048,
    train_split: float = 0.9,
):
    """Load and tokenize dataset using messages-format JSONL with tool_calls."""
    return load_chat_data(data_path, tokenizer, max_length=max_length, train_split=train_split)


def train(config: dict):
    """Main training function."""
    model_config = config["model"]
    data_config = config["data"]
    lora_config = config["lora"]
    training_config = config["training"]
    output_config = config["output"]
    hardware_config = config.get("hardware", {})
    quantization_config = config.get("quantization", {})

    use_4bit = hardware_config.get("use_4bit", False) or quantization_config.get("enabled", False)
    use_8bit = hardware_config.get("use_8bit", False)

    # Set environment variables for better CUDA memory management
    # expandable_segments:False fixes a known PyTorch bug (#124807, #128829) with gradient checkpointing
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:False"

    # Clear CUDA cache before loading
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    # Determine precision BEFORE loading model
    # GPU BF16 support check — use the proper PyTorch API
    supports_bf16 = torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    print(f"   GPU: {gpu_name}")
    print(f"   BF16 supported: {supports_bf16}")

    # Use fp16 for training on Turing/Pascal (T4, P100)
    # Use bf16 for training on Ampere+ (A100, A10, H100)
    use_bf16 = supports_bf16
    use_fp16 = not use_bf16

    if training_config.get("bf16", False) and not supports_bf16:
        print(f"   ⚠️  bf16 requested but GPU doesn't support it — falling back to fp16")
    print(f"   Mixed precision: bf16={use_bf16}, fp16={use_fp16}")

    # Load model and tokenizer (MUST use same dtype as training precision)
    print(f"Loading model: {model_config['name']} (4bit={use_4bit}, 8bit={use_8bit})")
    model, tokenizer = load_model_and_tokenizer(
        model_name=model_config["name"],
        trust_remote_code=model_config.get("trust_remote_code", True),
        use_4bit=use_4bit,
        use_8bit=use_8bit,
        use_fp16=use_fp16,
    )

    # Print memory stats after model loading
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"   GPU memory after model load: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")

    # Load data
    print(f"Loading dataset: {data_config['input_path']}")
    train_dataset, eval_dataset = load_data(
        data_path=data_config["input_path"],
        tokenizer=tokenizer,
        max_length=data_config.get("max_length", 2048),
        train_split=data_config.get("train_split", 0.9),
    )
    print(f"   Train samples: {len(train_dataset)}")
    if eval_dataset:
        print(f"   Eval samples: {len(eval_dataset)}")
    else:
        print("   No eval set (using all data for training)")

    # Apply LoRA
    peft_config = LoraConfig(
        r=lora_config["r"],
        lora_alpha=lora_config.get("lora_alpha", lora_config.get("alpha", 32)),
        lora_dropout=lora_config.get("lora_dropout", lora_config.get("dropout", 0.05)),
        target_modules=lora_config["target_modules"],
        bias=lora_config["bias"],
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Training arguments
    output_dir = output_config["lora_dir"]
    os.makedirs(output_dir, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=training_config["num_epochs"],
        per_device_train_batch_size=training_config["batch_size"],
        gradient_accumulation_steps=training_config["gradient_accumulation"],
        learning_rate=training_config["learning_rate"],
        warmup_steps=training_config.get("warmup_steps", 100),
        weight_decay=training_config.get("weight_decay", 0.01),
        max_grad_norm=training_config.get("max_grad_norm", 1.0),
        max_steps=training_config.get("max_steps", -1),
        logging_steps=training_config.get("logging_steps", 10),
        save_steps=training_config.get("save_steps", 100),
        save_total_limit=training_config.get("save_total_limit", 2),
        bf16=False,
        fp16=False,  # Disabled — P100/Pascal AMP has GradScaler bugs with fp16
        gradient_checkpointing=training_config.get("gradient_checkpointing", True),
        gradient_checkpointing_kwargs={"use_reentrant": False},
        evaluation_strategy="steps" if eval_dataset else "no",
        eval_steps=training_config.get("eval_steps", 100) if eval_dataset else None,
        report_to="none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
        optim="paged_adamw_32bit" if (use_4bit or use_8bit) else "adamw_torch_fused",
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    print("=" * 60)
    print("Starting training...")
    print("=" * 60)
    trainer.train()
    print("Training completed!")

    # Save final adapter
    trainer.save_model(output_dir)
    print(f"✅ Adapter saved to {output_dir}")

    return trainer


def make_config_from_args(args) -> dict:
    """Build a minimal config dict from CLI arguments for quick testing."""
    return {
        "model": {
            "name": args.model_name or "Qwen/Qwen2.5-Coder-1.5B",
            "trust_remote_code": True,
        },
        "data": {
            "input_path": args.data_path or "training/training-data/tool_examples_combined.jsonl",
            "max_length": args.max_length or 2048,
            "train_split": args.train_split or 0.9,
        },
        "lora": {
            "r": args.lora_r or 16,
            "alpha": args.lora_alpha or 32,
            "dropout": 0.05,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            "bias": "none",
        },
        "training": {
            "num_epochs": 1,
            "batch_size": args.per_device_batch_size or 1,
            "gradient_accumulation": args.gradient_accumulation or 4,
            "learning_rate": 1e-4,
            "warmup_steps": 10,
            "weight_decay": 0.01,
            "max_grad_norm": 1.0,
            "logging_steps": 5,
            "save_steps": 100,
            "save_total_limit": 1,
            "gradient_checkpointing": True,
        },
        "output": {
            "lora_dir": args.output_dir or "./output/lora",
        },
        "hardware": {
            "use_4bit": args.use_4bit or False,
            "use_8bit": args.use_8bit or False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 Training")
    # Config file mode (original)
    parser.add_argument("--config", type=str, help="Path to YAML config ( mutually exclusive with CLI args)")
    # CLI mode for quick testing
    parser.add_argument("--data_path", type=str, default=None, help="Path to JSONL data file")
    parser.add_argument("--model_name", type=str, default=None, help="Model name or path")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for checkpoints")
    parser.add_argument("--max_steps", type=int, default=None, help="Max training steps (overrides epochs)")
    parser.add_argument("--max_length", type=int, default=None, help="Max sequence length")
    parser.add_argument("--train_split", type=float, default=None, help="Train/eval split ratio")
    parser.add_argument("--per_device_batch_size", type=int, default=None)
    parser.add_argument("--gradient_accumulation", type=int, default=None)
    parser.add_argument("--lora_r", type=int, default=None)
    parser.add_argument("--lora_alpha", type=int, default=None)
    parser.add_argument("--use_4bit", action="store_true")
    parser.add_argument("--use_8bit", action="store_true")
    
    args = parser.parse_args()

    print("=" * 60)
    print("Stack 2.9 Simple Training")
    print("=" * 60)

    if args.config:
        # Original config-file mode
        config = load_config(args.config)
        print(f"Config loaded: {args.config}")
        print(f"Model: {config['model']['name']}")
        print(f"Data: {config['data']['input_path']}")
    else:
        # CLI mode
        if not args.data_path and not args.output_dir:
            parser.error("Either --config or (--data_path and --output_dir) is required")
        config = make_config_from_args(args)
        print(f"Model: {config['model']['name']}")
        print(f"Data: {config['data']['input_path']}")
    
    # Override max_steps if specified
    if args.max_steps is not None:
        config["training"]["max_steps"] = args.max_steps
        config["training"]["num_epochs"] = 999  # effectively infinite
        config["training"]["save_steps"] = args.max_steps + 10  # don't save mid-training

    try:
        train(config)
        print("\n" + "=" * 60)
        print("✅ TRAINING SUCCESS")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TRAINING FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
