#!/bin/bash

# Stack 2.9 Complete Training Pipeline
# Usage: ./run_training.sh

set -e

echo "🚀 Starting Stack 2.9 Training Pipeline..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the stack-2.9-training directory"
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

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    exit 1
fi

# Install dependencies
print_status "Installing Python dependencies..."
pip3 install -r requirements.txt
print_success "Dependencies installed successfully!"

# Check if training data exists
if [ ! -f "/Users/walidsobhi/.openclaw/workspace/training-data/synthetic/examples.jsonl" ]; then
    print_warning "Training data not found at /Users/walidsobhi/.openclaw/workspace/training-data/synthetic/examples.jsonl"
    print_warning "Please ensure the synthetic examples file exists before running the pipeline"
    exit 1
fi

# Step 1: Prepare Dataset
print_status "📊 Step 1: Preparing Dataset..."
python3 prepare_dataset.py
print_success "Dataset preparation completed!"

# Step 2: Train with LoRA
print_status "🚀 Step 2: Training with LoRA..."
python3 train_lora.py
print_success "LoRA training completed!"

# Step 3: Merge LoRA Weights
print_status "🔄 Step 3: Merging LoRA weights..."
python3 merge_lora.py
print_success "LoRA weights merged successfully!"

# Step 4: Apply AWQ Quantization
print_status "🔄 Step 4: Applying AWQ quantization..."
python3 quantize_awq.py
print_success "AWQ quantization completed!"

# Final Summary
print_success "🎉 Stack 2.9 Training Pipeline completed successfully!"
print_success "📁 Output directory: output/"

# List results
print_status "📋 Training results:"
ls -la output/

print_success "🚀 Training complete!"
echo ""
echo "💡 Next steps:"
echo "1. Test the quantized model:"
echo "   python3 -c \"from transformers import AutoModelForCausalLM, AutoTokenizer;"
echo "   model = AutoModelForCausalLM.from_pretrained('output/stack-2.9-awq',"
echo "   torch_dtype=torch.float16, load_in_4bit=True, device_map='auto');"
echo "   tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-Coder-32B');"
echo "   print(tokenizer.decode(model.generate(tokenizer('Hello', return_tensors='pt').to(model.device), max_new_tokens=512)[0], skip_special_tokens=True))\""
echo ""
echo "2. Model details:"
echo "   - LoRA model: output/stack-2.9-lora/"
echo "   - Merged model: output/stack-2.9-merged/"
echo "   - Quantized model: output/stack-2.9-awq/"
echo ""
echo "🚀 Happy coding with Stack 2.9!"
echo ""

exit 0