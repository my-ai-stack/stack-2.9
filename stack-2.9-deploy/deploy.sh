#!/bin/bash
#
# Stack 2.9 Turnkey Deployment Script
# One-command deployment for Local, RunPod, and VastAI platforms
#
# Usage:
#   ./deploy.sh [platform] [options]
#
# Platforms:
#   local      - Deploy locally with docker-compose
#   runpod     - Deploy to RunPod (requires runpodctl)
#   vastai     - Deploy to Vast.ai (requires vastai)
#   kubernetes - Deploy to Kubernetes cluster
#
# Examples:
#   ./deploy.sh local --model TheBloke/Llama-2-7B-Chat-AWQ
#   ./deploy.sh runpod --gpu A100-40GB
#   ./deploy.sh kubernetes --namespace inference
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
cyan='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PLATFORM="${1:-local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"
IMAGE_NAME="stack-2.9-server"
VERSION="2.9.0"
BUILD_ARGS=""
MODEL_ID=""
HF_TOKEN=""

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║         Stack 2.9 Deployment Tool v${VERSION}         ║"
echo "║     Turnkey LLM Inference Server Deployment       ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
parse_args() {
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --model)
                MODEL_ID="$2"
                shift 2
                ;;
            --token)
                HF_TOKEN="$2"
                shift 2
                ;;
            --gpu)
                GPU_TYPE="$2"
                shift 2
                ;;
            --namespace)
                K8S_NAMESPACE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    echo "Usage: $0 [platform] [options]"
    echo ""
    echo "Platforms:"
    echo "  local         Deploy with docker-compose (default)"
    echo "  runpod        Deploy to RunPod.io"
    echo "  vastai        Deploy to Vast.ai"
    echo "  kubernetes    Deploy to Kubernetes"
    echo ""
    echo "Options:"
    echo "  --model ID     Hugging Face model ID (default: TheBloke/Llama-2-7B-Chat-AWQ)"
    echo "  --token TOKEN  Hugging Face token for gated models"
    echo "  --gpu TYPE     GPU type for cloud deployments"
    echo "  --namespace NS Kubernetes namespace (default: default)"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local --model mistralai/Mistral-7B-Instruct-v0.2"
    echo "  $0 runpod --gpu A100-40GB"
    echo "  $0 kubernetes --namespace inference"
}

# Platform detection
detect_platform() {
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
        HAS_GPU=true
    else
        echo -e "${YELLOW}⚠ No NVIDIA GPU detected - CPU-only mode${NC}"
        HAS_GPU=false
    fi

    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ Docker & Docker Compose available${NC}"
        HAS_DOCKER=true
    else
        echo -e "${RED}✗ Docker not available${NC}"
        HAS_DOCKER=false
    fi
}

# Build Docker image
build_image() {
    echo -e "\n${BLUE}Building Docker image...${NC}"

    if [ -n "$MODEL_ID" ]; then
        BUILD_ARGS="$BUILD_ARGS --build-arg MODEL_ID=$MODEL_ID"
    fi

    docker build \
        --build-arg PYTHON_VERSION=3.10 \
        --build-arg VLLM_VERSION=0.6.3 \
        --build-arg CUDA_VERSION=12.1.0 \
        -t "${IMAGE_NAME}:${VERSION}" \
        -t "${IMAGE_NAME}:latest" \
        "$SCRIPT_DIR"

    echo -e "${GREEN}✓ Docker image built successfully${NC}"
}

