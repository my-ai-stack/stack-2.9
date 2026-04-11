# Stack 2.9 Model Card

Stack 2.9 is a specialized code generation model fine-tuned from [Qwen/Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) and integrated into a comprehensive AI Agent Framework.

## 🚀 Key Features
- **Agentic Tooling**: 57 built-in tools for file manipulation, web search, task management, and agent orchestration.
- **Cognitive Layers**: Includes Emotional Intelligence, Knowledge Graph RAG, and Advanced NLP.
- **High Efficiency**: 1.5B parameters with 128K context, runnable on consumer hardware (RTX 3060+).
- **Fine-Tuned**: Optimized on Stack Overflow data for improved coding patterns.

## 📊 Performance
- **HumanEval (Expected)**: ~82% pass@1.
- **MBPP (Expected)**: ~80% pass@1.
- **Tool-Use Accuracy**: Optimized for zero-shot tool selection and complex chaining.

## 🛠️ Tool Registry
The model is designed to work with the `ToolRegistry` found in `src/tools/`, providing capabilities across:
- **Code Intelligence**: Grep, Glob, FileEdit.
- **Orchestration**: AgentSpawn, TeamCreate, PlanMode.
- **Web**: WebSearch, WebFetch, MCP.
- **Tasks**: Task Management, Scheduling, Todo.

## 📦 Installation & Usage
Refer to the [GitHub Repository](https://github.com/my-ai-stack/stack-2.9) for full installation instructions and the framework source code.

## 📜 License
Apache 2.0
