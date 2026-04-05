#!/usr/bin/env python3
"""
Simple standalone training script for Stack 2.9.
Uses bfloat16 with optional 4-bit quantization via bitsandbytes.
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
import torch


def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_model_and_tokenizer(
    model_name: str,
    trust_remote_code: bool = True,
    use_4bit: bool = False,
):
    """Load base model in bfloat16, with optional 4-bit quantization."""
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
            device_map={"": torch.device("cuda")},
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            trust_remote_code=trust_remote_code,
            device_map="auto",
            offload_folder="/tmp/model_offload",
            offload_state_dict=True,
        )

    return model, tokenizer


def load_data(
    data_path: str,
    tokenizer,
    max_length: int = 2048,
    train_split: float = 0.9,
):
    """Load and tokenize dataset.

    Args:
        train_split: If < 1.0, fraction for training (e.g., 0.9 = 90% train, 10% eval).
                     If >= 1.0, treated as absolute number of training samples.
                     If train_split equals dataset size, returns all for training (no eval).
    """
    raw_dataset = load_dataset("json", data_files=data_path, split="train")

    def tokenize_function(examples):
        texts = []
        for instr, out in zip(
            examples.get("instruction", [""]), examples.get("output", [""])
        ):
            if instr and out:
                texts.append(
                    f"### Instruction:\n{instr}\n\n### Response:\n{out}"
                )
            elif out:
                texts.append(out)
            elif instr:
                texts.append(instr)
            else:
                texts.append("")

        tokenized = tokenizer(
            texts, truncation=True, max_length=max_length, padding="max_length"
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    tokenized_dataset = raw_dataset.map(
        tokenize_function, batched=True, remove_columns=raw_dataset.column_names
    )

    # Handle train_split logic
    total_samples = len(tokenized_dataset)
    if train_split >= 1.0:
        n_train = int(train_split)
        if n_train >= total_samples:
            return tokenized_dataset, None
        else:
            split = tokenized_dataset.train_test_split(train_size=n_train)
            return split["train"], split["test"]
    else:
        split = tokenized_dataset.train_test_split(train_size=train_split)
        return split["train"], split["test"]


def train(config: dict):
    """Main training function."""
    model_config = config["model"]
    data_config = config["data"]
    lora_config = config["lora"]
    training_config = config["training"]
    output_config = config["output"]
    hardware_config = config.get("hardware", {})

    use_4bit = hardware_config.get("use_4bit", False)

    # Load model and tokenizer
    print(f"Loading model: {model_config['name']} (4bit={use_4bit})")
    model, tokenizer = load_model_and_tokenizer(
        model_name=model_config["name"],
        trust_remote_code=model_config.get("trust_remote_code", True),
        use_4bit=use_4bit,
    )

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

    # Enable gradient checkpointing with use_reentrant=False (required for PyTorch 2.9+)
    if training_config.get("gradient_checkpointing", True):
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        if hasattr(model, 'base_model') and hasattr(
            model.base_model, 'enable_gradient_checkpointing'
        ):
            model.base_model.enable_gradient_checkpointing(
                gradient_checkpointing_kwargs={"use_reentrant": False}
            )

    # Training arguments — bf16 is safe for both full and quantized models
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
        logging_steps=training_config.get("logging_steps", 10),
        save_steps=training_config.get("save_steps", 100),
        save_total_limit=training_config.get("save_total_limit", 2),
        bf16=False,
        fp16=True,
        gradient_checkpointing=training_config.get("gradient_checkpointing", True),
        evaluation_strategy="steps" if eval_dataset else "no",
        eval_steps=training_config.get("eval_steps", 100) if eval_dataset else None,
        report_to="none",
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config")
    args = parser.parse_args()

    print("=" * 60)
    print("Stack 2.9 Simple Training")
    print("=" * 60)

    config = load_config(args.config)
    print(f"Config loaded: {args.config}")
    print(f"Model: {config['model']['name']}")
    print(f"Data: {config['data']['input_path']}")

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
