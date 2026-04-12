<p align="center">
  <a href="https://github.com/my-ai-stack/stack-2.9">
    <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9?style=flat-square" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/my-ai-stack/stack-2.9/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/Parameters-1.5B-blue?style=flat-square" alt="Parameters"/>
  <img src="https://img.shields.io/badge/Context-128K-green?style=flat-square" alt="Context"/>
  <img src="https://img.shields.io/badge/Tools-69-orange?style=flat-square&logo=robot" alt="Tools"/>
  <img src="https://img.shields.io/badge/Agents-Multi--Agent-purple?style=flat-square" alt="Multi-Agent"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
  <img src="https://huggingface.co/common-database-badges/loved.svg" alt="Loved"/>
</p>

# Stack 2.9 - AI Agent Framework 🔧

Stack 2.9 is a high-performance AI Agent Framework built around a fine-tuned **Qwen2.5-Coder-1.5B** model. It is designed for autonomous software engineering, multi-agent orchestration, and complex tool-integrated workflows.

## 🌟 Key Highlights

- **57 Production-Ready Tools**: From deep code intelligence (Grep, Glob, FileEdit) to agent orchestration (Spawn, TeamCreate, PlanMode).
- **Cognitive Enhancements**: Integrated Emotional Intelligence, Knowledge Graph RAG, and Advanced NLP pipelines.
- **MCP Support**: Native integration with the Model Context Protocol for standardized tool and resource access.
- **Massive Context**: 128K token window for processing entire repositories.
- **Fine-tuned for Accuracy**: Optimized on Stack Overflow Q&A for high-precision code generation and debugging.

## 🛠️ Architecture Overview

The framework is divided into three core layers:
1. **The Brain**: A LoRA-finetuned Qwen2.5-Coder-1.5B model.
2. **The Toolbelt**: A centralized `ToolRegistry` managing 57+ tools across 13 categories.
3. **The Enhancements**: Modular plugins for sentiment analysis, relationship mapping, and static code auditing.

## 🚀 Getting Started

### Installation
```bash
git clone https://github.com/my-ai-stack/stack-2.9
cd stack-2.9
pip install -r requirements/requirements.txt
```

### Quick Usage
```python
from src.tools import get_registry
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Load the brain
model = AutoModelForCausalLM.from_pretrained("my-ai-stack/Stack-2-9-finetuned")
tokenizer = AutoTokenizer.from_pretrained("my-ai-stack/Stack-2-9-finetuned")

# 2. Access the tools
registry = get_registry()
print(f"Available tools: {len(registry.list())}")
```

## 📂 Project Structure
- `src/tools/`: Implementation of the 57 agent tools.
- `src/enhancements/`: Cognitive modules (EI, Knowledge Graph, NLP).
- `src/mcp/`: Model Context Protocol client and server.
- `stack/eval/`: Benchmark suites and evaluation results.
- `stack/training/`: Fine-tuning pipelines and dataset scripts.

## 📄 Documentation
For detailed information, see the [Model Card](docs/MODEL_CARD.md) and [API Reference](docs/API.md).

---
Built by [Walid Sobhi](https://github.com/my-ai-stack)
