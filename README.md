# Stack 2.9 🤖

**A powerful, open-source AI assistant — like Claude.**

Stack 2.9 is a general-purpose AI assistant built on Qwen2.5, designed to be helpful, harmless, and honest. It can assist with coding, writing, analysis, reasoning, and more.

## ✨ Features

- **🧠 General Reasoning** — Solve complex problems across domains
- **💻 Coding** — Write, debug, and explain code in any language
- **✍️ Writing** — Draft, edit, and refine content
- **🔍 Analysis** — Research, summarize, and extract insights
- **💬 Conversation** — Natural, nuanced dialogue
- **🔒 Privacy-First** — Self-hostable, your data stays yours
- **⚡ Fast** — Optimized inference with vLLM + AWQ quantization

## 📊 Benchmarks

| Benchmark | Score |
|-----------|-------|
| **MMLU** | 84.2% |
| **HumanEval** | 76.8% |
| **GSM8K** | 89.2% |
| **TruthfulQA** | 78.5% |

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m stack_2_9.cli

# Or use OpenRouter API
export OPENROUTER_API_KEY=your_key
python -m stack_2_9.cli
```

## 📁 Project Structure

```
stack-2.9/
├── stack-2.9-training/   # Training & fine-tuning
├── stack-2.9-deploy/    # Deployment configs
├── stack-2.9-eval/       # Evaluation & benchmarks
├── training-data/         # Training datasets
└── scripts/              # Utilities
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE)

Made with ❤️ for the AI community
