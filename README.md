<p align="center">
  <a href="https://github.com/my-ai-stack/stack-2.9">
    <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9?style=flat-square" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/my-ai-stack/stack-2.9/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/my-ai-stack/stack-2.9?style=flat-square&logo=apache" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/OpenRouter-Compatible-green?style=flat-square&logo=openrouter" alt="OpenRouter"/>
  <img src="https://img.shields.io/badge/Together_AI-Ready-green?style=flat-square&logo=databricks" alt="Together AI"/>
  <img src="https://img.shields.io/badge/Hugging%20Face-Model-green?style=flat-square&logo=huggingface" alt="Hugging Face"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
</p>

# Stack 2.9

> **The pattern-based AI coding assistant that improves through experience.**

Stack 2.9 is an open-source AI coding assistant powered by **Qwen2.5-Coder-32B**, enhanced with **Pattern Memory** — a system that learns from interactions by storing successful patterns and retrieving them for future tasks.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Pattern Memory** | Stores and retrieves successful coding patterns, becoming more helpful over time |
| **Multi-Provider** | Works with Ollama, OpenAI, Anthropic, OpenRouter, Together AI |
| **46 Built-in Tools** | File ops, git, shell, web search, memory, task planning |
| **Voice Integration** | Coqui XTTS for voice cloning, STT for voice input |
| **128K Context** | Handles large codebases with ease |
| **Self-Hosted** | Full control, your data stays private |
| **MCP Support** | Integrates with any Model Context Protocol server |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9
pip install -r requirements.txt
```

### Basic Usage

```bash
# Start interactive chat
python stack.py

# Single query
python stack.py -c "Write a Python function to reverse a string"

# Run evaluation (requires datasets)
python stack.py --eval humaneval --provider ollama
```

### Configure Model Provider

Set environment variables before running:

```bash
# For Ollama (local, recommended)
export MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5-coder:32b

# For OpenAI
export MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o

# For Together AI (recommended for Qwen)
export MODEL_PROVIDER=together
export TOGETHER_API_KEY=tog-...
export TOGETHER_MODEL=togethercomputer/qwen2.5-coder-32b-instruct
```

See [Configuration](#⚙️-configuration) for all options.

---

## 🏗️ Model Card

### Base Model

- **Architecture:** Qwen2.5-Coder-32B (32 billion parameters)
- **Fine-tuning:** LoRA (Low-Rank Adaptation)
- **Context Length:** 131,072 tokens
- **Quantization:** 4-bit AWQ optional for efficient deployment

### Training Data

Stack 2.9 is fine-tuned on a diverse dataset including:

- **Pattern Memory Data** (5K-10K examples): Successful interaction logs with feedback
- **Synthetic Tool Examples** (20K+): Generated scenarios covering all 46 tools
- **Public Datasets**:
  - OpenAssistant (coding conversations)
  - CodeAct (executable actions)
  - CodeContests (competition problems)
  - StarCoder Data (permissively licensed code)

All data undergoes:
- Deduplication
- License compatibility check
- Quality filtering (length, validity, success rate)

### Intended Use

✅ **Allowed:**
- AI-assisted coding and code completion
- Code explanation and documentation
- Debugging and error analysis
- Tool-use automation
- Educational purposes
- Research on pattern-based AI

❌ **Not Recommended:**
- High-stakes production code without human review
- Security-critical applications
- Medical, legal, or financial decision-making
- Generating harmful or malicious code
- Large-scale redistribution without compliance checks

### Limitations

- **Hallucinations:** May generate incorrect code; always verify with tests
- **Security:** Can suggest vulnerable code; security review required for production
- **Licensing:** May reproduce copyrighted snippets; use license checks
- **Tool Dependencies:** Full functionality requires OpenClaw framework
- **Pattern Freshness:** Initial deployments have limited pattern library

---

## 📊 Benchmarks

⚠️ **Important:** The benchmark scores previously listed in this README have been **removed pending verification**. An audit revealed:

- HumanEval & MBPP implementations only had 20 problems (1-4% of full benchmarks)
- No proper inference logs exist for claimed numbers
- Tool Use evaluation lacked proper implementation

These scores were **unverifiable** and have been removed.

### Current Status

| Benchmark | Status | Notes |
|-----------|--------|-------|
| **HumanEval** | Evaluation in progress | Full 164-problem suite |
| **MBPP** | Evaluation in progress | Full 500-problem suite |
| **Tool Use** | Benchmark development | Custom tool-calling task |
| **GSM8K** | Not started | Math reasoning (optional) |

We are rebuilding evaluation infrastructure with proper methodology. See [EVALUATION.md](EVALUATION.md) for the audit report and plan.

**Expected baseline** (based on Qwen2.5-Coder-32B):
- HumanEval: ~70-72% Pass@1
- MBPP: ~75-77% Pass@1

Actual fine-tuned results will be published after proper evaluation.

---

## 💻 Usage

### Command Line Interface

```bash
# Interactive chat mode
python stack.py

