#!/bin/bash

# Stack 2.9 Local Deployment Script
# Usage: ./local_deploy.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
COMPOSE_FILE="docker-compose.yml"
MODEL_PATH="./models"
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"  # Will be replaced with Stack 2.9
MODEL_FORMAT="hf"
GPU_MEMORY_UTILIZATION="0.9"
LOG_LEVEL="INFO"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check NVIDIA Docker support
    if ! docker info | grep -q "nvidia"; then
        print_warning "NVIDIA Docker support not detected. GPU acceleration may not work."
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create directories
    mkdir -p models logs
    chmod 755 models logs
    
    # Create .env file
    cat > .env << EOF
MODEL_PATH=${MODEL_PATH}
MODEL_NAME=${MODEL_NAME}
MODEL_FORMAT=${MODEL_FORMAT}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION}
LOG_LEVEL=${LOG_LEVEL}
EOF
    
    print_success "Environment setup complete"
}

# Function to download model
download_model() {
    print_status "Downloading model (this may take a while)..."
    
    if [ ! -d "models/${MODEL_NAME##*/}" ]; then
        print_status "Downloading ${MODEL_NAME}..."
        
        # Use HuggingFace Hub to download model
        if command -v huggingface-cli &> /dev/null; then
            huggingface-cli download ${MODEL_NAME} --local-dir models
        elif command -v git &> /dev/null; then
            git lfs install
            git clone https://huggingface.co/${MODEL_NAME} models/${MODEL_NAME##*/}
        else
            print_error "Neither huggingface-cli nor git is available for model download"
            exit 1
        fi
        
        print_success "Model downloaded successfully"
    else
        print_warning "Model already exists, skipping download"
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    docker-compose -f ${COMPOSE_FILE} up -d
    
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check if services are running
    if docker-compose -f ${COMPOSE_FILE} ps | grep -q "Up"; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        docker-compose -f ${COMPOSE_FILE} logs
        exit 1
    fi
}

# Function to check status
check_status() {
    print_status "Checking service status..."
    
    docker-compose -f ${COMPOSE_FILE} ps
    
    print_status "Health check..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "vLLM server is healthy"
    else
        print_warning "vLLM server health check failed"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --no-model          Skip model download"
    echo "  --force-download    Force download even if model exists"
    echo "  --clean             Clean up before deployment"
    echo ""
    echo "Environment variables:"
    echo "  MODEL_PATH          Path to model directory"
    echo "  MODEL_NAME          HuggingFace model name"
    echo "  MODEL_FORMAT        Model format (hf, safetensors, etc.)"
    echo "  GPU_MEMORY_UTILIZATION  GPU memory utilization (0.0-1.0)"
    echo "  LOG_LEVEL           Log level (DEBUG, INFO, WARNING, ERROR)"
}

# Parse command line arguments
NO_MODEL=false
FORCE_DOWNLOAD=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --no-model)
            NO_MODEL=true
            shift
            ;;
        --force-download)
            FORCE_DOWNLOAD=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Clean up if requested
if [[ "${CLEAN}" == "true" ]]; then
    print_status "Cleaning up existing deployment..."
    docker-compose -f ${COMPOSE_FILE} down -v
    rm -rf models logs
fi

# Main deployment process
main() {
    print_status "Starting Stack 2.9 local deployment..."
    echo "==================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Download model if not skipped
    if [[ "${NO_MODEL}" == "false" ]]; then
        if [[ "${FORCE_DOWNLOAD}" == "true" ]] || [ ! -d "models/${MODEL_NAME##*/}" ]; then
            download_model
        else
            print_warning "Model exists and --force-download not specified, skipping download"
        fi
    else
        print_warning "Model download skipped as requested"
    fi
    
    # Start services
    start_services
    
    # Check status
    check_status
    
    print_success "Stack 2.9 deployment completed successfully!"
    echo ""
    echo "Service URLs:"
    echo "  vLLM API: http://localhost:8000"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000"
    echo "  Traefik Dashboard: http://localhost:8080"
    echo ""
    echo "Health check: http://localhost:8000/health"
    echo ""
    echo "To stop services: docker-compose -f ${COMPOSE_FILE} down"
    echo "To view logs: docker-compose -f ${COMPOSE_FILE} logs -f"
}

# Run main function
main "$@"