#!/usr/bin/env python3
"""
Stack 2.9 HuggingFace Upload Script
Pushes the trained model to HuggingFace Hub with proper model card.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_args():
    parser = argparse.ArgumentParser(description="Upload Stack 2.9 to HuggingFace")
    parser.add_argument(
        "--model-path",
        type=str,
        default="./output/stack-2.9-quantized",
        help="Path to quantized model"
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="HuggingFace repo ID (e.g., 'username/stack-2.9')"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="HuggingFace token (or set HF_TOKEN env var)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create private repo"
    )
    parser.add_argument(
        "--create-model-card",
        action="store_true",
        default=True,
        help="Create model card automatically"
    )
    parser.add_argument(
        "--push-to-hub",
        action="store_true",
        default=True,
        help="Actually push to Hub (else just prepare locally)"
    )
    parser.add_argument(
        "--add-spaces",
        action="store_true",
        help="Create Gradio Spaces demo"
    )
    return parser.parse_args()


def get_token():
    """Get HuggingFace token from args or env."""
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_TOKEN")


def create_model_card(args, base_model: str = "Qwen/Qwen2.5-Coder-32B") -> str:
    """Generate model card content."""
    
    # Read existing benchmarks if available
    benchmarks = ""
    benchmarks_path = Path(__file__).parent.parent / "BENCHMARKS.md"
    if benchmarks_path.exists():
        benchmarks_content = benchmarks_path.read_text()
        # Extract key metrics
        if "## Results" in benchmarks_content:
            benchmarks = benchmarks_content.split("## Results")[1].split("#")[0]
    
    model_card = f"""---
title: Stack 2.9
base_model: {base_model}
tags:
- stack-2.9
- open-source
- claude-competitor
- code-generation
- qwen
- fine-tuned
- transformers
pipeline_tag: text-generation
license: apache-2.0
---

# Stack 2.9

Stack 2.9 is a fine-tuned version of Qwen2.5-Coder-32B, specialized for code generation and software development tasks.

## Model Details

- **Base Model**: Qwen2.5-Coder-32B
- **Training Data**: Curated coding examples and educational content
- **Fine-tuning Method**: LoRA + Merge
- **Quantization**: 4-bit (bitsandbytes)

## Quick Start

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "{args.repo_id}",
    torch_dtype="auto",
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained("{args.repo_id}")

