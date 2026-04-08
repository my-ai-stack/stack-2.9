# Stack 2.9 - Fine-tuned Code Assistant

A 1.5B parameter code generation model, fine-tuned from Qwen2.5-Coder on Stack Overflow Q&A data.

**Model:** [my-ai-stack/Stack-2-9-finetuned](https://huggingface.co/my-ai-stack/Stack-2-9-finetuned)  
**Live Demo:** [stack-2-9-demo](https://huggingface.co/spaces/my-ai-stack/stack-2-9-demo)

## Quick Start

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("my-ai-stack/Stack-2-9-finetuned")
tokenizer = AutoTokenizer.from_pretrained("my-ai-stack/Stack-2-9-finetuned")
```

## Hardware Requirements

| Config | GPU | VRAM |
|--------|-----|------|
| FP16 | RTX 3060+ | ~4GB |
| 8-bit | RTX 3060+ | ~2GB |
| 4-bit | Any modern GPU | ~1GB |

## License

Apache 2.0