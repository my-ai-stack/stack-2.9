#!/bin/bash
# Deploy Stack 2.9 to Vast.ai
# Requires: vastai CLI installed and configured

set -euo pipefail

echo "🚀 Deploying Stack 2.9 to Vast.ai"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
MODEL_PATH="${MODEL_PATH:-/workspace/models/stack-2.9-awq}"
VLLM_PORT="${VLLM_PORT:-8000}"
MIN_GPU_RAM="${VAST_GPU_RAM:-16}"  # GB
MIN_CUDA="${VAST_CUDA_VERSION:-11.8}"
SEARCH_LIMIT="${VAST_SEARCH_LIMIT:-10}"

# Check prerequisites
if ! command -v vastai &> /dev/null; then
    echo -e "${RED}❌ vastai CLI not found. Install from: https://vast.ai/docs/cli${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq is required but not installed. Install: apt-get install jq / brew install jq${NC}"
    exit 1
fi

# Verify authentication
if ! vastai whoami &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with Vast.ai. Run: vastai login${NC}"
    exit 1
fi

echo "🔍 Searching for suitable instance..."
echo "  Requirements: GPU RAM ≥ ${MIN_GPU_RAM}GB, CUDA ≥ ${MIN_CUDA}"

# Build search query
SEARCH_QUERY="cuda>=${MIN_CUDA} gpu_ram>=${MIN_GPU_RAM} gpu_name!='A100-80GB'"
# Exclude A100-80GB unless explicitly needed (too expensive)

# Search for offers
SEARCH_RESULT=$(vastai search offers "$SEARCH_QUERY" --sort "dpkwh" --encoding json --limit "$SEARCH_LIMIT" 2>/dev/null || echo "[]")

if [ "$SEARCH_RESULT" = "[]" ]; then
    echo -e "${YELLOW}⚠️  No instances found with criteria. Trying with lower GPU RAM...${NC}"
    SEARCH_RESULT=$(vastai search offers "cuda>=${MIN_CUDA} gpu_ram>=8" --sort "dpkwh" --encoding json --limit "$SEARCH_LIMIT" 2>/dev/null || echo "[]")
fi

INSTANCE_ID=$(echo "$SEARCH_RESULT" | jq -r '.[0].id // empty' 2>/dev/null || true)

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}❌ No suitable instance found. Try adjusting search criteria (VAST_GPU_RAM).${NC}"
    echo "   Available instances:"
    vastai search offers "cuda>=${MIN_CUDA}" --sort "dpkwh" --limit 5
    exit 1
fi

echo -e "${GREEN}✅ Found instance: $INSTANCE_ID${NC}"

# Get instance details
echo "📋 Instance details:"
vastai show instance "$INSTANCE_ID" --encoding json | jq -r '
  .gpu_name + " (" + (.gpu_ram/1024 | tostring) + "GB) - $" + (.dpkwh | tostring) + "/hr"'
echo ""

# Confirm deployment
read -p "Deploy this instance? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Start the instance
echo "🚀 Starting instance..."
if ! vastai start instance "$INSTANCE_ID"; then
    echo -e "${RED}❌ Failed to start instance${NC}"
    exit 1
fi

echo "  Waiting for instance to be ready (2-3 minutes)..."
sleep 90

# Get connection info
INSTANCE_INFO=$(vastai show instance "$INSTANCE_ID" --encoding json)
SSH_PORT=$(echo "$INSTANCE_INFO" | jq -r '.ssh_port // "22"')
SSH_HOST=$(echo "$INSTANCE_INFO" | jq -r '.ssh_host // empty')
PUBLIC_IP=$(echo "$INSTANCE_INFO" | jq -r '.public_ipaddr // empty')

if [ -z "$SSH_HOST" ] || [ "$SSH_HOST" = "null" ]; then
    echo -e "${YELLOW}⚠️  SSH host not ready yet, waiting longer...${NC}"
    sleep 30
    INSTANCE_INFO=$(vastai show instance "$INSTANCE_ID" --encoding json)
    SSH_HOST=$(echo "$INSTANCE_INFO" | jq -r '.ssh_host // empty')
