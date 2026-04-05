# Stack 2.9 — 5-Minute Quick Start

> **Goal:** Get Stack 2.9 running and solving coding tasks in under 5 minutes.

Stack 2.9 is an AI coding assistant powered by **Qwen2.5-Coder-32B** with Pattern Memory — it learns from your interactions and improves over time.

---

## 📋 Prerequisites

### Required
| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| Git | Any recent | `git --version` |
| pip | Latest | `pip --version` |

### Optional (Recommended)
| Resource | Why You Need It | Minimum |
|----------|----------------|---------|
| **GPU** | Fast code generation | RTX 3070 / M1 Pro |
| **16GB VRAM** | Run 32B model smoothly | 8GB for 7B quantized |

> **No GPU?** Stack 2.9 works on CPU via Ollama or cloud providers (OpenAI, Together AI, etc.).

---

## ⚡ Step 1 — Install in 60 Seconds

```bash
# 1. Clone the repository
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env
```

**That's it.** If you hit errors, see [Troubleshooting](#-troubleshooting) below.

---

## 🔑 Step 2 — Configure Your Model Provider

Stack 2.9 supports multiple LLM providers. **Pick one that matches your setup:**

### Option A: Ollama (Recommended — Local, Private)

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the Qwen model
ollama pull qwen2.5-coder:32b

# Set environment
export MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5-coder:32b
```

Edit your `.env` file:
```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:32b
```

### Option B: Together AI (Best for Qwen, Cloud)

```bash
# Get your API key at https://together.ai
export TOGETHER_API_KEY=tog-your-key-here
```

Edit your `.env`:
```env
MODEL_PROVIDER=together
TOGETHER_API_KEY=tog-your-key-here
TOGETHER_MODEL=togethercomputer/qwen2.5-32b-instruct
```

### Option C: OpenAI (GPT-4o)

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

### Option D: Anthropic (Claude)

```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20240229
```

### Option E: OpenRouter (Unified Access)

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_MODEL=openai/gpt-4o
```

---

## 🚀 Step 3 — Run Your First Task

### Interactive Chat Mode

```bash
python stack.py
```

You'll see:
```
╔══════════════════════════════════════════════╗
║         Stack 2.9 — AI Coding Assistant     ║
║  Pattern Memory: Active | Tools: 46          ║
╚══════════════════════════════════════════════╝

You: Write a Python function to reverse a string
```

### Single Query Mode

```bash
python stack.py -c "Write a Python function to reverse a string"
```

**Expected output:**
```python
def reverse_string(s):
    """Reverse a string and return it."""
    return s[::-1]

# Or for a more robust version:
def reverse_string(s):
    return ''.join(reversed(s))
```

### Ask About Your Codebase

```bash
python stack.py -c "Find all Python files modified in the last week and list them"
```

### Generate and Run Code

```bash
python stack.py -c "Create a hello world Flask app with one route"
```

---

## 📊 Step 4 — Run Evaluation (Optional)

> **Note:** Evaluation requires a GPU with ~16GB VRAM or more.

### Prepare Your Fine-Tuned Model

After training Stack 2.9 on your data, your merged model will be in:
```
./output/merged/
```

### Run HumanEval Benchmark

```bash
python evaluate_model.py \
    --model-path ./output/merged \
    --benchmark humaneval \
    --num-samples 10 \
    --output results.json
```

### Run MBPP Benchmark

```bash
python evaluate_model.py \
    --model-path ./output/merged \
    --benchmark mbpp \
    --num-samples 10 \
    --output results.json
```

### Run Both Benchmarks

```bash
python evaluate_model.py \
    --model-path ./output/merged \
    --benchmark both \
    --num-samples 10 \
    --k-values 1,10 \
    --output results.json
```

**Expected output format:**
```
============================================================
HumanEval Results
============================================================
  pass@1: 65.00%
  pass@10: 82.00%
  Total problems evaluated: 12
============================================================

============================================================
MBPP Results
============================================================
  pass@1: 70.00%
  pass@10: 85.00%
  Total problems evaluated: 12
============================================================
```

