#!/usr/bin/env python3
"""
Stack 2.9 LoRA Fine-tuning Script
Fine-tunes Qwen2.5-Coder-32B with LoRA adapter.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml
import torch
import numpy as np
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset, Dataset
from peft import LoraConfig, get_peft_model, PeftModel
from accelerate import Accelerator
import bitsandbytes as bnb


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load training configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "train_config.yaml"
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_model_and_tokenizer(config: Dict[str, Any]) -> tuple:
    """
    Load model and tokenizer with appropriate settings.
    """
    model_config = config["model"]
    hardware_config = config["hardware"]
    quant_config = config["quantization"]
    
    model_name = model_config["name"]
    torch_dtype = getattr(torch, model_config.get("torch_dtype", "float16"))
    trust_remote_code = model_config.get("trust_remote_code", True)
    
    # Load tokenizer
    print(f"Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=trust_remote_code
    )
    
    # Add padding token if needed
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model - handle MPS/CPU for local training
    print(f"Loading model: {model_name}")
    
    device = hardware_config.get("device", "mps")
    load_in_4bit = hardware_config.get("use_4bit", False)
    load_in_8bit = hardware_config.get("use_8bit", False)
    
    # Check for MPS availability
    if device == "mps" and not torch.backends.mps.is_available():
        print("MPS not available, falling back to CPU")
        device = "cpu"
    
    if load_in_4bit and device != "cpu":
        from bitsandbytes import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch_dtype,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        device_map = "auto"
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map=device_map,
            torch_dtype=torch_dtype,
            trust_remote_code=trust_remote_code
        )
        print("Model loaded in 4-bit precision")
    else:
        # Load without quantization - use device_map for MPS/CPU
        if device == "mps":
            # MPS needs device_map="auto" or explicit device placement
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch_dtype,
                trust_remote_code=trust_remote_code
            )
            # Force to MPS if not already
            if next(model.parameters()).device.type != "mps":
                model = model.to("mps")
            print("Model loaded in float16 on MPS")
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch_dtype,
                trust_remote_code=trust_remote_code
            )
            print("Model loaded in full precision")
    
    return model, tokenizer


def setup_lora(config: Dict[str, Any]) -> LoraConfig:
    """
    Configure LoRA parameters.
    """
    lora_config = config["lora"]
    
    return LoraConfig(
        r=lora_config["r"],
        lora_alpha=lora_config["alpha"],
        lora_dropout=lora_config.get("dropout", 0.05),
        target_modules=lora_config["target_modules"],
        bias=lora_config.get("bias", "none"),
        task_type=lora_config.get("task_type", "CAUSAL_LM"),
        inference_mode=False
    )


def create_training_arguments(config: Dict[str, Any]) -> TrainingArguments:
    """
    Create HuggingFace TrainingArguments from config.
    """
    training_config = config["training"]
    output_config = config["output"]
    logging_config = config["logging"]
    hardware_config = config["hardware"]
    
    output_dir = output_config["lora_dir"]
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    report_to = []
    if logging_config.get("report_to") == "wandb":
        report_to = ["wandb"]
        
        # Initialize wandb
        import wandb
        wandb.init(
            project=logging_config.get("wandb_project", "stack-2.9"),
            name=logging_config.get("run_name")
        )
    
    # Determine device for training
    device = hardware_config.get("device", "mps")
    
    return TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=training_config["batch_size"],
        per_device_eval_batch_size=training_config["batch_size"],
        gradient_accumulation_steps=training_config["gradient_accumulation"],
        learning_rate=training_config["learning_rate"],
        num_train_epochs=training_config["num_epochs"],
        warmup_steps=training_config["warmup_steps"],
        weight_decay=training_config["weight_decay"],
        max_grad_norm=training_config["max_grad_norm"],
        fp16=training_config.get("fp16", True),
        bf16=training_config.get("bf16", False),  # Use config setting
        gradient_checkpointing=training_config.get("gradient_checkpointing", True),
        logging_steps=training_config["logging_steps"],
        eval_strategy="steps",
        eval_steps=training_config["eval_steps"],
        save_strategy="steps",
        save_steps=training_config["save_steps"],
        save_total_limit=training_config.get("save_total_limit", 3),
        report_to=report_to,
        remove_unused_columns=False,
        optim="adamw_torch",
        logging_first_step=True,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        ddp_find_unused_parameters=False,
        dataloader_num_workers=0
    )


def create_data_collator(tokenizer: AutoTokenizer) -> DataCollatorForLanguageModeling:
    """
    Create data collator for language modeling.
    """
    return DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # Causal LM, not masked LM
    )


def train_lora(
    config_path: str = None,
    resume_from_checkpoint: Optional[str] = None
) -> None:
    """
    Main LoRA training function.
    
    Args:
        config_path: Path to config file
        resume_from_checkpoint: Checkpoint to resume from
    """
    print("=" * 60)
    print("Stack 2.9 LoRA Fine-tuning")
    print("=" * 60)
    
    # Load configuration
    config = load_config(config_path)
    data_config = config["data"]
    lora_config = config["lora"]
    output_config = config["output"]
    
    # Print configuration
    print(f"\n📋 Configuration:")
    print(f"   Model: {config['model']['name']}")
    print(f"   LoRA rank: {lora_config['r']}")
    print(f"   LoRA alpha: {lora_config['alpha']}")
    print(f"   Target modules: {lora_config['target_modules']}")
    print(f"   Epochs: {config['training']['num_epochs']}")
    print(f"   Batch size: {config['training']['batch_size']}")
    print(f"   Gradient accumulation: {config['training']['gradient_accumulation']}")
    print(f"   Learning rate: {config['training']['learning_rate']}")
    
    # Load datasets - handle local disk datasets
    print(f"\n📂 Loading datasets...")
    train_dir = data_config["train_dir"]
    eval_dir = data_config["eval_dir"]
    
    # Check if it's a local disk dataset (saved with save_to_disk)
    # save_to_disk creates dataset_info.json
    if Path(train_dir).exists() and (Path(train_dir) / "dataset_info.json").exists():
        from datasets import load_from_disk
        train_dataset = load_from_disk(train_dir)
        eval_dataset = load_from_disk(eval_dir)
        print(f"   Loaded pre-processed datasets from disk")
    else:
        # Try loading as JSONL or other format
        train_dataset = load_dataset(train_dir)
        eval_dataset = load_dataset(eval_dir)
        print(f"   Loaded datasets from: {train_dir}, {eval_dir}")
    
    print(f"   Train samples: {len(train_dataset)}")
    print(f"   Eval samples: {len(eval_dataset)}")
    
    # Setup model and tokenizer
    print(f"\n🤖 Setting up model...")
    model, tokenizer = setup_model_and_tokenizer(config)
    
    # Setup LoRA
    print(f"\n🔧 Applying LoRA...")
    lora_cfg = setup_lora(config)
    model = get_peft_model(model, lora_cfg)
    
    # Print trainable parameters
    model.print_trainable_parameters()
    
    # Setup training arguments
    print(f"\n⚙️ Setting up training...")
    training_args = create_training_arguments(config)
    
    # Create data collator
    data_collator = create_data_collator(tokenizer)
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer
    )
    
    # Train
    print(f"\n🚀 Starting training...")
    
    # Resume if specified
    checkpoint = None
    if resume_from_checkpoint:
        checkpoint = resume_from_checkpoint
    elif Path(output_config["lora_dir"]).exists():
        # Check for latest checkpoint
        checkpoints = list(Path(output_config["lora_dir"]).glob("checkpoint-*"))
        if checkpoints:
            checkpoint = str(max(checkpoints, key=lambda p: int(p.name.split("-")[-1])))
    
    if checkpoint:
        print(f"   Resuming from checkpoint: {checkpoint}")
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
    else:
        train_result = trainer.train()
    
    # Save final model
    print(f"\n💾 Saving model...")
    trainer.save_model()
    trainer.save_state()
    
    print(f"\n✅ Training completed!")
    print(f"   Model saved to: {output_config['lora_dir']}")
    
    # Return training metrics
    metrics = train_result.metrics
    train_metrics = {k: v for k, v in metrics.items() if "loss" in k.lower()}
    print(f"   Final metrics: {train_metrics}")
    
    return trainer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stack 2.9 LoRA Training")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint to resume from")
    args = parser.parse_args()
    
    try:
        train_lora(args.config, args.resume)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)