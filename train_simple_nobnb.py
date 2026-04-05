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
        # No quantization - load in fp16 for Kaggle T4/P100 (bf16 not supported)
        # Model dtype MUST match training dtype to avoid GradScaler conflicts
        load_dtype = torch.float16 if use_fp16 else torch.bfloat16
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=load_dtype,
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
    """Load and tokenize dataset."""
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
        logging_steps=training_config.get("logging_steps", 10),
        save_steps=training_config.get("save_steps", 100),
        save_total_limit=training_config.get("save_total_limit", 2),
        bf16=use_bf16,
        fp16=use_fp16,
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
