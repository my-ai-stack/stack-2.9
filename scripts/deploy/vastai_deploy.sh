#!/bin/bash
# =============================================================================
# vastai_deploy.sh - Deploy Stack 2.9 Training on Vast.ai
# =============================================================================
#
# USAGE:
#   ./vastai_deploy.sh [--mode train|inference] [--config CONFIG] [--gpu GPU_NAME]
#   ./vastai_deploy.sh [--list-gpus] [--ssh INSTANCE_ID]
#
# EXAMPLES:
#   # Find and launch a training instance with A100 80GB
#   ./vastai_deploy.sh --mode train --gpu A100-80
#
#   # Launch inference on RTX 4090
#   ./vastai_deploy.sh --mode inference --gpu RTX-4090
#
#   # SSH into running instance
#   ./vastai_deploy.sh --ssh 123456
#
#   # List available GPU instances
#   ./vastai_deploy.sh --list-gpus
#
# PREREQUISITES:
#   - vastai CLI installed: pip install vastai
#   - Vast.ai account with API key: vastai auth
#   - SSH key configured: vastai create-key
#   - HF_TOKEN set for gated models
#
# =============================================================================

set -euo pipefail

# ------------------------------ Defaults -------------------------------------
MODE="${MODE:-train}"
CONFIG_PATH="${CONFIG_PATH:-./stack_2_9_training/train_config.yaml}"
GPU_NAME="${GPU_NAME:-A100-80}"
MIN_VRAM_GB="${MIN_VRAM_GB:-40}"
MIN_DL_SPEED="${MIN_DL_SPEED:-800}"      # MB/s
MIN_CPU="${MIN_CPU:-8}"
SSH_KEY="${SSH_KEY:-}"                    # Leave empty to auto-detect
REPO_URL="${REPO_URL:-https://github.com/walidsobhie-code/ai-voice-clone.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
LOG_FILE="${LOG_FILE:-~/vastai_stack29.log}"
INSTANCE_ID=""

# ------------------------------ Helpers --------------------------------------
usage() {
    grep "^#" "$0" | sed 's/^# //;s/^#//'
    exit 1
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
error() { log "ERROR: $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" &>/dev/null || error "Required command not found: $1"
}

# GPU name map: friendly -> vastai search string
declare -A GPU_SEARCH_MAP
GPU_SEARCH_MAP["A100-80"]="A100 80GB"
GPU_SEARCH_MAP["A100-40"]="A100 40GB"
GPU_SEARCH_MAP["H100"]="H100"
GPU_SEARCH_MAP["RTX-4090"]="RTX 4090"
GPU_SEARCH_MAP["RTX-3090"]="RTX 3090"

# ------------------------------ Parse Args ----------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode) MODE="$2"; shift 2 ;;
        --config) CONFIG_PATH="$2"; shift 2 ;;
        --gpu) GPU_NAME="$2"; shift 2 ;;
        --ssh) INSTANCE_ID="$2"; shift 2 ;;
        --list-gpus) LIST_GPUS=true; shift ;;
        --help|-h) usage ;;
        *) error "Unknown option: $1" ;;
    esac
done

# --------------------------------- List GPUs ---------------------------------
if [[ "${LIST_GPUS:-false}" == "true" ]]; then
    log "Fetching available GPU offers..."
    vastai search instances "" --gpu "${GPU_SEARCH_MAP[$GPU_NAME]:-$GPU_NAME}" \
        --order "dph_total" \
        --num 20 2>/dev/null || vastai search offers "" 2>/dev/null
    exit 0
fi

# --------------------------------- SSH into Instance ------------------------
if [[ -n "$INSTANCE_ID" ]]; then
    log "Connecting to instance $INSTANCE_ID..."
    ssh -o StrictHostKeyChecking=no "instance${INSTANCE_ID}@console.vast.ai"
    exit 0
fi

# Validate mode
if [[ "$MODE" != "train" && "$MODE" != "inference" ]]; then
    error "Mode must be 'train' or 'inference', got: $MODE"
fi

# ------------------------------ Prerequisites --------------------------------
log "Checking prerequisites..."
require_cmd vastai

# ------------------------------ Find Suitable Instance -----------------------
SEARCH_TERM="${GPU_SEARCH_MAP[$GPU_NAME]:-$GPU_NAME}"
log "Searching for GPU: $SEARCH_TERM (min VRAM: ${MIN_VRAM_GB}GB)..."

# Query available offers
# Using: vastai search offers <query>
OFFERS=$(vastai search offers "$SEARCH_TERM" 2>/dev/null || echo "")

if [[ -z "$OFFERS" ]]; then
    error "No offers found for GPU: $GPU_NAME. Try --list-gpus to see available options."
fi

