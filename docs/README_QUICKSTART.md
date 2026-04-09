# Stack 2.9 — Quick Start

> **AI coding assistant powered by Qwen2.5-Coder-32B with Pattern Memory.**

```
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9
pip install -r requirements.txt
cp .env.example .env
python stack.py
```

That's it. Keep reading for details.

---

## Prerequisites

- **Python 3.10+**
- **GPU** (optional — runs on CPU via cloud providers too)
- **Git**

---

## Install & Run

```bash
# Clone
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Install
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure (pick a provider below, then edit .env)
cp .env.example .env

# Run!
python stack.py
```

---

## Configure Your Model Provider

Edit `.env` with one of these:

### Ollama (Local, Private) — Recommended
```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:32b
```
```bash
# First: curl -fsSL https://ollama.ai/install.sh | sh && ollama pull qwen2.5-coder:32b
```

### Together AI (Cloud, Fast)
```env
MODEL_PROVIDER=together
TOGETHER_API_KEY=tog-your-key-here
TOGETHER_MODEL=togethercomputer/qwen2.5-32b-instruct
```

### OpenAI (GPT-4o)
```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

### Anthropic (Claude)
```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20240229
```

---

## Usage

### Interactive Chat
```bash
python stack.py
```

### Single Query
```bash
python stack.py -c "Write a Python function to reverse a string"
```

### Evaluate Model (GPU required)
```bash
python evaluate_model.py --model-path ./output/merged --benchmark humaneval
```

### Deploy with Docker
```bash
docker build -t stack-2.9 . && docker run -p 7860:7860 stack-2.9
```

---

## 5-Minute Overview

| Feature | Command |
|---------|---------|
| Start chatting | `python stack.py` |
| Ask one question | `python stack.py -c "your question"` |
| Run benchmarks | `python evaluate_model.py --model-path ./merged --benchmark both` |
| List patterns | `python stack.py --patterns list` |
| Deploy locally | `docker build -t stack-2.9 . && docker run -p 7860:7860 stack-2.9` |

---

## Hardware Requirements

| Model | Minimum | Recommended |
|-------|---------|------------|
| 7B | RTX 3060 (6GB) | A100 40GB |
| 32B | RTX 3090 (24GB) | A100 80GB |

No GPU? Use Ollama on your machine or any cloud provider in `.env`.

---

## Key Links

- 📖 **Full docs:** [docs/QUICKSTART.md](docs/QUICKSTART.md)
- 🔧 **46 tools:** [TOOLS.md](TOOLS.md)
- 🧠 **Pattern memory:** [docs/pattern-moat.md](docs/pattern-moat.md)
- 🚀 **Training guide:** [docs/TRAINING_7B.md](docs/TRAINING_7B.md)
- 🐳 **Kubernetes:** [k8s/](k8s/)

---

## What's Inside

- **Qwen2.5-Coder-32B** — 32B parameter code-specialized model
- **Pattern Memory** — learns from successful interactions
- **46 built-in tools** — file ops, git, shell, search, memory, tasks
- **Multi-provider** — Ollama, OpenAI, Anthropic, Together AI, OpenRouter
- **128K context** — handles large codebases
- **Self-hosted** — full control, private
- **MCP support** — integrates with any Model Context Protocol server
- **Voice-ready** — Coqui XTTS for voice cloning

---

*Built with ❤️ for developers who want an AI that grows with them.*