### Quick Evaluation (5 Problems Only)

```bash
python evaluate_model.py \
    --model-path ./output/merged \
    --benchmark humaneval \
    --num-problems 5 \
    --num-samples 5
```

---

## 🐳 Step 5 — Deploy Stack 2.9

### Deploy Locally with Docker

```bash
# Start the container
docker build -t stack-2.9 .
docker run -p 7860:7860 \
    -e MODEL_PROVIDER=ollama \
    -e OLLAMA_MODEL=qwen2.5-coder:32b \
    stack-2.9
```

Access at: **http://localhost:7860**

### Deploy to RunPod (Cloud GPU)

```bash
# Edit runpod_deploy.sh with your config first
bash runpod_deploy.sh --gpu a100 --instance hourly
```

### Deploy to Kubernetes

```bash
# 1. Edit k8s/secret.yaml with your HuggingFace token
# 2. Apply the manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -n stack-29
kubectl logs -n stack-29 deployment/stack-29
```

### Hardware Requirements for Deployment

| Model Size | Minimum GPU | Recommended | Quantized (4-bit) |
|------------|-------------|-------------|-------------------|
| 7B | RTX 3070 (8GB) | A100 40GB | RTX 3060 (6GB) |
| 32B | A100 40GB | A100 80GB | RTX 3090 (24GB) |

---

## 🧠 Pattern Memory Quick Guide

Stack 2.9 stores successful patterns to help with future tasks.

### List Your Patterns

```bash
python stack.py --patterns list
python stack.py --patterns stats
```

### Extract Patterns from Your Git History

```bash
python scripts/extract_patterns_from_git.py \
    --repo-path . \
    --output patterns.jsonl \
    --since-date "2024-01-01"
```

### Merge LoRA Adapters (Team Sharing)

```bash
python scripts/merge_lora_adapters.py \
    --adapters adapter_a.safetensors adapter_b.safetensors \
    --weights 0.7 0.3 \
    --output merged.safetensors
```

---

## 🛠️ Troubleshooting

### "Module not found" errors

```bash
pip install -r requirements.txt
```

### "CUDA out of memory" during evaluation

```bash
# Reduce batch size
python evaluate_model.py --model-path ./merged --num-samples 5

# Or use 4-bit quantization
# (See docs/TRAINING_7B.md for quantized training)
```

### "Model not found" with Ollama

```bash
ollama pull qwen2.5-coder:32b
ollama list   # Verify it's installed
```

### "API key not set" errors

```bash
# Double-check your .env file
cat .env

# For testing, you can also set inline
export TOGETHER_API_KEY=tog-your-key
```

### Slow inference on CPU

```bash
# Use a smaller model
export OLLAMA_MODEL=qwen2.5-coder:7b

# Or switch to cloud
export MODEL_PROVIDER=together
```

### Docker build fails

```bash
# Use Python 3.10 explicitly
docker build --build-arg PYTHON_VERSION=3.10 -t stack-2.9 .
```

### Kubernetes GPU not found

```bash
# Verify nvidia.com/gpu label on your node
kubectl get nodes -L nvidia.com/gpu

# Install NVIDIA GPU Operator if missing
# https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/
```

---

## 📚 What's Next?

| Goal | Go To |
|------|-------|
| Train on my own data | `docs/TRAINING_7B.md` |
| Learn all 46 tools | `TOOLS.md` |
| Set up team pattern sharing | `docs/pattern-moat.md` |
| Understand the architecture | `docs/reference/ARCHITECTURE.md` |
| Report a bug | `SECURITY.md` / GitHub Issues |

---

## ⚡ Quick Reference Card

```bash
# Install
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9 && pip install -r requirements.txt

# Configure
cp .env.example .env   # Edit with your API keys

# Run
python stack.py                              # Interactive
python stack.py -c "your code request"        # Single query

# Evaluate
python evaluate_model.py --model-path ./merged --benchmark humaneval

# Deploy
docker build -t stack-2.9 . && docker run -p 7860:7860 stack-2.9
```

---

*Stack 2.9 — AI that learns your patterns and grows with you.*
