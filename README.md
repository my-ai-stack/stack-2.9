<p align="center">
  <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9" alt="Stars">
  <img src="https://img.shields.io/github/license/my-ai-stack/stack-2.9?logo=apache" alt="License: Apache 2.0">
   <img src="https://img.shields.io/badge/OpenRouter-Supported-green?logo=openrouter" alt="OpenRouter">
  <img src="https://img.shields.io/badge/Together_AI-Supported-green?logo=databricks" alt="Together AI">
  <img src="https://img.shields.io/badge/Hugging%20Face-Model-green?logo=huggingface" alt="Hugging Face">
  <img src="https://img.shields.io/badge/HumanEval-Evaluation%20In%20Progress-yellow?logo=python" alt="HumanEval">
  <img src="https://img.shields.io/badge/MBPP-Evaluation%20In%20Progress-yellow?logo=python" alt="MBPP">
  <img src="https://img.shields.io/python version/3.10+-blue" alt="Python">
  <img src="https://img.shields.io/discord" alt="Discord">
</p>

---

# Stack 2.9 🤖

<p align="center">
  <strong>The pattern-based AI coding assistant that improves through experience.</strong>
</p>

Stack 2.9 is an open-source AI coding assistant powered by Qwen2.5-Coder-32B. It features **Pattern Memory with Retrieval** - learning from interactions by storing successful patterns and retrieving them for future tasks, becoming more helpful through accumulated experience.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🧠 Pattern Memory** | Learns from interactions. Stores successful patterns, tracks success rates, and retrieves relevant precedents for new tasks |
| **🔊 Voice Integration** | Voice cloning and TTS with Coqui XTTS. Record voice commands and hear responses |
| **🎤 Speech-to-Text** | Voice recording with microphone input, silence detection |
| **🤖 Multi-Provider LLM** | Works with Ollama, OpenAI, Anthropic - unified client with automatic fallback |
| **🔗 MCP Support** | Model Context Protocol integration for extensible tools |
| **🔍 Code Indexing (RAG)** | Semantic code search - index your codebase for intelligent queries |
| **💻 Code Generation** | Evaluation in progress (see Benchmarks section) |
| **🔧 46 Built-in Tools** | File ops, search, shell commands, git, voice tools, MCP tools |
| **🌐 Multi-Provider** | Works with Ollama, OpenAI, Anthropic, OpenRouter, Together AI — or bring your own model |
| **📱 Terminal UI** | Beautiful interactive CLI with chat, benchmarks, and training |
| **🔒 Self-Hosted** | Run locally, own your data, deploy anywhere |

## 📊 Benchmark Evaluation

### Evaluation Status

⚠️ **Important**: The benchmark scores previously listed in this README (76.8% HumanEval, 82.3% MBPP, 94.1% Tool Use) have been **removed pending verification**. An audit of the evaluation infrastructure revealed that:

- **HumanEval & MBPP implementations had only 20 problems** (1-4% of full benchmarks)
- **No proper model inference logs exist** for the claimed numbers
- **Tool Use evaluation lacked a proper benchmark** implementation

These scores were therefore **unverifiable** and potentially misleading.

### Current Evaluation Framework

We are rebuilding the evaluation infrastructure with proper methodology:

**🔬 Recent Enhancement**: This release includes comprehensive documentation improvements, OpenRouter integration, complete tool reference (TOOLS.md), and a full evaluation audit. See [EVALUATION.md](EVALUATION.md) for details.

1. **Official datasets**: HumanEval (164 problems), MBPP (500 problems)
2. **Reproducible runs**: Full logs, config files, and per-problem results
3. **Standard metrics**: Pass@1 with confidence intervals, using k≥100 samples
4. **Transparent methodology**: All code and data publicly available

See [EVALUATION.md](EVALUATION.md) for the full audit report and methodology.

### Running Evaluations

Once datasets are prepared, run proper evaluations:

```bash
# Download official datasets (one-time)
python scripts/download_benchmark_datasets.py --data-dir ./data

# Run evaluation with a model provider
python stack_2_9_eval/run_proper_evaluation.py \
    --benchmark humaneval \
    --provider ollama \
    --model qwen2.5-coder:32b \
    --k-samples 100 \
    --output-dir ./results/humaneval_run
```

Or use the built-in CLI:

```bash
python stack.py --eval all --provider ollama --eval-model qwen2.5-coder:32b
```

### Expected Results (Base Model)

For reference, the base Qwen2.5-Coder-32B typically scores:

