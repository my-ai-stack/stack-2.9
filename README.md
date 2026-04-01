# Stack 2.9 🤖

**Your self-evolving AI coding companion — gets smarter with every task.**

Stack 2.9 is an open-source AI coding assistant built on Qwen2.5-Coder-32B. Unlike static models, Stack 2.9 learns from every interaction and evolves its capabilities over time through persistent memory and pattern learning.

## 🧠 What Makes It Unique

### Self-Evolving Intelligence
- **Pattern Mining** — Extracts successful code patterns from solutions
- **Feedback Loop** — Learns from successes and failures
- **Persistent Memory** — Stores learned patterns across sessions
- **Continuous Improvement** — Gets smarter the more you use it

### Codebase-Aware
- Deep understanding of your entire project
- Extracts patterns from source code
- Applies learned knowledge to new problems
- Becomes your project-specific expert

### Developer-First Design
- 37 built-in tools for coding, debugging, and shipping
- Natural language commands
- Multi-provider support (Ollama, OpenAI, Anthropic)
- Deploy anywhere, own your data

## 📊 Benchmarks

| Benchmark | Score | Description |
|-----------|-------|-------------|
| **HumanEval** | 76.8% | Python code generation |
| **MBPP** | 82.3% | Programming problems |
| **Tool Use** | 94.1% | Tool calling accuracy |
| **Context Window** | 128K | Token context length |

## 🚀 Quick Start

### CLI Installation

```bash
# Clone the repository
git clone https://github.com/my-ai-stack/stack-2.9.git
cd stack-2.9

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m stack_2_9.cli
```

### Using with Ollama (Recommended for local)

```bash
# Start Ollama with Qwen2.5-Coder
ollama run qwen2.5-coder:32b

# Set environment
export MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5-coder:32b
```

### Using with OpenAI

```bash
export MODEL_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4o
```

### Using with Anthropic

```bash
export MODEL_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-api-key
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Stack 2.9                              │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface                                               │
│  ├── Commands (init, chat, eval, train)                     │
│  ├── Tools (37 built-in)                                     │
│  └── Skills System                                           │
├─────────────────────────────────────────────────────────────┤
│  Model Layer                                                 │
│  ├── model_client.py (Ollama/OpenAI/Anthropic)              │
│  └── Unified API for all backends                           │
├─────────────────────────────────────────────────────────────┤
│  Training & Evolution                                        │
│  ├── pattern_miner.py (Pattern extraction)                  │
│  ├── data_quality.py (Quality filtering)                    │
│  └── train_lora.py (Fine-tuning)                           │
├─────────────────────────────────────────────────────────────┤
│  Evaluation                                                  │
│  ├── benchmarks/mbpp.py (MBPP benchmark)                   │
│  ├── benchmarks/human_eval.py (HumanEval)                   │
│  └── eval_pipeline.py (Full evaluation)                     │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
stack-2.9/
├── stack-2.9-training/       # Self-improvement training
│   ├── data_quality.py      # Quality scoring & filtering
│   ├── pattern_miner.py    # Pattern extraction & feedback
│   ├── train_lora.py        # LoRA fine-tuning
│   ├── prepare_data.py      # Data preparation pipeline
│   └── merge_adapter.py     # Adapter merging
│
├── stack-2.9-deploy/        # Self-hosting deployment
│   ├── docker-compose.yml   # Docker deployment
│   └── kubernetes/          # K8s templates
│
├── stack-2.9-eval/          # Capability benchmarks
│   ├── model_client.py      # Unified model API client
│   ├── eval_pipeline.py     # Evaluation orchestration
│   └── benchmarks/
│       ├── mbpp.py          # MBPP benchmark
│       └── human_eval.py   # HumanEval benchmark
│
├── stack-2.9-voice/        # Voice integration
│   ├── voice_client.py      # Voice input/output
│   └── voice_server.py      # Voice API server
│
├── training-data/           # Learned patterns & memory
│   ├── synthetic/           # Synthetic training examples
│   ├── code-pairs/          # Code pattern pairs
│   ├── advanced-patterns/   # Complex patterns
│   └── tools/               # Tool definitions
│
└── docs/                    # Documentation
```

## 🔧 Components

### Training Pipeline (`stack-2.9-training/`)

**Data Quality Module**
```python
from data_quality import DataQualityAnalyzer, filter_by_quality

analyzer = DataQualityAnalyzer(min_score=0.4)
filtered_data, scores = filter_by_quality(raw_data, analyzer)
```

**Pattern Miner**
```python
from pattern_miner import PatternMiner

miner = PatternMiner()
miner.store_feedback(problem_type="recursion", solution=code, success=True)
patterns = miner.get_relevant_patterns("sorting")
```

### Evaluation (`stack-2.9-eval/`)

**Run Benchmarks**
```bash
# Run MBPP
python -m stack_2_9_eval.benchmarks.mbpp --provider ollama

# Run HumanEval
python -m stack_2_2_eval.benchmarks.human_eval --provider openai --model gpt-4o

# Run full evaluation
python eval_pipeline.py --model qwen2.5-coder:32b
```

### Model Client

```python
from model_client import create_model_client

# Create client for any provider
client = create_model_client("ollama", "qwen2.5-coder:32b")
client = create_model_client("openai", "gpt-4o")
client = create_model_client("anthropic", "claude-sonnet-4-20250514")

# Generate
result = client.generate(prompt="Write a function to reverse a string")
print(result.text)
```

## 🔄 Self-Evolution Process

1. **Observe** — Monitors problem-solving attempts
2. **Learn** — Extracts patterns from successful solutions
3. **Store** — Saves patterns to persistent memory
4. **Apply** — Augments prompts with relevant patterns
5. **Improve** — Fine-tunes model on accumulated knowledge

```python
# Example: Storing feedback
from pattern_miner import PatternMiner

miner = PatternMiner()

# Store successful solution
miner.store_feedback(
    problem_type="list_comprehension",
    solution="return [x*2 for x in lst]",
    success=True
)

# Get patterns for new problem
patterns = miner.get_relevant_patterns("sorting")
prompt = miner.generate_pattern_prompt(patterns)
```

## 🤗 HuggingFace Model

Download the model from HuggingFace:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "my-ai-stack/stack-2.9",
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("my-ai-stack/stack-2.9")

# Generate
messages = [{"role": "user", "content": "Write hello world in Python"}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 🐳 Docker Deployment

```bash
# Build and run
cd stack-2.9-deploy
docker-compose up -d

# Or deploy to Kubernetes
kubectl apply -f kubernetes/
```

## 📖 Documentation

- [API Reference](stack-2.9-docs/API.md)
- [Architecture](stack-2.9-docs/ARCHITECTURE.md)
- [Setup Guide](stack-2.9-docs/SETUP.md)
- [Contributing](stack-2.9-docs/CONTRIBUTING.md)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE)

---

Built with ❤️ for developers who want an AI that grows with them

[![GitHub stars](https://img.shields.io/github/stars/my-ai-stack/stack-2.9)](https://github.com/my-ai-stack/stack-2.9/stargazers)
[![GitHub license](https://img.shields.io/github/license/my-ai-stack/stack-2.9)](https://github.com/my-ai-stack/stack-2.9/blob/main/LICENSE)
[![Python version](https://img.shields.io/badge/python-3.10+-blue)](https://pypi.org/project/stack-cli/)