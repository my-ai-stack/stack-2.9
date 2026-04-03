#!/bin/bash
set -e

# Stack 2.9 vLLM Startup Script
# Handles proper startup, logging, and signal handling

echo "🚀 Starting Stack 2.9 vLLM Server"
echo "================================"

# Configuration
LOG_DIR="/app/logs"
PID_FILE="/app/vllm.pid"
LOG_FILE="${LOG_DIR}/vllm.log"

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down vLLM server..."
    if [ -f "${PID_FILE}" ]; then
        kill "$(cat ${PID_FILE})" 2>/dev/null || true
        rm "${PID_FILE}"
    fi
    exit 0
}

# Trap signals
trap cleanup SIGINT SIGTERM EXIT

# Check if model directory exists
if [ ! -d "/models" ] || [ -z "$(ls -A /models 2>/dev/null)" ]; then
    echo "⚠️  Warning: No model found in /models"
    echo "   Expected model files in /models directory"
    echo "   Mount a volume with your model or download via HF"
fi

# Check for required environment variables
echo "📋 Environment Configuration:"
echo "  MODEL_PATH: ${MODEL_PATH:-/models}"
echo "  MODEL_NAME: ${MODEL_NAME:-meta-llama/Llama-3.1-8B-Instruct}"
echo "  GPU_MEMORY_UTILIZATION: ${GPU_MEMORY_UTILIZATION:-0.9}"
echo "  MAX_MODEL_LEN: ${MAX_MODEL_LEN:-131072}"
echo ""

# Start the server
echo "Starting vLLM server..."
python vllm_server.py 2>&1 | tee -a "${LOG_FILE}" &
echo $! > "${PID_FILE}"

echo "✅ vLLM server started with PID $(cat ${PID_FILE})"
echo "   Logs: ${LOG_FILE}"
echo "   Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"

# Wait for process
wait "${PID_FILE}" 2>/dev/null || true
