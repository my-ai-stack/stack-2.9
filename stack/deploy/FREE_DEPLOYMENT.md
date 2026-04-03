# Free Deployment Guide for Stack 2.9

This guide covers deploying Stack 2.9 on free-tier platforms.

---

## Option 1: HuggingFace Spaces (Free Inference)

### Step 1: Create Space
```bash
# Go to https://huggingface.co/spaces and create new Space
# Choose: Docker, Python 3.11, Small (2CPU 4GB)
```

### Step 2: Push Your Model
```bash
# Upload your fine-tuned model to HF
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="./stack-2.9-7b",
    repo_id="yourusername/stack-2.9",
    repo_type="model"
)
```

### Step 3: Configure API URL
Set environment variable in Space:
- `API_URL`: Your model inference URL
- `HF_TOKEN`: Your HF token

### Step 4: Deploy
```bash
# Clone Space and push files
git clone https://huggingface.co/spaces/yourusername/stack-2.9
cp deploy/hfSpaces/* .
git add . && git push
```

---

## Option 2: Together AI Fine-tuning (Free Credits)

### Free Tier Limits
- Up to 7B model fine-tuning
- Limited training minutes (varies by promotion)
- Requires: Together AI account

### Setup
```bash
# Get API key from https://together.ai
export TOGETHER_API_KEY="your-key"

# Fine-tune 7B model (free-tier friendly)
python stack/training/together_finetune.py \
    --model 7b \
    --data data/final/train.jsonl \
    --epochs 3
```

### Use Fine-tuned Model
```python
from together import Together

client = Together(api_key="your-key")

response = client.chat.completions.create(
    model="your-finetuned-model",
    messages=[{"role": "user", "content": "Write a function"}]
)
```

---

## Option 3: Google Colab (Free Training)

### Run Training
```python
# Open colab_train_stack29.ipynb in Google Colab
# Select GPU runtime (free tier: T4 15GB)

# For 7B model (runs on free tier):
batch_size = 2  # Reduce for 15GB VRAM
gradient_accumulation = 8
```

### Model Sizes for Free Tier
| Model | VRAM Needed | Free Tier? |
|-------|-------------|------------|
| 1.5B | ~4GB | ✅ Yes |
| 3B | ~8GB | ✅ Yes (T4) |
| 7B | ~16GB | ⚠️ Limited |
| 32B | ~64GB | ❌ No |

---

## Option 4: RunPod / Vast.ai (Cheap, Not Free)

### Quick Start
```bash
# Deploy on RunPod (~$0.20/hour for A100)
cd stack/deploy
./runpod_deploy.sh --template runpod-template.json

# Deploy on Vast.ai (~$0.15/hour)
./vastai_deploy.sh --template vastai-template.json
```

---

## Recommended Free Stack

```
┌─────────────────────────────────────────────┐
│  Stack 2.9 Free Deployment Stack           │
├─────────────────────────────────────────────┤
│  Model:    Qwen2.5-Coder-7B               │
│  Fine-tune: Together AI (free credits)      │
│  Deploy:    HuggingFace Spaces (free)       │
│  UI:        Gradio (included in Spaces)   │
└─────────────────────────────────────────────┘
```

## Cost Comparison

| Platform | Cost | What's Free |
|----------|------|-------------|
| HF Spaces | $0 | 2CPU 4GB hosting |
| Together AI | varies | Fine-tuning credits |
| Colab | $0 | ~0.5hr GPU/day |
| RunPod | $0.20/hr | First $10 credit |
| Vast.ai | $0.15/hr | First $5 credit |