#!/bin/bash
# Stack 2.9 Local Training Setup Script

set -e

cd /Users/walidsobhi/.openclaw/workspace/stack-2.9

echo "=== Step 1: Verify venv ==="
source .venv/bin/activate
python -c "import torch; print('PyTorch:', torch.__version__)"
echo "MPS available: $(python -c 'import torch; print(torch.backends.mps.is_available())')"

echo ""
echo "=== Step 2: Export Qwen model from Ollama ==="
# This creates ./base_model_qwen7b from Ollama
mkdir -p ./base_model_qwen7b
ollama cp qwen2.5-coder:7b qwen2.5-coder:7b-local
# Export won't work directly, so we'll download from HF instead

echo ""
echo "=== Step 3: Download model from HuggingFace ==="
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
print('Downloading Qwen2.5-Coder-7B...')
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-Coder-7B', trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-Coder-7B', trust_remote_code=True)
tokenizer.save_pretrained('./base_model_qwen7b')
model.save_pretrained('./base_model_qwen7b')
print('Model saved to ./base_model_qwen7b')
"

echo ""
echo "=== Step 4: Prepare dataset ==="
# Convert JSONL to training format
python stack-2.9-training/prepare_dataset.py --input training-data/generated/synthetic_50k.jsonl

echo ""
echo "=== Step 5: Run training ==="
python stack-2.9-training/train_lora.py --config stack-2.9-training/train_config_local.yaml