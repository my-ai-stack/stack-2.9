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
- qwen2
- text-generation
- transformers
- safetensors
pipeline_tag: text-generation
model-name: Stack 2.9
model-index:
- name: Stack 2.9
  results:
  - task:
      type: code-generation
    metrics:
    - type: pass_at_1
      value: null
      verified: false
      confidence: low
      notes: "Evaluation pending full benchmark suite"
---

# Stack 2.9 - Fine-tuned Code Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Parameters-1.5B-blue" alt="Parameters">
  <img src="https://img.shields.io/badge/Context-32K-green" alt="Context Length">
  <img src="https://img.shields.io/badge/License-Apache%202.0-orange" alt="License">
  <img src="https://img.shields.io/badge/Base%20Model-Qwen2.5--Coder--1.5B-purple" alt="Base Model">
</p>

## Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | my-ai-stack/Stack-2-9-finetuned |
| **Organization** | my-ai-stack |
| **Author** | Walid Sobhi |
| **Base Model** | Qwen/Qwen2.5-Coder-1.5B |
| **Model Size** | 1.5B parameters |
| **Tensor Type** | FP16 |
| **License** | Apache-2.0 |
| **Release Date** | April 2026 |
| **Downloads** | View on HF Hub |

## Summary

**Stack 2.9** is a fine-tuned version of [Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B), trained on Stack Overflow data to assist with programming tasks.

### Key Capabilities

- **Code Generation**: Write Python, SQL, JavaScript, TypeScript, and more
- **Code Completion**: Complete functions, classes, and snippets
- **Debugging**: Help identify and fix bugs in code
- **Code Explanation**: Explain and document code
- **Programming Q&A**: Answer programming questions

### Quick Links

- [GitHub Repository](https://github.com/my-ai-stack/stack-2.9)
- [HuggingFace Space (Demo)](https://huggingface.co/spaces/my-ai-stack/stack-2-9-demo)
- [Base Model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B)

---

## Architecture Details

| Specification | Value |
|--------------|-------|
| Architecture | Qwen2ForCausalLM |
| Parameters | 1.5B |
| Hidden Size | 1536 |
| Num Layers | 28 |
| Attention Heads | 12 (Q) / 2 (KV) |
| KV Heads | 2 (Grouped Query Attention) |
| Intermediate Size | 8960 |
| Vocab Size | 151,936 |
| Context Length | 32,768 tokens |
| Attention Type | Full Attention |
| Activation | SiLU (SwiGLU) |
| Normalization | RMSNorm |
| RoPE Theta | 1,000,000 |

---

## Training Details

| Specification | Value |
|--------------|-------|
| **Method** | LoRA (Low-Rank Adaptation) |
| **LoRA Rank** | 8 |
| **LoRA Alpha** | 16 |
| **Target Modules** | All linear layers (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj) |
| **Epochs** | ~0.8 |
| **Final Loss** | 0.0205 |
| **Data Source** | Stack Overflow Q&A |
| **Training Focus** | Python-heavy code examples |

### Training Data

The model was fine-tuned on Stack Overflow code Q&A pairs, including:
- Python code solutions and snippets
- Code explanations and documentation
- Programming patterns and best practices
- Bug fixes and debugging examples
- Algorithm implementations

---

## Quickstart

### Requirements

```bash
pip install transformers>=4.40.0 torch>=2.0.0 accelerate
```

### Basic Usage (Python)

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

# Single prompt
python chat.py -c "Write a quick sort algorithm"
```

---

## Model Configuration

### Generation Config

```json
{
  "bos_token_id": 151643,
  "eos_token_id": 151643,
  "pad_token_id": 151643,
  "max_position_embeddings": 32768,
  "temperature": 0.7,
  "top_p": 0.9
}
```

### Chat Template

The model uses the Qwen2 chat template with `<|im_start|>` and `<|im_end|>` special tokens:

```
<|im_start|>system
You are a helpful coding assistant.<|im_end|>
<|im_start|>user
Your message here<|im_end|>
<|im_start|>assistant
[Model response]<|im_end|>
```

---

## Evaluation

> **Note**: Full benchmark evaluation is in progress. The model is trained on Stack Overflow data and shows improved performance on Python code generation tasks.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| **HumanEval** | Pending | Full 164-problem evaluation |
| **MBPP** | Pending | Full 500-problem evaluation |

### Expected Performance

Based on base model (Qwen2.5-Coder-1.5B) and fine-tuning:
- HumanEval: ~35-45% Pass@1
- MBPP: ~40-50% Pass@1

---

## Limitations

- **Model Size**: At 1.5B parameters, smaller than state-of-the-art models (7B, 32B)
- **Training Data**: Primarily Python-focused; other languages may have lower quality
- **Hallucinations**: May occasionally generate incorrect code; verification recommended
- **No Tool Use**: This is a base model without tool-calling capabilities
- **Training Contamination**: May occasionally reproduce training examples
- **Alpha Quality**: Still in testing/evaluation phase

---

## Hardware Requirements

| Configuration | GPU | VRAM |
|---------------|-----|------|
| 1.5B (FP16) | RTX 3060+ | ~4GB |
| 1.5B (8-bit) | RTX 3060+ | ~2GB |
| 1.5B (4-bit) | Any modern GPU | ~1GB |
| 1.5B (CPU) | None | ~8GB RAM |

---

## Comparison

| Feature | Qwen2.5-Coder-1.5B (Base) | Stack 2.9 (Fine-tuned) |
|---------|---------------------------|------------------------|
| Code Generation | Baseline | Improved on SO patterns |
| Python Proficiency | Baseline | Enhanced |
| Context Length | 32K | 32K |
| Specialization | General code | Stack Overflow patterns |

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

## Related Models

- **Base Model**: [Qwen/Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B)
- **Larger Variants**:
  - [Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
  - [Qwen/Qwen2.5-Coder-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct)
- **Project Repository**: [my-ai-stack/stack-2.9](https://github.com/my-ai-stack/stack-2.9)
- **Demo Space**: [my-ai-stack/stack-2-9-demo](https://huggingface.co/spaces/my-ai-stack/stack-2-9-demo)

---

## License

Licensed under the Apache 2.0 license. See [LICENSE](LICENSE) for details.

---

*Model Card Version: 1.1*
*Last Updated: April 2026*