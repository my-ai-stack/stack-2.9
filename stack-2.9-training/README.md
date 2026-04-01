# Stack 2.9 Training Pipeline

This repository contains a complete training pipeline for Stack 2.9, including data preparation, LoRA training, model merging, and AWQ quantization.

## Overview

1. **Data Preparation**: Converts synthetic examples to HuggingFace Dataset format
2. **LoRA Training**: Fine-tunes Qwen2.5-Coder-32B with LoRA
3. **Model Merging**: Merges LoRA weights back to base model
4. **AWQ Quantization**: Quantizes model for efficient inference

## Requirements

- Python 3.8+
- CUDA-compatible GPU (recommended)
- At least 32GB VRAM for base model
- Recommended: 48GB+ VRAM for training

## Installation

```bash
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9-training
pip install -r requirements.txt
```

## Data Preparation

```bash
python prepare_dataset.py
```

This script:
- Loads training data from `/Users/walidsobhi/.openclaw/workspace/training-data/synthetic/examples.jsonl`
- Applies chat template using Qwen2 tokenizer
- Tokenizes with max_length=131072
- Splits into 90% train / 10% eval
- Saves to `data/train.parquet` and `data/eval.parquet`

## Training with LoRA

```bash
python train_lora.py
```

Training configuration:
- Model: Qwen/Qwen2.5-Coder-32B
- Precision: 4-bit (bitsandbytes/unsloth)
- LoRA: r=64, alpha=128
- Target modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
- Batch size: 1 (gradient accumulation: 16)
- Learning rate: 1e-4
- Epochs: 3
- Output: `output/stack-2.9-lora/`

## Merging LoRA Weights

```bash
python merge_lora.py
```

This merges the trained LoRA adapter back into the base model and saves to:
- `output/stack-2.9-merged/`

## AWQ Quantization

```bash
python quantize_awq.py
```

This applies AWQ 4-bit quantization for efficient inference and saves to:
- `output/stack-2.9-awq/`

## Complete Training Pipeline

Run the full pipeline with:

```bash
./run_training.sh
```

## File Structure

```
stack-2.9-training/
├── requirements.txt          # Python dependencies
├── prepare_dataset.py       # Data preparation script
├── train_lora.py           # LoRA training script
├── merge_lora.py           # Model merging script
├── quantize_awq.py         # AWQ quantization script
├── run_training.sh         # Complete pipeline script
├── README.md               # This file
├── data/                   # Processed datasets
│   ├── train/              # Training data
│   └── eval/               # Evaluation data
└── output/                 # Trained models
    ├── stack-2.9-lora/      # LoRA trained model
    ├── stack-2.9-merged/    # Merged model
    └── stack-2.9-awq/       # Quantized model
```

## Hardware Requirements

### Minimum
- GPU: 32GB VRAM
- CPU: 8+ cores
- RAM: 64GB+ system memory

### Recommended
- GPU: 48GB+ VRAM (A100, H100, or multiple 24GB cards)
- CPU: 16+ cores
- RAM: 128GB+ system memory
- Storage: 1TB+ NVMe SSD

## Training Time Estimates

- Data preparation: 5-10 minutes
- LoRA training: 8-12 hours (depends on GPU)
- Model merging: 2-5 minutes
- AWQ quantization: 10-30 minutes

## Usage

After training, use the quantized model for inference:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-awq",
    torch_dtype=torch.float16,
    load_in_4bit=True,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")

# Generate
prompt = "Write a Python function to calculate factorial"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
output = model.generate(**inputs, max_new_tokens=512)
result = tokenizer.decode(output[0], skip_special_tokens=True)
print(result)
```

## Troubleshooting

### Memory Issues
- Reduce `gradient_accumulation` in `train_lora.py`
- Use CPU offloading: `device_map="auto", offload_dir="/tmp/offload"`
- Train with smaller batch sizes

### CUDA Errors
- Ensure CUDA drivers are up to date
- Check GPU memory with `nvidia-smi`
- Reduce model precision if needed

### Dataset Errors
- Verify `examples.jsonl` exists at the specified path
- Check JSON format is correct
- Ensure required columns are present

### Installation Issues
- Use Python 3.8+ environment
- Install PyTorch with CUDA support
- Check system dependencies (cmake, g++)

## Performance Tips

1. **Gradient Accumulation**: Use higher values for better GPU utilization
2. **Mixed Precision**: 4-bit quantization reduces memory usage significantly
3. **Data Loading**: Use `num_proc` for faster dataset loading
4. **Checkpointing**: Save intermediate checkpoints during training
5. **Evaluation**: Monitor validation loss to prevent overfitting

## License

This training pipeline is provided as-is for educational and research purposes.

## Support

For issues with the training pipeline, check:
1. Console error messages
2. GPU memory usage
3. Dataset format
4. Python environment

## Changelog

- v1.0: Initial release with complete training pipeline