# Stack 2.9 Official Launch Checklist

This document outlines the steps to officially launch Stack 2.9.

---

## Phase 1: Testing & Validation

### ✅ 1.1 Run Unit Tests
```bash
cd stack-2.9
python -m pytest samples/ -v
```

### ✅ 1.2 Test Model Inference
```bash
# Test with Ollama (local)
python stack/eval/simple_test.py

# Or test with OpenAI
python stack/eval/simple_test.py --provider openai
```

### ⏳ 1.3 Run Benchmarks (Required)
```bash
# Download datasets
python scripts/download_benchmark_datasets.py

# Run HumanEval
python stack/eval/run_proper_evaluation.py --benchmark humaneval --output results/

# Run MBPP
python stack/eval/run_proper_evaluation.py --benchmark mbpp --output results/
```

### ⏳ 1.4 Test Deployment
```bash
# Test Docker locally
cd stack/deploy
docker build -t stack-2.9 .
docker run -p 8000:8000 stack-2.9
```

---

## Phase 2: Model Preparation

### ⏳ 2.1 Fine-tune Model
```bash
# Option 1: Together AI (free credits)
python stack/training/together_finetune.py --model 7b --data data/final/train.jsonl

# Option 2: Google Colab
# Open colab_train_stack29.ipynb
```

### ⏳ 2.2 Quantize Model (for deployment)
```bash
python stack/training/quantize_awq.py \
    --model Qwen/Qwen2.5-Coder-7B \
    --output stack/deploy/models/
```

### ⏳ 2.3 Upload to HuggingFace
```bash
python -c "
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path='./stack/deploy/models',
    repo_id='yourusername/stack-2.9-7b',
    repo_type='model'
)
"
```

---

## Phase 3: Deployment

### ⏳ 3.1 Deploy to HuggingFace Spaces (Free)
```bash
# 1. Create space: https://huggingface.co/spaces/new
# 2. Choose: Docker, Python 3.11
# 3. Push files:
git clone https://huggingface.co/spaces/yourusername/stack-2.9
cp stack/deploy/hfSpaces/* .
git add . && git push
```

### ⏳ 3.2 Create Demo UI (Gradio)
```bash
# Already included in hfSpaces/app.py
# Access at: https://your-space.hf.space
```

---

## Phase 4: Documentation & Launch

### ⏳ 4.1 Final Documentation Check
- [ ] README.md complete
- [ ] FREE_DEPLOYMENT.md complete
- [ ] API documentation in stack/docs/
- [ ] Examples in samples/

### ⏳ 4.2 Create Release
```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0

# Create GitHub release with:
# - Release notes
# - Model download links
# - Demo links
```

### ⏳ 4.3 Submit to Platforms
- [ ] Submit to OpenRouter (API listing)
- [ ] Submit to HuggingFace (model + Space)
- [ ] Add to LangChain integrations (optional)

---

## Phase 5: Promotion

### ⏳ 5.1 Social Media
- [ ] Announce on Twitter/X
- [ ] Post on LinkedIn
- [ ] Share on AI Discord servers

### ⏳ 5.2 Community
- [ ] Create Discord server
- [ ] Add to awesome lists
- [ ] Submit to Product Hunt

---

## Quick Start (If Everything Ready)

```bash
# 1. Test locally
python stack/eval/simple_test.py

# 2. Deploy to HF Spaces
# (manual - see Phase 3)

# 3. Create release
git tag v1.0.0 && git push origin v1.0.0
```

---

## Current Status

| Item | Status |
|------|--------|
| Unit Tests | ✅ Ready (in samples/) |
| Inference Test | ✅ Ready |
| Benchmarks | ⏳ Need to run |
| Model Fine-tuned | ⏳ Need to do |
| Deployment | ⏳ Need to deploy |
| Release | ⏳ Need to create |