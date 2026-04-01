<p align="center">
  <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9" alt="Stars">
  <img src="https://img.shields.io/github/license/my-ai-stack/stack-2.9" alt="License">
  <img src="https://img.shields.io/python version/3.10+-blue" alt="Python">
  <img src="https://img.shields.io/discord" alt="Discord">
</p>

---

# Stack 2.9 🤖

<p align="center">
  <strong>The self-evolving AI coding assistant that gets smarter with every interaction.</strong>
</p>

Stack 2.9 is an open-source AI coding assistant powered by Qwen2.5-Coder-32B. Unlike static models, Stack 2.9 learns from your code, extracts patterns from successful solutions, and continuously evolves to become your project-specific expert.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🧠 Self-Evolving** | Learns from every interaction. Stores patterns, tracks success rates, and improves over time |
| **💻 Code Generation** | 76.8% HumanEval, 82.3% MBPP accuracy on code generation tasks |
| **🔧 37 Built-in Tools** | File ops, search, shell commands, git, and more |
| **🌐 Multi-Provider** | Works with Ollama, OpenAI, Anthropic — or bring your own model |
| **📱 Terminal UI** | Beautiful interactive CLI with chat, benchmarks, and training |
| **🔒 Self-Hosted** | Run locally, own your data, deploy anywhere |

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
║              Stack 2.9 - Self-Evolving AI                ║
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

### Pattern Mining (Self-Evolution)

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

| Benchmark | Score | Description |
|-----------|-------|-------------|
| **HumanEval** | 76.8% | Python code generation |
| **MBPP** | 82.3% | Programming problem solving |
| **Tool Use** | 94.1% | Tool calling accuracy |
| **GSM8K** | 85%+ | Math reasoning |
| **Context** | 128K | Token context window |

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
│         OllamaClient  │  OpenAIClient  │  AnthropicClient   │
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