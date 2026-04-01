# Stack 2.9: Open-Source Voice-Enabled Coding Assistant

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-ready-brightgreen)](https://openrouter.ai)
[![Hugging Face](https://img.shields.io/badge/🤗-Hugging%20Face-yellow)](https://huggingface.co)

**Stack 2.9** is an open-source, voice-enabled AI coding assistant based on Qwen2.5-Coder-32B, fine-tuned on OpenClaw's tool-use patterns. Deploy it yourself or access via OpenRouter.

![Stack 2.9 Architecture](../docs/architecture.png)

## ✨ Features

- **🎤 Voice-First Coding**: Natural voice commands for hands-free development
- **🔧 37 Built-in Tools**: File operations, search, debugging, Git, MCP servers
- **🤖 Advanced Agent System**: Swarm intelligence, teammate collaboration, memory
- **⚡ Fast Inference**: vLLM + AWQ 4-bit quantization (~50 tokens/sec on A100)
- **🔒 Privacy-First**: Self-hostable, no data leaves your infrastructure
- **📊 Comprehensive Evaluation**: Benchmarks on HumanEval, MBPP, GSM8K
- **🎨 Extensible**: Plugin system, custom tools, MCP integration

## 🚀 Quick Start

### Local Deployment (5 minutes)

```bash
# Clone and setup
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Deploy with Docker Compose
./stack-2.9-deploy/local_deploy.sh

# Test the API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "stack-2.9",
    "messages": [{"role": "user", "content": "Write a Python Fibonacci function"}]
  }'
```

### Training Your Own

```bash
# Prepare dataset (already included: 519 examples)
cd stack-2.9-training
./run_training.sh

# Output: stack-2.9-awq/ (quantized model ready for vLLM)
```

### Voice Integration

```bash
# Start voice service
cd stack-2.9-voice
docker-compose up -d

# Use voice chat
python integration_example.py
```

## 🏗️ Architecture

Stack 2.9 consists of several modular components:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Training Pipeline** | LoRA fine-tuning on Qwen2.5-Coder-32B | `stack-2.9-training/` |
| **Deployment** | vLLM server + Docker + cloud scripts | `stack-2.9-deploy/` |
| **Voice Integration** | Speech-to-text + text-to-speech | `stack-2.9-voice/` |
| **Evaluation** | Benchmarks + quality metrics | `stack-2.9-eval/` |
| **Documentation** | API docs + OpenRouter submission | `stack-2.9-docs/` |
| **Training Data** | 519 examples + 4k code pairs | `training-data/` |

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Base Model** | Qwen2.5-Coder-32B |
| **Fine-tuning** | LoRA (r=64, α=128) |
| **Quantization** | AWQ 4-bit |
| **Context Length** | 32,768 tokens |
| **Throughput** | ~50 tokens/sec (A100 80GB) |
| **Tools Supported** | 37 (FileRead, FileWrite, Bash, Grep, MCP, etc.) |

*Benchmarks in progress: HumanEval, MBPP, GSM8K*

## 🔧 Tools

Stack 2.9 inherits all OpenClaw tools including:

- **File Operations**: Read, Write, Edit, Glob, Grep
- **Code Execution**: Bash, PowerShell, LSP, REPL
- **Project Mgmt**: Git, GitHub, tasks, agents
- **Web**: Fetch, Search, MCP servers
- **Memory**: Session memory, team memory
- **Voice**: Speech synthesis, voice cloning (optional)

See `stack-2.9-docs/API.md` for complete tool reference.

## 🌐 Deployment Options

### 1. Local (Docker)
```bash
cd stack-2.9-deploy
./local_deploy.sh
```
Services: vLLM API (8000), Prometheus (9090), Grafana (3000)

### 2. Cloud (RunPod/Vast.ai)
```bash
cd stack-2.9-deploy
./runpod_deploy.sh   # or ./vastai_deploy.sh
```
Automated GPU allocation, model downloading, health checks.

### 3. OpenRouter
Once approved, access via:
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "HTTP-Referer: https://github.com/my-ai-stack/stack-2.9" \
  -H "X-Title: Stack 2.9" \
  -d '{
    "model": "my-ai-stack/stack-2.9",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas needing help:**
- More training data (conversation logs, code-comment pairs)
- Evaluation on additional benchmarks
- Voice model improvements (lower latency, better quality)
- IDE integrations (VS Code, JetBrains)
- Additional MCP servers

## 📄 License

Apache 2.0 - You can use, modify, and distribute freely. See [LICENSE](LICENSE).

## 🙏 Acknowledgments

- **OpenClaw** - Architecture and tool patterns
- **Qwen Team** - Base model (Qwen2.5-Coder-32B)
- **vLLM** - High-performance inference engine
- **Unsloth** - Efficient LoRA fine-tuning
- **Hugging Face** - Model hosting and community

## 📚 Documentation

- [API Reference](stack-2.9-docs/API.md)
- [Training Guide](stack-2.9-docs/TRAINING_DATA.md)
- [Voice Integration](stack-2.9-docs/VOICE_INTEGRATION.md)
- [OpenRouter Submission](stack-2.9-docs/OPENROUTER_SUBMISSION.md)
- [Benchmarks](stack-2.9-docs/BENCHMARKS.md)

## 🔗 Links

- **GitHub**: https://github.com/my-ai-stack/stack-2.9
- **Hugging Face**: (coming soon after training)
- **OpenRouter**: (submission in progress)
- **Discord**: (community coming soon)

---

**Stack 2.9** - Code by voice, open for everyone.
