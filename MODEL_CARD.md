---
language:
- en
- code
library_name: transformers
license: apache-2.0
tags:
- code generation
- python
- qwen
- fine-tuned
- stack-overflow
- coding-assistant
---

# Stack 2.9 Fine-tuned

A fine-tuned version of [Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) trained on Stack Overflow data.

## Model Details

- **Base Model:** Qwen/Qwen2.5-Coder-1.5B
- **Architecture:** Transformer decoder with grouped query attention
- **Parameters:** 1.5B
- **Context Length:** 8,192 tokens
- **Precision:** FP16
- **Trained on:** Stack Overflow Q&A data

## Capabilities

✅ **Code Generation** — Write Python, SQL, JavaScript, and more  
✅ **Code Completion** — Complete functions and snippets  
✅ **Programming Help** — Debug, explain, and refactor code  
✅ **Natural Language** — Answer questions and chat  

## Usage

### Python (Transformers)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("my-ai-stack/stack-2-9-finetuned")
tokenizer = AutoTokenizer.from_pretrained("my-ai-stack/stack-2-9-finetuned")

prompt = "def quick_sort(arr):"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Interactive Chat

```python
# See chat.py in the repo for an interactive CLI
```

## Training Details

- **Method:** LoRA fine-tuning
- **Rank:** 8
- **Epochs:** ~0.8
- **Final Loss:** 0.0205
- **Data:** Stack Overflow code Q&A

## Limitations

⚠️ **Training Contamination** — May occasionally repeat training examples  
⚠️ **Small Model** — 1.5B params; larger models (7B, 32B) perform better  
⚠️ **Single Language** — Primarily trained on Python-heavy data  
⚠️ **No Tool Use** — This is a base model, not an agent  

## Citation

```bibtex
@misc{my-ai-stack/stack-2-9-finetuned,
  author = {Walid Sobhi},
  title = {Stack 2.9 Fine-tuned on Stack Overflow},
  year = {2026},
  publisher = {HuggingFace},
  url = {https://huggingface.co/my-ai-stack/stack-2-9-finetuned}
}
```

## Contact

- **GitHub:** [my-ai-stack/stack-2.9](https://github.com/my-ai-stack/stack-2.9)
- **Author:** Walid Sobhi
