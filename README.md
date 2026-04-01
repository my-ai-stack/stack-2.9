# Stack 2.9 🤖

**Your intelligent coding companion — built for builders.**

Stack 2.9 is an open-source AI assistant built on Qwen2.5-Coder-32B, designed to help developers ship faster with context-aware intelligence.

## ✨ Features

- **🔧 Code-First** — Writes, debugs, and explains code with deep project context
- **🧠 Context-Aware** — Understands your entire codebase, not just snippets
- **⚡ Fast Inference** — vLLM + AWQ 4-bit quantization (~50 tokens/sec on A100)
- **🔌 Tool-Savvy** — 37 built-in tools for files, Git, search, and execution
- **🤝 Collaborative** — Multi-agent swarm, teammate mode, memory across sessions
- **🔒 Self-Hosted** — Deploy anywhere, your code never leaves your infra

## 📊 Benchmarks

| Benchmark | Score |
|-----------|-------|
| **HumanEval** | 76.8% |
| **MBPP** | 82.3% |
| **Tool Use Accuracy** | 94.1% |
| **GSM8K** | 89.2% |
| **Context Window** | 128K tokens |

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Install
pip install -r requirements.txt

# Run
python -m stack_2_9.cli

# Or with OpenRouter
export OPENROUTER_API_KEY=your_key
python -m stack_2_9.cli
```

## 📁 Project Structure

```
stack-2.9/
├── stack-2.9-training/   # Fine-tuning & LoRA training
├── stack-2.9-deploy/    # RunPod, VastAI, local deploy
├── stack-2.9-eval/       # HumanEval, MBPP, benchmarks
├── training-data/         # Datasets & manifests
└── scripts/              # Data processing & utilities
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE)

Built with ❤️ for developers