fi

echo ""
echo "📋 Instance details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  SSH: ssh -p $SSH_PORT vastai_ssh@$SSH_HOST"
echo "  Public IP: $PUBLIC_IP"
echo ""

# Create deployment package
TEMP_PACKAGE="/tmp/stack-2.9-deployment-$(date +%s).tar.gz"
echo "📦 Creating deployment package..."
tar czf "$TEMP_PACKAGE" \
  stack-2.9-deploy/ \
  requirements.txt \
  2>/dev/null || {
    echo -e "${RED}❌ Failed to create deployment package${NC}"
    exit 1
}

# Copy code to instance
echo "📤 Copying code to instance..."
if ! scp -P "$SSH_PORT" \
    "$TEMP_PACKAGE" \
    "vastai_ssh@$SSH_HOST:/workspace/" ; then
    echo -e "${RED}❌ Failed to copy package${NC}"
    echo "   SSH connection details: ssh -p $SSH_PORT vastai_ssh@$SSH_HOST"
    exit 1
fi

# Setup on remote
echo "🔧 Setting up on remote instance..."
ssh -p "$SSH_HOST" vastai_ssh@$SSH_HOST bash -c "'
set -euo pipefail
cd /workspace

echo \"Extracting package...\"
tar xzf stack-2.9-*.tar.gz

# Install system dependencies
echo \"Installing system packages...\"
apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
python3 -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo \"Installing Python requirements...\"
python3 -m pip install -r requirements.txt

# Model handling
echo \"Checking model at $MODEL_PATH...\"
if [ ! -d \"$MODEL_PATH\" ] || [ -z \"$(ls -A $MODEL_PATH 2>/dev/null)\" ]; then
    echo \"⚠️  Model not found at $MODEL_PATH\"
    echo \"   Options:\"
    echo \"   1. Upload model manually to: $MODEL_PATH\"\n    echo \"   2. Set MODEL_PATH to a HF model for download (may be slow)\"\nfi

# Create logs directory
mkdir -p /workspace/logs

# Start vLLM server
echo \"Starting vLLM server...\"
cd /workspace/stack-2.9-deploy
nohup python vllm_server.py > /workspace/vllm.log 2>&1 &
echo \$! > /tmp/vllm.pid

echo \"Server started with PID \$(cat /tmp/vllm.pid)\"
'" || {
    echo -e "${RED}❌ Failed to setup instance${NC}"
    exit 1
}

# Wait and test
echo ""
echo "⏳ Waiting for server to initialize (may take several minutes)..."
sleep 45

# Test connection
echo "🔍 Testing server health..."
if ssh -p "$SSH_PORT" vastai_ssh@$SSH_HOST "curl -f http://localhost:$VLLM_PORT/health &>/dev/null" 2>/dev/null; then
    echo -e "${GREEN}✅ Server is running and healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Server is starting but health check not yet ready${NC}"
    echo "   Check logs: ssh -p $SSH_PORT vastai_ssh@$SSH_HOST 'tail -f /workspace/vllm.log'"
fi

echo ""
echo -e "${GREEN}✅ Deployment initiated!${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  SSH: ssh -p $SSH_PORT vastai_ssh@$SSH_HOST"
echo "  vLLM API: http://$PUBLIC_IP:$VLLM_PORT (if port forwarded)"
echo "  Logs: ssh vastai_ssh@$SSH_HOST 'tail -f /workspace/vllm.log'"
echo ""
echo -e "${YELLOW}⚠️  Vast.ai charges by the hour. Remember to stop when done:${NC}"
echo "  vastai stop instance $INSTANCE_ID"
echo ""
echo "📋 Useful commands:"
echo "  vastai show instance $INSTANCE_ID     # Instance details"
echo "  vastai logs $INSTANCE_ID            # View logs (if supported)"
echo "  vastai instances                    # List your instances"
echo "  vastai marketplace                 # Browse available instances"