- HumanEval: ~70-72% Pass@1
- MBPP: ~75-77% Pass@1

Stack 2.9's fine-tuned performance will be published after proper evaluation.

---



## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Install dependencies
pip install -r requirements.txt
```

### Hardware Requirements

Stack 2.9 requires a GPU for optimal performance. Minimum and recommended configurations:

| Configuration | Minimum | Recommended | Production |
|---------------|---------|-------------|------------|
| **GPU** | NVIDIA 8GB VRAM | NVIDIA 24GB VRAM | NVIDIA 40-80GB (A100/H100) |
| **RAM** | 16GB | 32GB | 64GB+ |
| **Disk** | 20GB free | 50GB free | 100GB+ (NVMe) |
| **CUDA** | 11.8 | 12.1 | 12.1+ |
| **Models** | 7B quantized | 32B quantized | 70B+ quantized |

**Notes:**
- CPU-only mode is possible but extremely slow (not recommended for production)
- AWQ/GPTQ quantization reduces VRAM requirements by ~50%
- Multi-GPU (tensor parallelism) supported for large models
- Ensure NVIDIA drivers and CUDA toolkit are installed

### Free Deployment (No Cost)

Stack 2.9 can be deployed on free platforms:

| Platform | What's Free | How |
|----------|-------------|-----|
| **HuggingFace Spaces** | 2CPU 4GB inference | `stack/deploy/FREE_DEPLOYMENT.md` |
| **Together AI** | Fine-tuning credits | `stack/training/together_finetune.py` |
| **Google Colab** | ~0.5hr GPU/day | `colab_train_stack29.ipynb` |

**Recommended for free tier:**
- Model: `Qwen2.5-Coder-7B` (runs on free GPU)
- Fine-tune: Together AI (free credits)
- Deploy: HuggingFace Spaces (free hosting)

See `stack/deploy/FREE_DEPLOYMENT.md` for detailed guide.
For paid deployment (Docker, RunPod, Vast.ai), see `stack/deploy/README.md`.

### Interactive Chat

```bash
# Start the CLI
python stack.py

# Or use the module
python -m stack_cli.cli
```

### Quick Commands

```bash
# Run a single query
python stack.py -c "Write a hello world function in Python"

# Run benchmarks
python stack.py --eval all --provider ollama
python stack.py --eval mbpp --provider openai --model gpt-4o

# View learned patterns
python stack.py --patterns list
python stack.py --patterns stats
```

---

## 💻 Usage Examples

### Chat Mode

```
$ python stack.py
╔═══════════════════════════════════════════════════════════╗
║              Stack 2.9 - Pattern Memory AI             ║
║              Your AI coding companion                     ║
╚═══════════════════════════════════════════════════════════╝

Main Menu:
  [1] Chat with Stack 2.9
  [2] Run Evaluation
  [3] Manage Patterns
  [4] Train Model
  [5] Settings

Select> 1

[Stack]> Write a function to reverse a string in Python

Here's a simple implementation:

def reverse_string(s):
    return s[::-1]

You: exit
Goodbye!
```

### Programmatic Usage

```python
from stack_cli.cli import StackCLI
from stack_cli.agent import create_agent

# Direct agent usage
agent = create_agent()
response = agent.process("Write a hello world in Python")
print(response.content)

# Or use the model client directly
from stack_2_9_eval.model_client import create_model_client

client = create_model_client("ollama", "qwen2.5-coder:32b")
result = client.generate("Write a function to reverse a string")
print(result.text)
```

### Pattern Mining (Pattern Memory)

```python
from stack_2_9_training.pattern_miner import PatternMiner

miner = PatternMiner()

# Store feedback from successful solutions
miner.store_feedback(
    problem_type="recursion",
    solution="return n * factorial(n-1)",
    success=True
)

# Get patterns for similar problems
patterns = miner.get_relevant_patterns("sorting")
print(f"Found {len(patterns)} relevant patterns")
```

---

## 📊 Benchmarks

⚠️ **Benchmark scores are currently under independent verification.** See [Evaluation Status](#-benchmark-evaluation) above for details.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| **HumanEval** | Pending | Full 164-problem evaluation in progress |
| **MBPP** | Pending | Full 500-problem evaluation in progress |
| **Tool Use** | Pending | Custom tool-calling benchmark to be created |
| **GSM8K** | Not started | Math reasoning evaluation planned |
| **Context** | ✅ 128K | Token context window tested |

---

## ⚙️ Configuration

### Environment Variables

```bash
# Ollama (Recommended for local)
export MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5-coder:32b

