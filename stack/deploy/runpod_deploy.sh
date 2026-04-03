#!/bin/bash
# Deploy Stack 2.9 to RunPod
# Requires: runpodctl installed and configured

set -euo pipefail

echo "🚀 Deploying Stack 2.9 to RunPod"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration (can be overridden by environment variables)
IMAGE="${RUNPOD_IMAGE:-docker.io/library/pytorch:2.1.0-cuda11.8-cudnn8-runtime}"
TEMPLATE_NAME="${RUNPOD_TEMPLATE_NAME:-stack-2.9-template}"
CONTAINER_NAME="${RUNPOD_CONTAINER_NAME:-stack-2.9-server}"
GPU_TYPE="${RUNPOD_GPU_TYPE:-NVIDIA RTX A6000}"
DISK_SIZE="${RUNPOD_DISK_SIZE:-50}"
MODEL_PATH="${MODEL_PATH:-/workspace/models/stack-2.9-awq}"
VLLM_PORT="${VLLM_PORT:-8000}"

# Check prerequisites
command -v runpodctl >/dev/null 2>&1 || {
    echo -e "${RED}❌ runpodctl not found. Install from: https://github.com/runpod/runpodctl${NC}"
    exit 1
}

echo "📋 Configuration:"
echo "  GPU: $GPU_TYPE"
echo "  Disk: ${DISK_SIZE}GB"
echo "  Image: $IMAGE"
echo "  Model path: $MODEL_PATH"
echo ""

# Step 1: Create template (one-time, may already exist)
echo "📦 Creating/verifying RunPod template..."
if ! runpodctl get template "$TEMPLATE_NAME" &>/dev/null; then
    runpodctl create template \
      --name "$TEMPLATE_NAME" \
      --image "$IMAGE" \
      --docker-run-args "--gpus all -e MODEL_PATH=$MODEL_PATH -e VLLM_PORT=$VLLM_PORT -p $VLLM_PORT:8000" \
      --volume "/workspace/models:$MODEL_PATH:ro" \
      --volume "/workspace/output:/workspace/output" \
      --container-disk-size "${DISK_SIZE}GB"
    echo -e "${GREEN}✅ Template created${NC}"
else
    echo -e "${YELLOW}⚠️  Template already exists, using existing${NC}"
fi

# Step 2: Deploy pod
echo "☁️  Deploying pod..."
POD_ID=$(runpodctl create pod \
  --name "$CONTAINER_NAME" \
  --gpu-type "$GPU_TYPE" \
  --disk-size "${DISK_SIZE}GB" \
  --template "$TEMPLATE_NAME" \
  --env "MODEL_PATH=$MODEL_PATH" \
  --env "VLLM_PORT=$VLLM_PORT" \
  --port "$VLLM_PORT" \
  --query id)

echo -e "${GREEN}✅ Pod created: $POD_ID${NC}"
echo "  Waiting for startup (this may take 2-3 minutes for first-time model load)..."
sleep 60

# Step 3: Copy deployment files
echo "📤 Copying code to pod..."
# Create deployment package
TEMP_PACKAGE="/tmp/stack-2.9-deployment-$(date +%s).tar.gz"
tar czf "$TEMP_PACKAGE" \
  stack-2.9-deploy/ \
  requirements.txt \
  2>/dev/null || {
    echo -e "${RED}❌ Failed to create deployment package${NC}"
    exit 1
}

# Copy to pod
if ! runpodctl cp "$TEMP_PACKAGE" "$POD_ID:/workspace/" ; then
    echo -e "${RED}❌ Failed to copy package to pod${NC}"
    exit 1
fi

# Extract and setup
echo "🔧 Setting up on pod..."
runpodctl ssh "$POD_ID" bash -c "'
set -euo pipefail
cd /workspace
tar xzf stack-2.9-*.tar.gz

# Install system dependencies
apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install requirements
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

# Check if model exists
if [ ! -d \"$MODEL_PATH\" ] || [ -z \"$(ls -A $MODEL_PATH 2>/dev/null)\" ]; then
    echo \"⚠️  Model not found at $MODEL_PATH\"
    echo \"   You have two options:\"
    echo \"   1. Upload your model to: $MODEL_PATH\"\n    echo \"   2. Set MODEL_PATH to a HuggingFace model name and it will be downloaded\"\n    echo \"   Example: export MODEL_PATH=meta-llama/Llama-3.1-8B-Instruct\"\n    echo \"   Note: Downloading large models may take hours and exceed pod disk space.\"\n    echo \"   Recommendation: Upload AWQ-quantized model to S3 and download it.\"\nfi

echo \"Starting vLLM server...\"
cd /workspace/stack-2.9-deploy
nohup python vllm_server.py > vllm.log 2>&1 &
echo \$! > /tmp/vllm.pid
'" || {
    echo -e "${RED}❌ Failed to setup pod${NC}"
    exit 1
}

# Step 4: Wait and check status
echo "⏳ Waiting for vLLM server to start..."
sleep 30

# Get pod status
echo ""
echo "📊 Pod status:"
runpodctl get pod "$POD_ID"

# Get public URL
PUBLIC_URL=$(runpodctl get pod "$POD_ID" --query "url" --output text 2>/dev/null || echo "pending")

echo ""
echo -e "${GREEN}✅ Deployment initiated!${NC}"
echo "  Pod ID: $POD_ID"
echo "  vLLM API: http://$PUBLIC_URL:8000"
echo "  Health: http://$PUBLIC_URL:8000/health"
echo ""
echo "📋 To monitor:"
echo "  runpodctl logs $POD_ID            # View logs"
echo "  runpodctl ssh $POD_ID            # SSH into pod"
echo "  runpodctl stop pod $POD_ID       # Stop (saves disk)"
echo "  runpodctl delete pod $POD_ID     # Delete (you lose data)"
echo ""
echo -e "${YELLOW}⚠️  First server startup may take 5-15 minutes as the model loads${NC}"
echo -e "${YELLOW}⚠️  Monitor logs: runpodctl logs $POD_ID${NC}"
