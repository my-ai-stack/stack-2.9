---
language:
- en
license: apache-2.0
tags:
- code-generation
- python
- qwen
- fine-tuned
- stack-overflow
- coding-assistant
- text-generation
model_name: Stack 2.9
---

<p align="center">
  <a href="https://github.com/my-ai-stack/stack-2.9">
    <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9?style=flat-square" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/my-ai-stack/stack-2.9/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/my-ai-stack/stack-2.9?style=flat-square&logo=apache" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/Parameters-1.5B-blue?style=flat-square" alt="Parameters"/>
  <img src="https://img.shields.io/badge/Context-32K-green?style=flat-square" alt="Context"/>
  <img src="https://img.shields.io/badge/HuggingFace-Model-green?style=flat-square&logo=huggingface" alt="Hugging Face"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
</p>

# Stack 2.9 - Fine-tuned Code Assistant

> **A fine-tuned version of Qwen2.5-Coder-1.5B trained on Stack Overflow data**

Stack 2.9 is a code generation model fine-tuned from Qwen2.5-Coder-1.5B on Stack Overflow Q&A data for improved programming assistance.

## Model Overview

| Attribute | Value |
|-----------|-------|
| **Base Model** | Qwen/Qwen2.5-Coder-1.5B |
| **Parameters** | 1.5B |
| **Fine-tuning** | LoRA (Rank 8) |
| **Context Length** | 32,768 tokens |
| **License** | Apache 2.0 |
| **Release Date** | April 2026 |

## Key Capabilities

- **Code Generation**: Write Python, SQL, JavaScript, TypeScript, and more
- **Code Completion**: Complete functions, classes, and snippets
- **Debugging**: Help identify and fix bugs in code
- **Code Explanation**: Explain and document code
- **Programming Q&A**: Answer programming questions

## Quick Links

- [GitHub Repository](https://github.com/my-ai-stack/stack-2.9)
- [HuggingFace Space (Demo)](https://huggingface.co/spaces/my-ai-stack/stack-2-9-demo)
- [Base Model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B)

---

## Quickstart

### Requirements

```bash
pip install transformers>=4.40.0 torch>=2.0.0 accelerate
```

### Python Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "my-ai-stack/Stack-2-9-finetuned"

# Load model and tokenizer
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Create chat messages
messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
]

# Apply chat template
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# Generate
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512,
    temperature=0.7,
    do_sample=True
)

# Decode response
response = tokenizer.decode(
    generated_ids[0][len(model_inputs.input_ids[0]):],
    skip_special_tokens=True
)
print(response)
```

### Interactive Chat

```bash
# See chat.py in repository
python chat.py
```

---

## Hardware Requirements

| Configuration | GPU | VRAM |
|---------------|-----|------|
| 1.5B (FP16) | RTX 3060+ | ~4GB |
| 1.5B (8-bit) | RTX 3060+ | ~2GB |
| 1.5B (4-bit) | Any modern GPU | ~1GB |
| 1.5B (CPU) | None | ~8GB RAM |

---

## Training Details

- **Method**: LoRA (Low-Rank Adaptation)
- **LoRA Rank**: 8
- **LoRA Alpha**: 16
- **Target Modules**: All linear layers (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj)
- **Epochs**: ~0.8
- **Final Loss**: 0.0205
- **Data Source**: Stack Overflow Q&A (Python-heavy)

---

## Limitations

- **Model Size**: At 1.5B parameters, smaller than state-of-the-art models (7B, 32B)
- **Training Data**: Primarily Python-focused; other languages may have lower quality
- **Hallucinations**: May occasionally generate incorrect code; verification recommended
- **No Tool Use**: This is a base model without tool-calling capabilities

---

## Citation

```bibtex
@misc{my-ai-stack/stack-2-9-finetuned,
  author = {Walid Sobhi},
  title = {Stack 2.9: Fine-tuned Qwen2.5-Coder-1.5B on Stack Overflow Data},
  year = {2026},
  publisher = {HuggingFace},
  url = {https://huggingface.co/my-ai-stack/Stack-2-9-finetuned}
}
```

---

## License

Licensed under the Apache 2.0 license. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for developers
</p>