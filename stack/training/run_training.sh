#!/bin/bash
set -e
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9
source .venv/bin/activate

echo "=== Checking PyTorch & MPS ==="
python -c "import torch; print('PyTorch:', torch.__version__); print('MPS:', torch.backends.mps.is_available())"

echo ""
echo "=== Preparing Dataset ==="
python stack-2.9-training/prepare_dataset_local.py

echo ""
echo "=== Starting Training ==="
python stack-2.9-training/train_lora.py --config stack-2.9-training/train_config_local.yaml

echo ""
echo "=== Training Complete ==="