# OpenAI
export MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o

# Anthropic
export MODEL_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# OpenRouter
export MODEL_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-or-v1-...
export OPENROUTER_MODEL=qwen/qwen2.5-coder-32b
# Optional: customize referer and title for OpenRouter dashboard
export HTTP_REFERER=https://your-app.com
export X_TITLE="Stack 2.9"

# Together AI (Recommended for Qwen models)
export MODEL_PROVIDER=together
export TOGETHER_API_KEY=tog-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export TOGETHER_MODEL=togethercomputer/qwen2.5-coder-32b-instruct
```

### Configuration File

```yaml
# stack.yaml
model:
  provider: ollama
  name: qwen2.5-coder:32b

training:
  lora_rank: 16
  learning_rate: 3e-4

eval:
  benchmarks:
    - mbpp
    - human_eval
    - gsm8k
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Stack 2.9 CLI                           │
├─────────────────────────────────────────────────────────────┤
│  chat_mode          │  eval_mode  │  pattern_mode  │ train   │
├─────────────────────────────────────────────────────────────┤
│                     Model Client Layer                       │
│         OllamaClient  │  OpenAIClient  │  AnthropicClient  │  OpenRouterClient  │  TogetherClient │
├─────────────────────────────────────────────────────────────┤
│                  Self-Evolution Layer                        │
│    pattern_miner  │  data_quality  │  train_lora           │
├─────────────────────────────────────────────────────────────┤
│                      Base Model                              │
│              Qwen2.5-Coder-32B (or your model)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
stack-2.9/
├── stack_cli/            # CLI interface & agent
│   ├── cli.py           # Main CLI entry point
│   ├── agent.py         # AI agent with tools
│   └── context.py       # Context management
│
├── stack_2_9_eval/       # Evaluation framework
│   ├── model_client.py  # Unified model API
│   └── benchmarks/      # MBPP, HumanEval, GSM8K
│
├── stack_2_9_training/   # Training & evolution
│   ├── pattern_miner.py # Pattern extraction
│   ├── data_quality.py  # Data filtering
│   └── train_lora.py    # Fine-tuning
│
├── stack_2_9_deploy/     # Deployment configs
│   └── docker-compose.yml
│
└── training-data/       # Learned patterns
```

---

## 🔧 Development

### Running Benchmarks

```bash
# Individual benchmarks
python -m stack_2_9_eval.benchmarks.mbpp --provider ollama
python -m stack_2_9_eval.benchmarks.human_eval --provider openai --model gpt-4o
python -m stack_2_9_eval.benchmarks.gsm8k --provider anthropic

# Full evaluation
python -m stack_2_9_eval.eval_pipeline --model qwen2.5-coder:32b
```

### Training

```bash
# Prepare data
python -m stack_2_9_training.prepare_data

# Train LoRA
python -m stack_2_9_training.train_lora --config train_config.yaml

# Merge adapter
python -m stack_2_9_training.merge_adapter --base-model qwen2.5-coder-32b
```

---

## 🐳 Docker

```bash
# Quick start with Docker
cd stack-2.9-deploy
docker-compose up -d

# Access CLI
docker exec -it stack-2.9 python stack.py
```

---

## 📖 Documentation

- [API Reference](stack-2.9-docs/API.md)
- [Architecture](stack-2.9-docs/ARCHITECTURE.md)
- [Setup Guide](stack-2.9-docs/SETUP.md)
- [Contributing](CONTRIBUTING.md)

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Qwen](https://github.com/Qwen) for the base model
- [Hugging Face](https://huggingface.co/) for transformers & PEFT
- [Ollama](https://ollama.ai/) for local inference

---

<p align="center">
  Built with ❤️ for developers who want an AI that grows with them
</p>


### Free Deployment (No Cost)

Stack 2.9 can run on free platforms:

| Platform | What's Free | Recommended For |
|----------|-----------------|-----------------|
| **HuggingFace Spaces** | 2CPU 4GB hosting | API deployment |
| **Together AI** | Fine-tuning credits | Model customization |
| **Google Colab** | ~0.5hr GPU/day | Training experiments |

**Free tier model:** Use Qwen2.5-Coder-7B (runs on free GPU)

See `stack/deploy/FREE_DEPLOYMENT.md` for detailed guide.

For paid options see `stack/deploy/README.md`.