# Deploy locally with docker-compose
deploy_local() {
    echo -e "\n${BLUE}Deploying locally with Docker Compose...${NC}"

    if [ "$HAS_DOCKER" = false ]; then
        echo -e "${RED}Error: Docker is required for local deployment${NC}"
        exit 1
    fi

    # Build image
    build_image

    # Create .env file
    ENV_FILE="${SCRIPT_DIR}/.env"
    cat > "$ENV_FILE" << EOF
# Stack 2.9 Local Deployment Configuration
MODEL_ID=${MODEL_ID:-TheBloke/Llama-2-7B-Chat-AWQ}
HUGGING_FACE_TOKEN=${HF_TOKEN}
QUANTIZATION=awq
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-1}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.9}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-4096}
MAX_NUM_SEQS=${MAX_NUM_SEQS:-64}
MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-4096}
HOST=0.0.0.0
PORT=8000
EOF

    echo -e "${YELLOW}Configuration saved to $ENV_FILE${NC}"

    # Start services
    echo -e "\n${BLUE}Starting Stack 2.9 service...${NC}"
    docker-compose -f "$COMPOSE_FILE" up -d

    echo -e "\n${GREEN}✓ Stack 2.9 is starting...${NC}"
    echo -e "  API Endpoint: ${BLUE}http://localhost:8000${NC}"
    echo -e "  Health Check: ${BLUE}http://localhost:8000/health${NC}"
    echo -e "  API Docs: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "\n${YELLOW}View logs: docker-compose -f '$COMPOSE_FILE' logs -f${NC}"
    echo -e "${YELLOW}Stop service: docker-compose -f '$COMPOSE_FILE' down${NC}"
}

# Deploy to RunPod
deploy_runpod() {
    echo -e "\n${BLUE}Deploying to RunPod...${NC}"

    if ! command -v runpodctl &> /dev/null; then
        echo -e "${RED}Error: runpodctl not found${NC}"
        echo "Install with: npm install -g runpodctl"
        exit 1
    fi

    # Build and push image
    echo -e "${YELLOW}Building and pushing Docker image to registry...${NC}"
    # User needs to set their registry
    read -p "Enter your Docker registry (e.g., docker.io/username): " REGISTRY
    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}Registry is required for RunPod deployment${NC}"
        exit 1
    fi

    build_image
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"
    docker push "${REGISTRY}/${IMAGE_NAME}:latest"
    docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"

    # Update runpod-template.json with registry
    sed -i.bak "s|your-registry/stack-2.9:latest|${REGISTRY}/${IMAGE_NAME}:latest|g" \
        "${SCRIPT_DIR}/runpod-template.json"
    rm -f "${SCRIPT_DIR}/runpod-template.json.bak"

    # Create template on RunPod
    echo -e "${YELLOW}Creating RunPod template...${NC}"
    runpodctl create template \
        --template-file "${SCRIPT_DIR}/runpod-template.json" \
        --name "stack-2.9-${VERSION}"

    echo -e "\n${GREEN}✓ RunPod template created!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Go to RunPod.io and deploy using template 'stack-2.9-${VERSION}'"
    echo "  2. Set your desired GPU type"
    echo "  3. Configure MODEL_ID and HUGGING_FACE_TOKEN environment variables"
    echo "  4. The server will start automatically on port 8000"
}

