#!/bin/bash
# Deploy Stack 2.9 to Vast.ai
# Requires: vastai CLI installed and configured

set -e

echo "🚀 Deploying Stack 2.9 to Vast.ai"
echo "================================"
echo ""

# Check prerequisites
if ! command -v vastai &> /dev/null; then
    echo "❌ vastai CLI not found. Install from: https://vast.ai/docs/cli"
    exit 1
fi

# Configuration - find a suitable GPU instance
echo "🔍 Searching for suitable instance..."
# Use a search query to find GPU with enough memory (A6000 or A100)
SEARCH_RESULT=$(vastai search offers "gpu_name>=A6000 cuda>=11.8 gpu_ram>=20" --sort "dpkwh" --limit 1)

if [ -z "$SEARCH_RESULT" ]; then
    echo "⚠️  No A6000 found, trying broader search..."
    SEARCH_RESULT=$(vastai search offers "cuda>=11.8 gpu_ram>=16" --sort "dpkwh" --limit 1)
fi

INSTANCE_ID=$(echo "$SEARCH_RESULT" | jq -r '.id' | head -1)

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo "❌ No suitable instance found. Try adjusting search criteria."
    exit 1
fi

echo "✅ Found instance: $INSTANCE_ID"
echo "  Starting instance..."

# Start the instance
vastai start instance $INSTANCE_ID

# Wait for startup
echo "  Waiting for instance to be ready..."
sleep 60

# Get connection info
echo "📋 Instance details:"
vastai show instance $INSTANCE_ID

# Copy code to instance
echo "📤 Copying code to instance..."
scp -r \
  stack-2.9-deploy/ \
  stack-2.9-voice/ \
  training-data/ \
  requirements.txt \
  Makefile \
  vastai_ssh:$INSTANCE_ID:/workspace/

# Setup on remote
echo "🔧 Setting up on remote instance..."
ssh vastai_ssh:$INSTANCE_ID << 'EOF'
cd /workspace

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download model (or upload separately)
if [ ! -d "models/stack-2.9-awq" ]; then
    echo "Model not found. Downloading from Hugging Face..."
    huggingface-cli download your-username/stack-2.9-awq --local-dir models/stack-2.9-awq
fi

# Start vLLM server
echo "Starting vLLM server..."
nohup python stack-2.9-deploy/vllm_server.py > server.log 2>&1 &
EOF

# Get public URL (usually the SSH tunnel or HTTP endpoint)
echo ""
echo "✅ Deployment complete!"
echo "  Instance ID: $INSTANCE_ID"
echo "  To connect: ssh vastai_ssh:$INSTANCE_ID"
echo "  To view logs: ssh vastai_ssh:$INSTANCE_ID 'tail -f /workspace/server.log'"
echo ""
echo "⚠️  Reminder: Vast.ai charges per hour. Stop when done:"
echo "  vastai stop instance $INSTANCE_ID"