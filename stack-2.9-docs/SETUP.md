# Stack 2.9 - Detailed Setup Guide

This guide provides comprehensive instructions for setting up Stack 2.9 in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Hardware Requirements](#hardware-requirements)
- [Software Prerequisites](#software-prerequisites)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Docker Setup](#docker-setup)
- [Development Setup](#development-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.8+ | 3.11+ |
| **Node.js** | 18+ | 20 LTS |
| **RAM** | 8 GB | 16 GB |
| **GPU VRAM** | 8 GB | 24 GB |
| **Disk Space** | 10 GB | 50 GB |

### Operating Systems

- ✅ **Linux** (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- ✅ **macOS** (12 Monterey or later)
- ⚠️ **Windows** (via WSL2 or Docker)

---

## Hardware Requirements

### CPU-Only Inference (Testing/Development)

For local development and testing without GPU:

| Component | Specification |
|-----------|---------------|
| **CPU** | 4+ cores |
| **RAM** | 8 GB minimum |
| **Storage** | 10 GB free space |

### GPU Inference (Production)

For production deployment with optimal performance:

| Component | Specification | Notes |
|-----------|---------------|-------|
| **GPU** | NVIDIA GPU with 24GB+ VRAM | A100, H100, RTX 3090, RTX 4090 |
| **CPU** | 8+ cores | AMD Ryzen 9, Intel i9 |
| **RAM** | 32 GB | 64 GB recommended |
| **NVMe Storage** | 50 GB+ | For model caching |

### Multi-GPU Setup

For high-throughput production workloads:

```bash
# Example: 2x A100 80GB setup
export CUDA_VISIBLE_DEVICES=0,1

# Stack 2.9 will automatically use tensor parallelism
python stack.py --num-gpus 2
```

---

## Software Prerequisites

### 1. Python Installation

**Linux/macOS:**

```bash
# Using pyenv (recommended)
curl https://pyenv.run | bash
pyenv install 3.11.4
pyenv global 3.11.4

# Verify installation
python --version
```

**Windows (WSL2):**

```bash
# Install WSL2 first
wsl --install -d Ubuntu-22.04

# Then install Python
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### 2. Node.js Installation

**Linux/macOS:**

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# Verify installation
node --version
```

**Windows:**

Download from [nodejs.org](https://nodejs.org/) or use winget:

```powershell
winget install OpenJS.NodeJS.LTS
```

### 3. CUDA Setup (GPU Support)

```bash
# Check CUDA version
nvidia-smi

# Install CUDA Toolkit (if needed)
# Download from: https://developer.nvidia.com/cuda-downloads

# Install cuDNN
sudo apt install libcudnn8 libcudnn8-dev

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### 4. Docker Installation (Optional)

```bash
# Linux
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# macOS
brew install --cask docker

# Windows
# Download Docker Desktop from https://docker.com
```

---

## Installation Methods

### Method 1: Standard Installation

```bash
# Clone repository
git clone https://github.com/openclaw/stack-2.9.git
cd stack-2.9

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for voice features)
npm install

# Verify installation
python stack.py --version
```

### Method 2: Development Installation

```bash
# Clone and setup
git clone https://github.com/openclaw/stack-2.9.git
cd stack-2.9

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify
pytest
```

### Method 3: Docker Installation

```bash
# Build the image
docker build -t stack-2.9 .

# Run with GPU support (Linux)
docker run --gpus all -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  stack-2.9

# Run on macOS (uses Metal acceleration)
docker run -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  stack-2.9
```

### Method 4: Kubernetes Deployment

```yaml
# stack-2.9-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stack-2-9
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stack-2-9
  template:
    metadata:
      labels:
        app: stack-2-9
    spec:
      containers:
      - name: stack-2-9
        image: stack-2.9:latest
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: 32Gi
        ports:
        - containerPort: 3000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: stack-2-9-secrets
              key: api-key
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=3000
API_KEY=your-secret-api-key-here

# Model Configuration
MODEL_NAME=qwen/qwen2.5-coder-32b
CONTEXT_WINDOW=131072
QUANTIZATION=awq

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
NUM_GPUS=1

# Self-Evolution
ENABLE_SELF_EVOLUTION=true
EVOLUTION_INTERVAL_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=stack-2.9.log

# Database
MEMORY_DB_PATH=./self_evolution/data/memory.db
```

### Configuration File

Create `config.yaml` for advanced configuration:

```yaml
# Stack 2.9 Configuration
server:
  host: 0.0.0.0
  port: 3000
  workers: 4
  timeout: 300

model:
  name: qwen/qwen2.5-coder-32b
  device: cuda
  quantization: awq
  context_window: 131072
  temperature: 0.7
  max_tokens: 4096

tools:
  enabled:
    - file_operations
    - git_operations
    - shell_commands
    - api_calls
    - search
    - voice
  sandbox:
    enabled: true
    timeout: 30

self_evolution:
  enabled: true
  interval_hours: 24
  min_success_for_pattern: 3
  min_failure_for_pattern: 2
  max_memories: 10000

memory:
  db_path: ./self_evolution/data/memory.db
  embedding_dim: 128
  similarity_threshold: 0.3

rate_limiting:
  enabled: true
  requests_per_minute: 100
  tokens_per_day: 100000
  concurrent_requests: 5

logging:
  level: INFO
  file: stack-2.9.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### API Configuration

#### Authentication

```bash
# Generate API key
openssl rand -hex 32

# Set in environment
export API_KEY=your-generated-key
```

#### Rate Limiting

| Tier | Requests/min | Tokens/day | Concurrent |
|------|-------------|------------|------------|
| Free | 100 | 100,000 | 5 |
| Pro | 1,000 | 10,000,000 | 20 |
| Enterprise | Custom | Custom | Custom |

---

## Docker Setup

### Building the Image

```bash
# Build with GPU support
docker build -t stack-2.9:gpu -f Dockerfile.gpu .

# Build for CPU only
docker build -t stack-2.9:cpu -f Dockerfile.cpu .
```

### Running with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  stack-2-9:
    build: .
    ports:
      - "3000:3000"
    environment:
      - API_KEY=${API_KEY}
      - MODEL_NAME=qwen/qwen2.5-coder-32b
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f stack-2-9
```

---

## Development Setup

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/openclaw/stack-2.9.git
cd stack-2.9

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit
pre-commit install

# Run pre-commit checks
pre-commit run --all-files

# Run tests
pytest -v
```

### IDE Setup

**VS Code:**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

**PyCharm:**

1. Open Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv/bin/python`
4. Enable Black for formatting

### Running Development Server

```bash
# Start with auto-reload
python -m stack_cli.dev

# Or with debug mode
DEBUG=1 python stack.py
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'stack_cli'`

**Solution:**

```bash
# Reinstall in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. CUDA/GPU Issues

**Problem:** `CUDA out of memory` or `RuntimeError: CUDA not available`

**Solutions:**

```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Clear GPU cache
nvidia-smi --gpu-reset

# Use smaller batch size
python stack.py --batch-size 1

# Use quantization
python stack.py --quantization awq
```

#### 3. Memory Issues

**Problem:** `OutOfMemoryError` during inference

**Solutions:**

```bash
# Increase swap space (Linux)
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Use model quantization
python stack.py --quantization 4bit

# Reduce context window
python stack.py --context-window 32768
```

#### 4. Permission Issues (Linux)

**Problem:** `Permission denied` errors

**Solutions:**

```bash
# Fix script permissions
chmod +x stack.py install.sh setup.sh

# Fix directory permissions
chmod 755 self_evolution/data

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 5. Node.js Issues

**Problem:** `npm ERR!` during installation

**Solutions:**

```bash
# Clear npm cache
npm cache clean --force

# Install with legacy peer deps
npm install --legacy-peer-deps

# Use specific Node version
nvm use 20
```

#### 6. Port Already in Use

**Problem:** `OSError: [Errno 98] Address already in use`

**Solutions:**

```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use a different port
python stack.py --port 3001
```

### Diagnostic Commands

```bash
# Check system resources
nvidia-smi
free -h
df -h

# Check Python environment
python --version
pip list | grep -E "(torch|transformers|openai)"

# Verify installation
python -c "from stack_cli import cli; print('OK')"

# Run diagnostics
python scripts/diagnostics.py
```

### Getting Help

If you encounter issues not covered here:

1. **Check existing issues:** [GitHub Issues](https://github.com/openclaw/stack-2.9/issues)
2. **Ask in discussions:** [GitHub Discussions](https://github.com/openclaw/stack-2.9/discussions)
3. **Email support:** support@stack2.9.openclaw.org

---

## Next Steps

- [API Documentation](API.md) - Integrate Stack 2.9 into your applications
- [Architecture Guide](ARCHITECTURE.md) - Understand the technical internals
- [Contributing Guide](CONTRIBUTING.md) - Help improve Stack 2.9
