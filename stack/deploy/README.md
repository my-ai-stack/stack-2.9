# 🚀 Stack 2.9 - Pattern-Based AI Coding Assistant

A HuggingFace Spaces demo for Stack 2.9, a pattern-based AI coding assistant powered by Qwen2.5-Coder-7B.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)

## ✨ Features

- **🤖 Qwen2.5-Coder-7B** - State-of-the-art code generation model
- **🔧 7 Integrated Tools** - File operations, git, web search, shell commands
- **🧠 Pattern Memory** - Learns from each interaction
- **⚡ Fast Streaming** - Real-time token-by-token generation
- **💾 4-bit Quantization** - Runs on 16GB GPU (~4GB VRAM)

## 🔧 Available Tools

| Tool | Description |
|------|-------------|
| `file_read` | Read files from the filesystem |
| `file_write` | Write content to files |
| `git_status` | Check git repository status |
| `web_search` | Search the web for information |
| `run_command` | Execute shell commands |
| `create_directory` | Create new directories |
| `list_directory` | List directory contents |

## 🏃‍♂️ Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-repo/stack-2.9.git
cd stack-2.9/space

# Install dependencies
pip install -r requirements.txt

# Run the demo
python app.py --share
```

### HuggingFace Spaces

1. Create a new Space on [HuggingFace](https://huggingface.co/spaces)
2. Select "Gradio" as the SDK
3. Upload the files from this directory:
   - `app.py`
   - `requirements.txt`
   - `README.md`
4. The model will load automatically on startup

## 💻 Usage

### Example Prompts

```
Hello! What can you help me with?
Check git status of this repository
Search for best practices for Python async programming
List the files in the current directory
Write a simple Python function to calculate fibonacci
How do I use Git to create a new branch?
What's your memory of our conversation?
```

### Python API

```python
from app import StackModel, memory

# Initialize model
model = StackModel()
model.load()

# Generate response
response = model.generate("Write a hello world in Python")
print(response)

# Check memory stats
print(memory.get_stats())
```

## 🔐 Environment Variables

- `HF_TOKEN` - Your HuggingFace token for private models (optional)
- `MODEL_ID` - Override default model (default: Qwen/Qwen2.5-Coder-7B-Instruct)

## 📊 Memory System

Stack 2.9 includes a pattern memory system that:

1. **Tracks Interactions** - Records every user-assistant exchange
2. **Learns Patterns** - Identifies frequently used tools
3. **Stores Code** - Saves useful code snippets
4. **Adapts Behavior** - Uses learned context to improve responses

## 🛠️ Tech Stack

- **Model**: Qwen2.5-Coder-7B-Instruct
- **Quantization**: 4-bit (bitsandbytes)
- **Framework**: Gradio 4.0+
- **Backend**: Transformers + Accelerate
- **GPU**: 16GB VRAM recommended

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- [Qwen](https://github.com/QwenLM/Qwen) - Base model
- [HuggingFace](https://huggingface.co/) - Spaces hosting
- [Gradio](https://gradio.app/) - UI framework

---

<div align="center">

Made with ❤️ by Stack 2.9

</div>