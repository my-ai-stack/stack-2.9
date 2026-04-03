#!/bin/bash
# =============================================================================
# runpod_deploy.sh - Deploy Stack 2.9 Training on RunPod
# =============================================================================
#
# USAGE:
#   ./runpod_deploy.sh [--mode train|inference] [--config CONFIG_PATH] [--gpu GPU_TYPE]
#
# EXAMPLES:
#   # Start training on an A100 80GB
#   ./runpod_deploy.sh --mode train --gpu A100-80
#
#   # Start inference server on a smaller GPU
#   ./runpod_deploy.sh --mode inference --gpu A100-40
#
#   # Use custom config
#   ./runpod_deploy.sh --mode train --config ./my_config.yaml
#
# PREREQUISITES:
#   - RunPod CLI installed: https://docs.runpod.io/cli/install
#   - RunPod account with API key set: runpod config
#   - HF_TOKEN set for gated models (Qwen)
#
# =============================================================================

set -euo pipefail

# ------------------------------ Defaults -------------------------------------
MODE="${MODE:-train}"
GPU_TYPE="${GPU_TYPE:-A100-80}"
CONFIG_PATH="${CONFIG_PATH:-./stack_2_9_training/train_config.yaml}"
HF_TOKEN="${HF_TOKEN:-}"
OUTPUT_DIR="${OUTPUT_DIR:-./stack-2.9}"
CONTAINER_DISK_SIZE="${CONTAINER_DISK_SIZE:-200}"
MIN_VRAM_GB="${MIN_VRAM_GB:-80}"
REPO_URL="${REPO_URL:-https://github.com/walidsobhie-code/ai-voice-clone.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

# ------------------------------ Helpers --------------------------------------
usage() {
    grep "^#" "$0" | sed 's/^# //;s/^#//'
    exit 1
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
error() { log "ERROR: $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" &>/dev/null || error "Required command not found: $1. Install it first."
}

# ------------------------------ Parse Args ----------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode) MODE="$2"; shift 2 ;;
        --config) CONFIG_PATH="$2"; shift 2 ;;
        --gpu) GPU_TYPE="$2"; shift 2 ;;
        --help|-h) usage ;;
        *) error "Unknown option: $1" ;;
    esac
done

# Validate mode
if [[ "$MODE" != "train" && "$MODE" != "inference" ]]; then
    error "Mode must be 'train' or 'inference', got: $MODE"
fi

# ------------------------------ Prerequisites --------------------------------
log "Checking prerequisites..."
require_cmd runpod

# Check HF_TOKEN
if [[ -z "$HF_TOKEN" ]]; then
    log "WARNING: HF_TOKEN not set. Some models may fail to download."
    log "Set it with: export HF_TOKEN=your_token_here"
fi

# --------------------------------- GPU Selection ----------------------------
# Map friendly names to RunPod GPU IDs
declare -A GPU_MAP
GPU_MAP["A100-80"]="NVIDIA-A100-80GB"
GPU_MAP["A100-40"]="NVIDIA-A100-40GB"
GPU_MAP["A6000"]="NVIDIA-RTX-A6000"
GPU_MAP["4090"]="NVIDIA-RTX-4090"
GPU_MAP["3090"]="NVIDIA-RTX-3090"

GPU_ID="${GPU_MAP[$GPU_TYPE]:-$GPU_TYPE}"

log "Selected GPU: $GPU_TYPE (RunPod ID: $GPU_ID)"

# ------------------------------ Detect GPU Availability ----------------------
log "Checking GPU availability on RunPod..."

# Find available pod templates with the requested GPU
AVAILABLE_GPUS=$(runpod list gpus 2>/dev/null | grep -c "$GPU_ID" || echo "0")
if [[ "$AVAILABLE_GPUS" == "0" ]]; then
    log "WARNING: GPU $GPU_ID may not be available. Proceeding anyway..."
fi

# ------------------------------ Build Docker Command ------------------------
log "Building docker run command..."

# Base environment variables
ENV_VARS=(
    "HF_TOKEN=${HF_TOKEN}"
    "PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb=512"
    "TRANSFORMERS_CACHE=/data/hf_cache"
    "HF_HOME=/data/hf_cache"
)

# Build env string
ENV_STRING=""
for var in "${ENV_VARS[@]}"; do
    if [[ "$var" == "${var%=*}" ]]; then continue; fi  # skip if no '='
    KEY="${var%%=*}"
    VAL="${var#*=}"
    ENV_STRING+=" -e ${KEY}=${VAL}"
done

# Mount data volume for models and outputs
VOLUME_MOUNTS="-v /data:/data"

# Training command
if [[ "$MODE" == "train" ]]; then
    CMD="python -m stack_2_9_training.train_lora \
        --config ${CONFIG_PATH}"
    CONTAINER_PORT=""
else
    # Inference mode - start Gradio server
    CMD="python -m uvicorn stack.serve:app \
        --host 0.0.0.0 \
        --port 7860"
    CONTAINER_PORT="-p 7860:7860"
fi

# ------------------------------ Launch on RunPod -----------------------------
log "Launching RunPod instance..."

# Check if user wants interactive or one-liner
if [[ -t 0 ]]; then
    log "Interactive mode - will print the docker command for manual run:"
    echo ""
    echo "runpod run --gpu ${GPU_ID} \\"
    echo "  --container-disk-size ${CONTAINER_DISK_SIZE} \\"
    echo "  ${ENV_STRING} \\"
    echo "  ${VOLUME_MOUNTS} \\"
    echo "  ${CONTAINER_PORT} \\"
    echo "  -- python /app/entrypoint.sh"
    echo ""
    echo "Recommended: Use runpod CLI with a template instead."
    echo "See: https://docs.runpod.io/cli/templates"
else
    # Non-interactive: use runpod run
    runpod run \
        --gpu "$GPU_ID" \
        --container-disk-size "$CONTAINER_DISK_SIZE" \
        docker \
        bash -c "
            set -e
            echo '=== Starting Stack 2.9 Deployment ==='
            echo 'Mode: $MODE'
            echo 'GPU: $GPU_ID'
            echo ''
            echo '=== Installing dependencies ==='
            pip install --no-cache-dir \
                torch \
                transformers \
                peft \
                accelerate \
                bitsandbytes \
                datasets \
                trl \
                pyyaml \
                tqdm \
                gradio \
                fastapi \
                uvicorn 2>&1 | tail -5
            echo ''
            echo '=== Cloning repository ==='
            git clone --depth 1 -b $REPO_BRANCH $REPO_URL /app 2>/dev/null || echo 'Repo already present'
            cd /app
            echo ''
            echo '=== Starting application ==='
            $CMD
        "
fi

# ------------------------------ Post-Launch --------------------------------
log "Done. To check your pod status:"
log "  runpod ps"
log ""
log "To stream logs:"
log "  runpod logs <pod-id>"
log ""
log "To SSH into the instance:"
log "  runpod ssh <pod-id>"

# ------------------------------ Cleanup Hint ---------------------------------
log ""
log "To stop and remove the instance:"
log "  runpod stop <pod-id> && runpod rm <pod-id>"