# Deploy to VastAI
deploy_vastai() {
    echo -e "\n${BLUE}Deploying to Vast.ai...${NC}"

    if ! command -v vastai &> /dev/null; then
        echo -e "${RED}Error: vastai CLI not found${NC}"
        echo "Install from: https://vast.ai/docs/cli"
        exit 1
    fi

    # Build and push image
    read -p "Enter your Docker registry (e.g., docker.io/username): " REGISTRY
    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}Registry is required for VastAI deployment${NC}"
        exit 1
    fi

    build_image
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"
    docker push "${REGISTRY}/${IMAGE_NAME}:latest"
    docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"

    # Update vastai-template.json
    sed -i.bak "s|your-registry/stack-2.9:latest|${REGISTRY}/${IMAGE_NAME}:latest|g" \
        "${SCRIPT_DIR}/vastai-template.json"
    rm -f "${SCRIPT_DIR}/vastai-template.json.bak"

    echo -e "${GREEN}✓ VastAI template ready!${NC}"
    echo -e "${YELLOW}Deploy with:${NC}"
    echo "  vastai create instance --template-file ${SCRIPT_DIR}/vastai-template.json"
    echo ""
    echo "Or manually:"
    echo "  1. Select GPU: RTX 4090 24GB or higher"
    echo "  2. Set max bid to ~\$0.50/hour"
    echo "  3. Upload template and launch"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    echo -e "\n${BLUE}Deploying to Kubernetes...${NC}"

    K8S_NAMESPACE="${K8S_NAMESPACE:-stack-2.9}"

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}Error: kubectl not found${NC}"
        exit 1
    fi

    # Build and push image (requires image builder)
    read -p "Enter your Docker registry: " REGISTRY
    if [ -z "$REGISTRY" ]; then
        echo -e "${YELLOW}Using local image - ensure your K8s cluster can access it${NC}"
    else
        build_image
        docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
        docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"
        docker push "${REGISTRY}/${IMAGE_NAME}:latest"
        IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
    fi

    IMAGE="${IMAGE:-${IMAGE_NAME}:latest}"

    # Apply manifests
    echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"

    # Create namespace if needed
    kubectl create namespace "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Update image in deployment
    sed "s|your-registry/stack-2.9:latest|${IMAGE}|g" \
        "${SCRIPT_DIR}/kubernetes/deployment.yaml" | \
        kubectl apply -n "$K8S_NAMESPACE" -f -

    # Apply PVC
    kubectl apply -n "$K8S_NAMESPACE" -f "${SCRIPT_DIR}/kubernetes/pvc.yaml"

    # Apply service
    kubectl apply -n "$K8S_NAMESPACE" -f "${SCRIPT_DIR}/kubernetes/service.yaml"

    # Apply HPA
    kubectl apply -n "$K8S_NAMESPACE" -f "${SCRIPT_DIR}/kubernetes/hpa.yaml"

    echo -e "\n${GREEN}✓ Kubernetes deployment complete!${NC}"
    echo -e "  Namespace: ${K8S_NAMESPACE}"
    echo -e "  Checking deployment status..."

    kubectl wait --for=condition=available --timeout=300s deployment/stack-2.9 -n "$K8S_NAMESPACE"

    # Get service URL
    SERVICE_TYPE=$(kubectl get svc stack-2.9 -n "$K8S_NAMESPACE" -o jsonpath='{.spec.type}')
    if [ "$SERVICE_TYPE" = "LoadBalancer" ]; then
        EXTERNAL_IP=$(kubectl get svc stack-2.9 -n "$K8S_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        echo -e "  API Endpoint: ${BLUE}http://${EXTERNAL_IP}:8000${NC}"
    else
        NODE_PORT=$(kubectl get svc stack-2.9 -n "$K8S_NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}')
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
        echo -e "  API Endpoint: ${BLUE}http://${NODE_IP}:${NODE_PORT}${NC}"
    fi
}

# Health check after deployment
health_check() {
    local url="http://localhost:${PORT:-8000}/health"
    echo -e "\n${YELLOW}Waiting for server to become healthy...${NC}"

    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" &> /dev/null; then
            echo -e "${GREEN}✓ Server is healthy!${NC}"
            echo -e "Health check response:"
            curl -s "$url" | python3 -m json.tool 2>/dev/null || curl -s "$url"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    echo -e "\n${RED}✗ Health check failed after $((max_attempts * 2)) seconds${NC}"
    echo "Check logs with: docker-compose -f '$COMPOSE_FILE' logs"
    return 1
}

# Main execution
main() {
    case "$PLATFORM" in
        local|"")
            detect_platform
            deploy_local
            health_check
            ;;
        runpod)
            detect_platform
            deploy_runpod
            ;;
        vastai)
            detect_platform
            deploy_vastai
            ;;
        kubernetes|k8s)
            deploy_kubernetes
            ;;
        *)
            echo -e "${RED}Unknown platform: $PLATFORM${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Run
parse_args "$@"
main