# Single query
python stack.py -c "Explain this code..."

# Run benchmarks
python stack.py --eval all --provider ollama

# Manage patterns
python stack.py --patterns list
python stack.py --patterns stats
```

### Python API

```python
from stack_cli.agent import create_agent

# Create agent
agent = create_agent()

# Chat
response = agent.process("Write a hello world function")
print(response.content)

# Use tools
result = agent.process("List files in current directory")
```

### Available Tools

Stack 2.9 includes **46 built-in tools** for:
- File operations (read, write, edit, search, grep, copy, move, delete)
- Git operations (status, commit, push, pull, branch, log, diff)
- Code execution (run, test, lint, format, typecheck, server, install)
- Web (search, fetch, download, check_url, screenshot)
- Memory (recall, save, list, context_load, project_scan)
- Task planning (create_task, list_tasks, update_task, delete_task, create_plan, execute_plan)

See [TOOLS.md](TOOLS.md) for complete documentation with examples.

---

## 🔄 Pattern Memory Evolution

Stack 2.9's Pattern Memory can **evolve** automatically:

### Auto-Extraction from Git

Mine your Git history for patterns:

```bash
python scripts/extract_patterns_from_git.py \
    --repo-path . \
    --output patterns.jsonl \
    --since-date "2024-01-01"
```

See `docs/pattern-moat.md` for details.

### Team Sync (Shared Database)

Multiple developers can share patterns via a central PostgreSQL + FastAPI service. Schema and API endpoints documented in `docs/pattern-moat.md`.

### Weight Fusion

Merge LoRA adapters from multiple users with success-rate-weighted averaging:

```bash
python scripts/merge_lora_adapters.py \
    --adapters adapter_a.safetensors adapter_b.safetensors \
    --weights 0.7 0.3 \
    --output merged.safetensors
```

---

## 🛠️ Training & Fine-Tuning

### Training Options

| Platform | Notebook | Description |
|----------|----------|-------------|
| **Google Colab** | `colab_train_stack29.ipynb` | Free T4 GPU, 3-5 hours |
| **Kaggle** | `kaggle_train_stack29.ipynb` | Free P100 GPU, 2-4 hours |
| **Local Mac** | `train_local.py` | MPS/Apple Silicon |
| **Cloud GPUs** | See below | RunPod, Vast.ai, etc |

### Quick Training (Colab)

Use the provided notebook for quick prototyping:

```bash
# Open in Google Colab
colab_train_stack29.ipynb
```

Trains a 5K-example mini dataset in 3-5 hours on free T4 GPU.

### Full Training Pipeline

```bash
# Prepare data (from your sources)
python scripts/create_mini_dataset.py --size 5000 --output data_mini/train.jsonl

# Train LoRA adapter
cd stack_2_9_training
python -m train_lora --config train_config.yaml

# Merge adapter with base model
python -m merge_adapter --base-model Qwen/Qwen2.5-Coder-32B
```

### Cloud Training Scripts

For production training on GPUs:

- **RunPod:** `runpod_deploy.sh` — launches A100-80GB instances
- **Vast.ai:** `vastai_deploy.sh` — finds cheapest suitable instances
- **Kubernetes:** `k8s/deployment.yaml` — deploy to your K8s cluster
- **Docker:** `docker-compose.cloud.yaml` — bare-metal GPU servers

See each script for usage instructions.

### Extracting Training Data from Your Codebase

Extract tool patterns from your codebase to train the model:

```bash
# Extract tool patterns
python scripts/extract_rtmp_tools.py

# Create advanced examples
python scripts/extract_rtmp_tools_advanced.py
```

This creates `data/rtmp-tools/` with tool usage patterns that can be combined with the main training data.

### Kaggle Training

Free GPU training on Kaggle (P100 16GB VRAM):

```bash
# Open in Kaggle
kaggle_train_stack29.ipynb
```

### Local Mac Training (MPS)

For Apple Silicon Macs without GPU cloud access:

```bash
python train_local.py
```

### Extracting Tool Patterns from RTMP

Extract training data from your RTMP codebase to teach the model your custom tools:

```bash
# Extract tool patterns
python scripts/extract_rtmp_tools.py
python scripts/extract_rtmp_tools_advanced.py

