#!/bin/bash
# Deploy Stack 2.9 to RunPod
# Requires: runpodctl installed and configured

set -e

echo "🚀 Deploying Stack 2.9 to RunPod"
echo "================================"
echo ""

# Check prerequisites
if ! command -v runpodctl &> /dev/null; then
    echo "❌ runpodctl not found. Install from: https://github.com/runpod/runpodctl"
    exit 1
fi

# Configuration
IMAGE="docker.io/library/pytorch:2.1.0-cuda11.8-cudnn8-runtime"
TEMPLATE_NAME="stack-2.9-template"
CONTAINER_NAME="stack-2.9-server"
GPU_TYPE="NVIDIA RTX A6000"
DISK_SIZE=50

echo "📋 Configuration:"
echo "  GPU: $GPU_TYPE"
echo "  Disk: ${DISK_SIZE}GB"
echo "  Image: $IMAGE"
echo ""

# Step 1: Create template (one-time)
echo "📦 Creating RunPod template..."
runpodctl create template \
  --name "$TEMPLATE_NAME" \
  --image "$IMAGE" \
  --docker-run-args "--gpus all -e VLLM_MODEL=/workspace/models/stack-2.9-awq -p 8000:8000" \
  --volume "/workspace/models:/workspace/models" \
  --volume "/workspace/output:/workspace/output" || echo "Template may already exist"

# Step 2: Deploy pod/container
echo "☁️  Deploying pod..."
POD_ID=$(runpodctl create pod \
  --name "$CONTAINER_NAME" \
  --gpu-type "$GPU_TYPE" \
  --disk-size "$DISK_SIZE" \
  --template "$TEMPLATE_NAME" \
  --env "VLLM_MODEL=/workspace/models/stack-2.9-awq" \
  --env "VLLM_PORT=8000" \
  --port 8000 \
  --query id)

echo "✅ Pod created: $POD_ID"
echo "  Waiting for startup..."
sleep 60

# Step 3: Copy model and code
echo "📤 Copying model and code to pod..."
tar czf /tmp/stack-2.9-deployment.tar.gz \
  stack-2.9-deploy/ \
  stack-2.9-voice/ \
  training-data/ \
  requirements.txt \
  Makefile 2>/dev/null || true

runpodctl cp /tmp/stack-2.9-deployment.tar.gz $POD_ID:/workspace/
runpodctl ssh $POD_ID "tar xzf /workspace/stack-2.9-deployment.tar.gz -C /workspace/"

# Step 4: Install dependencies and start services
echo "🔧 Setting up on pod..."
runpodctl ssh $POD_ID << 'EOF'
cd /workspace

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download model if not present (skipped if using pre-uploaded)
if [ ! -d "models/stack-2.9-awq" ]; then
    echo "Model not found in pod. You need to upload it separately or download via HF."
    echo "Consider uploading model to S3 and downloading in this step."
fi

# Start vLLM
echo "Starting vLLM server..."
nohup python stack-2.9-deploy/vllm_server.py &
EOF

# Step 5: Get public URL
PUBLIC_URL=$(runpodctl get pod $POD_ID --query "url" --output text)
echo ""
echo "✅ Deployment complete!"
echo "  Pod ID: $POD_ID"
echo "  vLLM API: http://$PUBLIC_URL:8000"
echo "  Health: http://$PUBLIC_URL:8000/health"
echo ""
echo "To view logs: runpodctl logs $POD_ID"
echo "To stop: runpodctl delete pod $POD_ID"