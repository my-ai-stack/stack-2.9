import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, HfArgumentParser
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from accelerate import Accelerator
from trl import SFTTrainer
import os
import numpy as np

# Define arguments
class TrainArguments:
    def __init__(self):
        self.model_name = "Qwen/Qwen2.5-Coder-32B"
        self.output_dir = "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-lora"
        self.train_dir = "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/data/train"
        self.eval_dir = "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/data/eval"
        self.learning_rate = 1e-4
        self.num_epochs = 3
        self.batch_size = 1
        self.gradient_accumulation = 16
        self.r = 64
        self.lora_alpha = 128
        self.target_modules = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize arguments
args = TrainArguments()

# Set up accelerator
accelerator = Accelerator()

# Load model in 4-bit with unsloth
if 'unsloth' in sys.modules:
    from unsloth import prepare_model
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        load_in_4bit=True,
        device_map="auto",
        trust_remote_code=True
    )
    base_model = prepare_model(base_model, bf16=True)
else:
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        load_in_4bit=True,
        device_map="auto"
    )

# Setup LoRA configuration
lora_config = LoraConfig(
    r=args.r,
    lora_alpha=args.lora_alpha,
    target_modules=args.target_modules,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(base_model, lora_config)

# Load datasets
train_dataset = load_dataset(args.train_dir)
eval_dataset = load_dataset(args.eval_dir)

# Setup tokenizer
tokenizer = AutoTokenizer.from_pretrained(args.model_name)

# Prepare training
model, train_dataset, eval_dataset, tokenizer = accelerator.prepare(
    model, train_dataset, eval_dataset, tokenizer
)

# Create SFTTrainer
trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    max_seq_length=32768,
    batch_size=args.batch_size,
    gradient_accumulation_steps=args.gradient_accumulation,
    learning_rate=args.learning_rate,
    num_train_epochs=args.num_epochs,
    fp16=True,
    logging_steps=10,
    eval_steps=100,
    save_strategy="epoch",
    output_dir=args.output_dir,
    remove_unused_columns=False,
    report_to=[],
    accelerator=accelerator
)

# Train
print(f"Starting training with LoRA (r={args.r}, alpha={args.lora_alpha})")
print(f"Model: {args.model_name}")
print(f"Output: {args.output_dir}")
print(f"Batch size: {args.batch_size}")
print(f"Gradient accumulation: {args.gradient_accumulation}")
print(f"Learning rate: {args.learning_rate}")
print(f"Epochs: {args.num_epochs}")

model = trainer.train()

# Save final model
trainer.save_model()

print(f"Training completed! Model saved to: {args.output_dir}")
print(f"LoRA weights saved to: {args.output_dir}/adapter_model.bin")