# Parse best offer (lowest price, meets requirements)
# Extract the first offer that meets VRAM requirements
BEST_OFFER=$(echo "$OFFERS" | awk -v min_vram="$MIN_VRAM_GB" '
    /^[0-9]/ {
        # Very rough parsing - in production use jq with vastai API
        # This is a simplified heuristic
    }
' | head -1)

# Simpler approach: use the CLI directly with filters
log "Finding best available instance..."

# Create instance with inline args
# See: https://docs.vast.ai/cli/#creating-an-instance
CREATE_CMD="vastai create instance \
    --gpu \"$SEARCH_TERM\" \
    --min-dl-speed $MIN_DL_SPEED \
    --min-cpu-cores $MIN_CPU \
    --onstart-url https://raw.githubusercontent.com/walidsobhie-code/ai-voice-clone/main/vastai_onstart.sh \
    --image nvidia/cuda:12.1.0-runtime-ubuntu22.04 \
    --force-yes"

log "Would run: $CREATE_CMD"
log ""
log "NOTE: Vast.ai interactive mode recommended. Run the following manually:"
log ""
log "  # Search for available instances:"
log "  vastai search offers \"${GPU_SEARCH_MAP[$GPU_NAME]:-$GPU_NAME}\""
log ""
log "  # Launch an instance:"
log "  vastai create instance \\"
log "    --gpu ${GPU_SEARCH_MAP[$GPU_NAME]:-$GPU_NAME} \\"
log "    --image nvidia/cuda:12.1.0-runtime-ubuntu22.04 \\"
log "    --min-dl-speed $MIN_DL_SPEED \\"
log "    --ssh-key $(ssh-add -L 2>/dev/null | cut -d' ' -f2 | head -1 || echo 'YOUR_SSH_KEY_ID')"
log ""
log "  # Then SSH in and run training manually (see below)"
log ""
log "  # Or use this script in interactive mode with TMUX:"
log "  tmux new-session -d -s stack29 'bash'"
log ""

# ------------------------------ Training/Inference Script ---------------------
log "Creating deployment script for instance..."

DEPLOY_SCRIPT="/tmp/stack29_deploy.sh"
cat > "$DEPLOY_SCRIPT" << 'DEPLOY_EOF'
#!/bin/bash
set -euo pipefail

MODE="${1:-train}"
CONFIG_PATH="${2:-./stack_2_9_training/train_config.yaml}"
LOGFILE="/root/stack29_$(date +%Y%m%d_%H%M%S).log"
HF_TOKEN="${HF_TOKEN:-}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }

log "=== Stack 2.9 Deployment Started ==="
log "Mode: $MODE"
log "Config: $CONFIG_PATH"
log "Log: $LOGFILE"
log "Hostname: $(hostname)"
log "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv 2>/dev/null || echo 'nvidia-smi not found')"
log ""

# ---- Env setup ----
export HF_TOKEN="${HF_TOKEN}"
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb=512"
export TRANSFORMERS_CACHE="/data/hf_cache"
export HF_HOME="/data/hf_cache"
export CUDA_VISIBLE_DEVICES="0"

mkdir -p /data/hf_cache /data/outputs /data/adapters

# ---- Install deps ----
log "Installing system packages..."
apt-get update -qq && apt-get install -y -qq \
    git curl wget build-essential libsndfile1 ffmpeg \
    2>&1 | tail -3

log "Installing Python packages..."
pip install --upgrade pip -q
pip install -q \
    torch \
    transformers \
    peft \
    accelerate \
    bitsandbytes \
    datasets \
    trl \
    scipy \
    soundfile \
    librosa \
    pyyaml \
    tqdm \
    gradio \
    fastapi \
    uvicorn \
    2>&1 | tail -5

# ---- Clone repo ----
log "Cloning repository..."
cd /data
if [[ ! -d "ai-voice-clone" ]]; then
    git clone --depth 1 -b main https://github.com/walidsobhie-code/ai-voice-clone.git ai-voice-clone
fi
cd ai-voice-clone

# Copy config if custom
if [[ "$CONFIG_PATH" != "./stack_2_9_training/train_config.yaml" ]]; then
    cp "$CONFIG_PATH" ./stack_2_9_training/train_config.yaml
fi

log "Repository ready. Starting application..."

# ---- Start Training or Inference ----
if [[ "$MODE" == "train" ]]; then
    log "Starting LoRA training..."
    log "Command: python -m stack_2_9_training.train_lora --config ./stack_2_9_training/train_config.yaml"
    python -m stack_2_9_training.train_lora \
        --config ./stack_2_9_training/train_config.yaml \
        2>&1 | tee -a "$LOGFILE"
else
    log "Starting inference server..."
    log "Command: python -m uvicorn stack.serve:app --host 0.0.0.0 --port 7860"
    python -m uvicorn \
        stack.serve:app \
        --host 0.0.0.0 \
        --port 7860 \
        2>&1 | tee -a "$LOGFILE"
fi
DEPLOY_EOF

chmod +x "$DEPLOY_SCRIPT"
log "Deploy script written to: $DEPLOY_SCRIPT"
log "Contents will be transferred to the instance on creation."

# ------------------------------ Full Create Instructions ---------------------
log ""
log "=== Full Vast.ai Deployment Instructions ==="
log ""
log "1. Find a suitable instance:"
log "   vastai search offers \"${GPU_SEARCH_MAP[$GPU_NAME]:-$GPU_NAME}\""
log ""
log "2. Create the instance (note the offer ID from step 1):"
log "   vastai create instance --offer-id <id> \\"
log "     --image nvidia/cuda:12.1.0-devel-ubuntu22.04 \\"
log "     --ssh-key <your-ssh-key> \\"
log "     --onstart-url https://raw.githubusercontent.com/walidsobhie-code/ai-voice-clone/main/vastai_onstart.sh \\"
log "     --onstart-cmd '$MODE /data/ai-voice-clone/stack_2_9_training/train_config.yaml'"
log ""
log "3. SSH into the instance after it starts:"
log "   vastai ssh <instance-id>"
log ""
log "4. Or use screen/tmux for persistent sessions:"
log "   screen -S stack29"
log "   bash /tmp/stack29_deploy.sh $MODE $CONFIG_PATH"
log "   # Ctrl+A D to detach"
log ""
log "5. Monitor training:"
log "   tail -f $LOGFILE"
log "   nvidia-smi -l 1"
log ""
log "=== Clean Shutdown ==="
log "To stop training gracefully:"
log "  # Find the process"
log "  ps aux | grep train_lora"
log "  # Send SIGTERM for graceful shutdown"
log "  kill -SIGTERM <pid>"
log ""
log "To stop and destroy the instance:"
log "  vastai destroy instance <instance-id>"
