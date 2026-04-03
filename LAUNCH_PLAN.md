# Stack 2.9 Official Launch Plan

This document outlines the steps to officially release Stack 2.9.

---

## Phase 1: Testing & Validation (Immediate)

### 1.1 Unit Tests
```bash
# Run existing tests
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9
python -m pytest samples/ -v

# Expected: All tests pass
```

### 1.2 Integration Tests
```bash
# Test CLI functionality
python -m pytest samples/integration/ -v

# Test tools
python -m pytest samples/unit/test_tools.py -v
```

### 1.3 Model Benchmark
```bash
# Download benchmark datasets
python scripts/download_benchmark_datasets.py --data-dir ./data

# Run HumanEval (164 problems)
python stack/eval/run_proper_evaluation.py \
    --benchmark humaneval \
    --provider ollama \
    --model qwen2.5-coder:7b \
    --k-samples 10 \
    --output-dir ./results

# Run MBPP (500 problems)
python stack/eval/run_proper_evaluation.py \
    --benchmark mbpp \
    --provider ollama \
    --model qwen2.5-coder:7b \
    --k-samples 10 \
    --output-dir ./results
```

### 1.4 Quick Smoke Test
```bash
# Test basic functionality
python stack/eval/simple_test.py
```

---

## Phase 2: Demo & Showcase (Day 1-2)

### 2.1 Create Working Demo
```bash
# Create a simple Gradio demo
cd stack/deploy
python app.py  # Should start web interface
```

### 2.2 Record Demo Video
- Show voice input/output
- Show code generation
- Show tool usage

### 2.3 Create Screenshots
- CLI interface
- Web UI
- API responses

---

## Phase 3: Documentation Finalization (Day 2-3)

### 3.1 Verify All Docs Present
```
README.md              ✅ Main documentation
stack/deploy/FREE_DEPLOYMENT.md  ✅ Free deployment guide
stack/deploy/README.md ✅ Deployment docs
DIRECTORY_STRUCTURE.md ✅ Project structure
```

### 3.2 Update Version
```bash
# Update version in files
- README.md
- pyproject.toml
- package.json
```

---

## Phase 4: Deployment Setup (Day 3-4)

### 4.1 HuggingFace Space
1. Create account at huggingface.co
2. New Space → Docker → Python 3.11
3. Push `stack/deploy/hfSpaces/*`
4. Get public URL

### 4.2 Model Upload
```bash
# Upload fine-tuned model
python stack/training/upload_hf.py \
    --model-path ./output/stack-2.9-7b \
    --repo-id yourusername/stack-2.9-7b
```

### 4.3 Test Free Deployment
```bash
# Test on free tier
cd stack/deploy/hfSpaces
docker build -t stack-2.9 .
docker run -p 7860:7860 stack-2.9
```

---

## Phase 5: Launch & Promote (Day 5-7)

### 5.1 Social Media
- Twitter/X thread
- LinkedIn post
- Hacker News submission
- Reddit r/LocalLLaMA

### 5.2 Platforms
- Submit to [OpenRouter](https://openrouter.ai/)
- Submit to [HuggingFace](https://huggingface.co/)
- Add to [awesome-llm](https://github.com/Hannibal046/Awesome-LLM) list

### 5.3 Community
- Discord server invite
- GitHub discussions

---

## Launch Checklist

| Task | Status | Notes |
|------|--------|-------|
| Unit tests pass | ⬜ | Run `pytest samples/` |
| Integration tests pass | ⬜ | Run `pytest samples/integration/` |
| Benchmarks run | ⬜ | HumanEval + MBPP |
| Demo works | ⬜ | Gradio UI test |
| Free deployment works | ⬜ | HF Spaces test |
| Documentation complete | ⬜ | All docs in place |
| Version updated | ⬜ | Set to 1.0.0 |
| HF Space deployed | ⬜ | Get public URL |
| Model uploaded | ⬜ | To HuggingFace |
| Social media ready | ⬜ | Posts prepared |

---

## Quick Test Commands

```bash
# 1. Test imports
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9
python -c "from stack.eval.model_client import create_model_client; print('OK')"

# 2. Test CLI
python -m stack.cli.cli --help

# 3. Test eval
python stack/eval/simple_test.py

# 4. Run benchmarks
python stack/eval/run_proper_evaluation.py --benchmark humaneval --provider ollama --model qwen2.5-coder:7b --k-samples 5

# 5. Start web UI
cd stack/deploy && python app.py
```

---

## Expected Outcomes

After launch:
- ✅ Working open-source AI coding assistant
- ✅ Free deployment on HF Spaces
- ✅ Fine-tunable on Together AI
- ✅ 46 tool schemas trained
- ✅ OpenAI-compatible API

---

## Contact & Support

- Issues: https://github.com/my-ai-stack/stack-2.9/issues
- Discussions: https://github.com/my-ai-stack/stack-2.9/discussions