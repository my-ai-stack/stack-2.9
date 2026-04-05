# Training Stack 2.9 on Qwen2.5-Coder-7B

## Overview

This guide covers training Stack 2.9 on the Qwen2.5-Coder-7B model using LoRA/QLoRA fine-tuning.

## Hardware Requirements

### Minimum (QLoRA - 4-bit)
| GPU | VRAM | Batch Size | Notes |
|-----|------|-----------|-------|
| T4 (Colab) | 15GB | 1 | Gradient accu = 16 |
| P100 (Kaggle) | 16GB | 1 | Gradient accu = 8 |
| RTX 3090 | 24GB | 2 | Full performance |

### Recommended (Full LoRA - bf16)
| GPU | VRAM | Batch Size | Notes |
|-----|------|-----------|-------|
| A100 40GB | 40GB | 2 | 2x for better throughput |
| A100 80GB | 80GB | 4 | Best for production |
| H100 80GB | 80GB | 4 | Next-gen option |

## VRAM Estimates

| Configuration | Batch Size | Gradient Checkpoint | Est. VRAM |
|--------------|-----------|-------------------|----------|
| Full bf16 | 1 | No | 14GB |
| Full bf16 | 2 | Yes | 16GB |
| Full bf16 | 4 | Yes | 22GB |
| QLoRA (4-bit) | 1 | Yes | 5-6GB |
| QLoRA (4-bit) | 2 | Yes | 7-8GB |

## Quick Start

### Option 1: Kaggle (QLoRA)

```bash
cd /kaggle/working/stack-2.9
chmod +x training-configs/kaggle-7b-qlora.sh
./training-configs/kaggle-7b-qlora.sh
```

### Option 2: Local (Full LoRA)

```bash
cd /path/to/stack-2.9
python train_local.py \
    --config training-configs/7b-lora-config.yaml
```

### Option 3: Custom Training Script

```python
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-7B",
    torch_dtype="bfloat16",
    device_map="auto"
)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                   "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

## Configuration Reference

### LoRA Parameters
```yaml
lora:
  r: 16              # Rank (8-32 recommended for 7B)
  alpha: 32          # Usually 2*r
  dropout: 0.05
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
```

### Training Parameters
```yaml
training:
  num_epochs: 3
  batch_size: 2      # A100: 2-4, T4/P100: 1
  gradient_accumulation: 8
  learning_rate: 1.0e-4
  warmup_steps: 100
  gradient_checkpointing: true
  bf16: true
```

## Expected Training Time

Based on ~10K samples, max_length=4096:

| Hardware | Config | Est. Time |
|----------|--------|----------|
| T4 | 4-bit QLoRA | 4-6 hours |
| P100 | 4-bit QLoRA | 2-3 hours |
| A100 40GB | bf16 LoRA | 30-45 min |
| A100 80GB | bf16 LoRA | 20-30 min |

Times scale linearly with dataset size.

## After Training

### Merge LoRA Adapter

```python
from peft import PeftModel
from transformers import AutoTokenizer

base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-7B",
    torch_dtype="bfloat16"
)

# Merge adapter
model = PeftModel.from_pretrained(base_model, "./output/lora")
merged = model.merge_and_unload()

# Save
merged.save_pretrained("./output/merged")
tokenizer.save_pretrained("./output/merged")
```

### Test the Model

```python
from transformers import AutoTokenizer, pipeline

tokenizer = AutoTokenizer.from_pretrained("./output/merged")
pipe = pipeline("text-generation", model=merged, tokenizer=tokenizer)

result = pipe("def quick_sort(arr):", max_new_tokens=100)
print(result[0]["generated_text"])
```

## Troubleshooting

### OOM (Out of Memory)
- Reduce `batch_size` to 1
- Enable `gradient_checkpointing: true`
- Reduce `max_length` (4096 → 2048)
- Enable 4-bit quantization

### Training Slow
- Increase batch size if VRAM allows
- Enable `use_flash_attention: true` (A100/H100)
- Reduce gradient accumulation

### Loss Not Converging
- Check learning rate (try 5e-5 or 2e-4)
- Increase epochs (3 → 5)
- Verify data format matches expected template

## Alternative: RunPod /cloud Deployment

For faster training, see `runpod_deploy.sh` at repo root.

```bash
# Example: RunPod A100
bash runpod_deploy.sh --gpu a100 --instance $ hourly
```

## Notes

- **A100 recommended**: Best balance of VRAM and speed
- **4-bit QLoRA**: Use only if VRAM < 20GB, slightly reduces quality
- **Gradient checkpointing**: Always enable, minimal perf impact for big memory savings
- **Flash Attention**: A100/H100 only, significant speed boost