# Chat format
messages = [
    {{"role": "system", "content": "You are Stack, a helpful coding assistant."}},
    {{"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}}
]]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Requirements

```bash
pip install transformers>=4.40.0 torch>=2.0.0 accelerate
```

## Inference with vLLM

```bash
vllm serve {args.repo_id} --dtype half
```

## Benchmarks

{benchmarks}

## Limitations

- Trained on limited dataset; may not cover all edge cases
- Context window: 32K tokens
- Model may produce incorrect code; always verify outputs

## License

Apache 2.0 - See LICENSE file for details.

## Citation

```bibtex
@misc{{stack-2.9,
  title = {{Stack 2.9}},
  author = {{Stack Team}},
  year = {{2024}},
  url = {{https://huggingface.co/{args.repo_id}}}
}}
```
"""
    return model_card


def create_gradio_demo(repo_id: str) -> str:
    """Create a simple Gradio demo for the model."""
    demo_code = '''import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load model
MODEL_NAME = "{{REPO_ID}}"

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

def generate(prompt, max_tokens, temperature):
    messages = [
        {"role": "system", "content": "You are Stack, a helpful coding assistant."},
        {"role": "user", "content": prompt}
    ]
    
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=int(max_tokens),
            temperature=temperature,
            do_sample=True
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract just the assistant response
    return response.split("assistant")[-1].strip()

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Textbox(label="Prompt", placeholder="Write a Python function..."),
        gr.Slider(32, 1024, value=512, step=32, label="Max Tokens"),
        gr.Slider(0.1, 1.5, value=0.7, step=0.1, label="Temperature")
    ],
    outputs=gr.Markdown(label="Response"),
    title="Stack 2.9 Demo",
    description="Try Stack 2.9 - a code generation model"
)

demo.launch()
'''
    return demo_code.replace("{{REPO_ID}}", repo_id)


def main():
    args = parse_args()
    
    token = args.token or get_token()
    if not token:
        print("Error: No HuggingFace token provided")
        print("Set HF_TOKEN environment variable or pass --token")
        sys.exit(1)
    
    print("=" * 60)
    print("Stack 2.9 HuggingFace Upload")
    print("=" * 60)
    print(f"Model path: {args.model_path}")
    print(f"Repo ID: {args.repo_id}")
    print(f"Private: {args.private}")
    print("=" * 60)
    
    # Validate model path
    if not os.path.exists(args.model_path):
        print(f"Error: Model path {args.model_path} does not exist")
        sys.exit(1)
    
    # Create model card
    if args.create_model_card:
        print("Creating model card...")
        model_card = create_model_card(args)
        model_card_path = os.path.join(args.model_path, "README.md")
        with open(model_card_path, "w") as f:
            f.write(model_card)
        print(f"  Created: {model_card_path}")
    
    # Push to Hub
    if args.push_to_hub:
        print("\nPushing to HuggingFace Hub...")
        try:
            from huggingface_hub import HfApi, create_repo
            
            # Create repo if needed
            api = HfApi(token=token)
            try:
                create_repo(
                    args.repo_id,
                    token=token,
                    private=args.private,
                    repo_type="model",
                    exist_ok=True
                )
                print(f"  Repo created/verified: {args.repo_id}")
            except Exception as e:
                print(f"  Repo creation: {e}")
            
            # Upload model files
            print("  Uploading model files...")
            api.upload_folder(
                folder_path=args.model_path,
                repo_id=args.repo_id,
                repo_type="model",
                commit_message="Upload Stack 2.9 model"
            )
            
            print(f"\n✓ Successfully uploaded to https://huggingface.co/{args.repo_id}")
            
        except ImportError:
            print("Error: huggingface_hub not installed")
            print("Run: pip install huggingface_hub")
            sys.exit(1)
        except Exception as e:
            print(f"Upload failed: {e}")
            sys.exit(1)
    
    # Create Gradio demo
    if args.add_spaces:
        print("\nCreating Gradio Spaces demo...")
        demo_code = create_gradio_demo(args.repo_id)
        spaces_dir = "./stack-2.9-spaces"
        os.makedirs(spaces_dir, exist_ok=True)
        
        with open(os.path.join(spaces_dir, "app.py"), "w") as f:
            f.write(demo_code)
        
        # Create requirements
        with open(os.path.join(spaces_dir, "requirements.txt"), "w") as f:
            f.write("""gradio
transformers>=4.40.0
torch>=2.0.0
accelerate
""")
        
        # Create Spaces config
        with open(os.path.join(spaces_dir, "README.md"), "w") as f:
            f.write(f"""---
title: Stack 2.9 Demo
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
app_file: app.py
pinned: false
---

# Stack 2.9 Gradio Demo

Live demo of Stack 2.9 code generation model.

[Launch on HuggingFace Spaces](https://huggingface.co/spaces/{args.repo_id.replace('/', '-')})
""")
        
        print(f"  Created: {spaces_dir}/")
        
        # Optionally push to Spaces
        if args.push_to_hub:
            try:
                from huggingface_hub import create_repo
                spaces_repo = args.repo_id.replace("models", "spaces")
                create_repo(spaces_repo, token=token, repo_type="space", exist_ok=True)
                print(f"  Spaces repo: https://huggingface.co/spaces/{spaces_repo}")
            except Exception as e:
                print(f"  Spaces creation: {e}")
    
    print("\n✓ Upload complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())