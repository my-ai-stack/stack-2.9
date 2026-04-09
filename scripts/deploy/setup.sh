#!/bin/bash
# Stack 2.9 - Quick Setup Script
# This script sets up the development environment

set -e

echo "🚀 Stack 2.9 Setup"
echo "=================="
echo ""

# Check prerequisites
echo "📦 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "⚠️  npm is not installed. Some features may not work."
fi

echo "✅ Prerequisites check passed!"
echo ""

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt 2>/dev/null || echo "Note: Some packages may fail on older systems"

# Install training dependencies separately (they're heavy)
echo ""
echo "🤖 Installing training dependencies (this may take a while)..."
cd stack-2.9-training
pip3 install -r requirements.txt 2>/dev/null || echo "Note: Unsloth requires CUDA-compatible system"
cd ..

# Install voice dependencies
echo ""
echo "🎤 Installing voice dependencies..."
cd stack-2.9-voice
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt 2>/dev/null || echo "Voice dependencies may require additional system libraries"
fi
cd ..

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p training-data/code-pairs
mkdir -p stack-2.9-training/data stack-2.9-training/output
mkdir -p stack-2.9-deploy/models
mkdir -p stack-2.9-voice/voice_models
mkdir -p stack-2.9-eval/results

# Verify training data exists
if [ ! -f "training-data/synthetic/examples.jsonl" ]; then
    echo "⚠️  Training data not found. Run the data extractor?"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review README.md for architecture overview"
echo "  2. Run 'make train' to start training (requires GPU)"
echo "  3. Run 'make deploy-local' to start vLLM server"
echo "  4. Run 'make voice-up' to start voice service"
echo "  5. Run 'make eval' to evaluate the model"
echo ""
echo "For help: make help"