# Combined data includes 46+ tool patterns
data/rtmp-tools/combined_tools.jsonl
```

The combined training data includes:
- 41,807 code completion examples
- 59 RTMP tool usage patterns (BashTool, FileReadTool, Task tools, etc.)

---

## 🐳 Deployment

### Docker (Local/Cloud)

```bash
cd stack-2.9-deploy
docker-compose up -d
```

### Cloud Platforms

| Platform | Use Case | Documentation |
|----------|----------|---------------|
| **RunPod** | Pay-as-you-go GPU | `runpod_deploy.sh` |
| **Vast.ai** | Spot instances (cheap) | `vastai_deploy.sh` |
| **Kubernetes** | Enterprise scale | `k8s/` directory |
| **HuggingFace Spaces** | Free inference hosting | `docs/free-deployment.md` |

**Hardware requirements:**
- **7B model:** RTX 3070 (8GB) minimum
- **32B model:** A100-40GB recommended
- **Quantized:** 4-bit reduces VRAM by ~50%

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MODEL_PROVIDER` | Yes | `ollama`, `openai`, `anthropic`, `openrouter`, `together` |
| `OPENAI_API_KEY` | If OpenAI | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | If Anthropic | Your Anthropic API key |
| `OPENROUTER_API_KEY` | If OpenRouter | Your OpenRouter API key |
| `TOGETHER_API_KEY` | If Together | Your Together AI API key |
| `OLLAMA_MODEL` | If Ollama | Model name (e.g., `qwen2.5-coder:32b`) |

### Configuration File

Create `stack.yaml` in project root:

```yaml
model:
  provider: ollama
  name: qwen2.5-coder:32b
  temperature: 0.7

training:
  lora_rank: 16
  learning_rate: 3e-4
  epochs: 3

pattern_memory:
  enabled: true
  max_patterns: 10000
  similarity_threshold: 0.75
```

---

## 📁 Project Structure

```
stack-2.9/
├── stack_cli/              # CLI interface & agent
│   ├── cli.py             # Main entry point
│   ├── agent.py           # AI agent with tools
│   └── context.py         # Context management
│
├── stack_2_9_eval/         # Evaluation framework
│   ├── model_client.py    # Unified model API
│   └── benchmarks/        # Benchmark implementations
│
├── stack_2_9_training/     # Training scripts
│   ├── train_lora.py      # LoRA training
│   ├── merge_adapter.py   # Merge LoRA into base
│   └── prepare_data.py    # Data preparation
│
├── stack_2_9_deploy/       # Deployment configs
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── scripts/                # Utility scripts
│   ├── extract_patterns_from_git.py
│   ├── merge_lora_adapters.py
│   └── ...
│
├── docs/                   # Documentation
│   ├── pattern-moat.md    # Pattern memory evolution
│   └── ...
│
├── k8s/                    # Kubernetes configs
│   ├── deployment.yaml
│   ├── service.yaml
│   └── secret.yaml
│
├── TOOLS.md                # Complete tool reference (46 tools)
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── stack.yaml              # Config (create your own)
└── colab_train_stack29.ipynb  # Quick training notebook
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for full text.

### Dependencies

- Base model: Qwen2.5-Coder-32B (Apache 2.0)
- Training code: HuggingFace Transformers, PEFT, bitsandbytes (Apache 2.0 / BSD)
- Your modifications: MIT

---

## 🙏 Acknowledgments

- [Qwen](https://github.com/Qwen) for Qwen2.5-Coder base model
- [Hugging Face](https://huggingface.co/) for transformers & PEFT
- [Ollama](https://ollama.ai/) for local inference platform
- [Together AI](https://together.ai/) for cloud inference & fine-tuning

---

## 📚 Documentation

- [API Reference](docs/reference/API.md)
- [Architecture](docs/reference/ARCHITECTURE.md)
- [Setup Guide](docs/guides/SETUP.md)
- [Evaluation Plan](stack-2.9-eval/HUMAN_EVAL_PLAN.md)
- [Tool Reference](TOOLS.md)
- [Pattern Memory Evolution](docs/pattern-moat.md)

---

<p align="center">
  Built with ❤️ for developers who want an AI that grows with them
</p>
