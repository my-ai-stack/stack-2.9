# Stack 2.9 Training Pipeline

Complete training infrastructure to fine-tune Stack 2.9 (Qwen2.5-Coder-32B) into a super-intelligent coding model.

## Overview

This pipeline provides:

1. **Data Preparation** (`prepare_data.py`) - Load, clean, format, deduplicate, and filter training data
2. **LoRA Training** (`train_lora.py`) - Fine-tune with LoRA adapters
3. **Model Merging** (`merge_adapter.py`) - Merge LoRA weights back to base model
4. **AWQ Quantization** (optional) - Quantize for efficient inference

## Requirements

- Python 3.10+
- CUDA-compatible GPU (recommended)
- 32GB+ VRAM for base model (48GB+ recommended for training)
- 128GB+ system RAM

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete pipeline
./run_training.sh
```

## Individual Steps

### 1. Prepare Data

```bash
python prepare_data.py --config train_config.yaml
```

Features:
- Loads JSONL training data
- Handles multiple formats (messages, instruction/response, prompt/completion)
- Deduplication via content hash
- Quality filtering (min/max length, response presence)
- Tokenization with chat template
- 90/10 train/eval split

### 2. Train LoRA

```bash
python train_lora.py --config train_config.yaml
```

Features:
- 4-bit quantization (bitsandbytes)
- LoRA: r=64, alpha=128
- Target modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
- Gradient checkpointing
- Mixed precision (FP16/BF16)
- wandb/tensorboard logging
- Checkpointing and resume

### 3. Merge Adapter

```bash
python merge_adapter.py --config train_config.yaml
```

Features:
- Merges LoRA into base model
- Exports to HuggingFace format
- Optional AWQ quantization

## Configuration

All hyperparameters are in `train_config.yaml`:

```yaml
# Model
model:
  name: "Qwen/Qwen2.5-Coder-32B"
  torch_dtype: "bfloat16"

# Data
data:
  input_path: "path/to/examples.jsonl"
  max_length: 131072

# LoRA
lora:
  r: 64
  alpha: 128
  target_modules: [...]

# Training
training:
  num_epochs: 3
  batch_size: 1
  gradient_accumulation: 16
  learning_rate: 1.0e-4
```

## File Structure

```
stack-2.9-training/
├── train_config.yaml      # All hyperparameters
├── prepare_data.py      # Data preparation
├── train_lora.py        # LoRA training
├── merge_adapter.py    # Model merging
├── run_training.sh      # One-command pipeline
├── requirements.txt    # Python dependencies
├── data/                # Processed datasets
│   ├── train/
│   └── eval/
└── output/              # Trained models
    ├── stack-2.9-lora/    # LoRA adapter
    ├── stack-2.9-merged/  # Merged model
    └── stack-2.9-awq/     # Quantized model
```

## Hardware Requirements

| Config | GPU VRAM | System RAM | Training Time |
|--------|----------|------------|---------------|
| Minimum | 32GB | 64GB | 12-24h |
| Recommended | 48GB+ | 128GB+ | 6-12h |
| Optimal | 80GB (A100) | 256GB+ | 4-8h |

## Usage After Training

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load quantized model
model = AutoModelForCausalLM.from_pretrained(
    "output/stack-2.9-awq",
    torch_dtype=torch.float16,
    load_in_4bit=True,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")

# Generate
prompt = "Write a Python function to calculate factorial"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
output = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

## Troubleshooting

### Memory Issues
- Reduce `batch_size` in config
- Enable gradient checkpointing
- Use 4-bit quantization

### CUDA Errors
- Verify CUDA drivers: `nvidia-smi`
- Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`

### Data Errors
- Verify JSONL format
- Check required columns: messages OR instruction/response

## License

Provided as-is for educational and research purposes.