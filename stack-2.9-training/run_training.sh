#!/bin/bash

# Stack 2.9 Complete Training Pipeline
# Downloads base model, trains LoRA, merges and exports

set -e

echo "🚀 Starting Stack 2.9 Training Pipeline..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

print_step() {
    echo -e "${CYAN}[STEP $1/$2]${NC} $3"
}

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    print_error "requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

# Check Python
print_status "Checking Python environment..."
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "Not found")
if [[ $PYTHON_VERSION == "Not found" ]]; then
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi
print_success "Python found: $PYTHON_VERSION"

# Check pip
print_status "Checking pip..."
PIP_VERSION=$(pip3 --version 2>/dev/null || echo "Not found")
if [[ $PIP_VERSION == "Not found" ]]; then
    print_error "pip not found. Please install pip"
    exit 1
fi
print_success "pip found: $PIP_VERSION"

# Check for config file
if [ ! -f "$SCRIPT_DIR/train_config.yaml" ]; then
    print_error "train_config.yaml not found in $SCRIPT_DIR"
    exit 1
fi
print_success "Config file found: train_config.yaml"

# Install dependencies
print_status "Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet
print_success "Dependencies installed!"

# Parse config for paths
CONFIG_FILE="$SCRIPT_DIR/train_config.yaml"
INPUT_DATA=$(grep "^  input_path:" "$CONFIG_FILE" | cut -d'"' -f2)

# Check if training data exists
if [ ! -f "$INPUT_DATA" ]; then
    print_warning "Training data not found at $INPUT_DATA"
    print_warning "Attempting to locate training data..."
    
    # Try alternate locations
    ALT_PATHS=(
        "/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/synthetic/examples.jsonl"
        "$SCRIPT_DIR/../training-data/synthetic/examples.jsonl"
    )
    
    for alt_path in "${ALT_PATHS[@]}"; do
        if [ -f "$alt_path" ]; then
            INPUT_DATA="$alt_path"
            print_status "Found training data at: $INPUT_DATA"
            break
        fi
    done
    
    if [ ! -f "$INPUT_DATA" ]; then
        print_error "Training data not found. Please ensure examples.jsonl exists."
        exit 1
    fi
fi
print_success "Training data found: $INPUT_DATA"

# Check GPU availability
print_status "Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || print_warning "GPU detected but nvidia-smi failed"
else
    print_warning "No NVIDIA GPU detected. Training may be slow on CPU."
fi

# Total number of steps
TOTAL_STEPS=4
CURRENT_STEP=0

# =============================================================================
# Step 1: Prepare Dataset
# =============================================================================
CURRENT_Step=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "Preparing Dataset..."

if python3 "$SCRIPT_DIR/prepare_data.py" --config "$CONFIG_FILE" --force; then
    print_success "Dataset preparation completed!"
else
    print_error "Dataset preparation failed!"
    exit 1
fi

# =============================================================================
# Step 2: Train with LoRA
# =============================================================================
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "Training with LoRA..."

# Check for GPU memory
if ! command -v nvidia-smi &> /dev/null; then
    print_warning "No GPU detected. Skipping LoRA training (requires GPU)."
    print_warning "To train later, run: python3 train_lora.py"
else
    if python3 "$SCRIPT_DIR/train_lora.py" --config "$CONFIG_FILE"; then
        print_success "LoRA training completed!"
    else
        print_error "LoRA training failed!"
        exit 1
    fi
fi

# =============================================================================
# Step 3: Merge LoRA Weights
# =============================================================================
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "Merging LoRA weights..."

# Check if LoRA output exists
LORA_DIR=$(grep "^  lora_dir:" "$CONFIG_FILE" | cut -d'"' -f2)
if [ -d "$LORA_DIR" ]; then
    if python3 "$SCRIPT_DIR/merge_adapter.py" --config "$CONFIG_FILE"; then
        print_success "LoRA weights merged successfully!"
    else
        print_warning "Merge failed. LoRA model may not exist."
    fi
else
    print_warning "LoRA output not found. Skipping merge step."
fi

# =============================================================================
# Step 4: AWQ Quantization (Optional)
# =============================================================================
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "Applying AWQ quantization..."

MERGED_DIR=$(grep "^  merged_dir:" "$CONFIG_FILE" | cut -d'"' -f2)
AWQ_DIR=$(grep "^  awq_dir:" "$CONFIG_FILE" | cut -d'"' -f2)

if [ -d "$MERGED_DIR" ]; then
    print_status "Merged model found. Quantizing with AWQ..."
    if python3 "$SCRIPT_DIR/merge_adapter.py" --config "$CONFIG_FILE" --awq; then
        print_success "AWQ quantization completed!"
    else
        print_warning "AWQ quantization failed. Using merged model instead."
    fi
else
    print_warning "Merged model not found. Skipping quantization."
fi

# =============================================================================
# Final Summary
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "🎉 Stack 2.9 Training Pipeline Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_status "📋 Training results:"
ls -la "$LORA_DIR" 2>/dev/null || true

echo ""
echo "💡 Next steps:"
echo ""
echo "   1. Test the model:"
echo "      python3 -c \\"
echo "        'from transformers import AutoModelForCausalLM, AutoTokenizer;'"
echo "        'model = AutoModelForCausalLM.from_pretrained("
echo "          \"$AWQ_DIR\", torch_dtype=torch.float16, load_in_4bit=True);'"
echo "        'tokenizer = AutoTokenizer.from_pretrained(\"Qwen/Qwen2.5-Coder-32B\");'"
echo "        'print(tokenizer.decode("
echo "          model.generate(tokenizer(\"Hello\", return_tensors=\"pt\").to(model.device), max_new_tokens=512)[0]))'"
echo ""
echo "   2. Model locations:"
echo "      - LoRA adapter: $LORA_DIR"
echo "      - Merged model: $MERGED_DIR"
echo "      - Quantized model: $AWQ_DIR"
echo ""
echo "🚀 Happy coding with Stack 2.9!"
echo ""

exit 0