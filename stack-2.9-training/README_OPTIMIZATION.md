# Stack 2.9 Optimization Guide

This guide covers optimizing Stack 2.9 for fast, efficient inference while maintaining quality.

## Overview

Stack 2.9 can be quantized from 64GB (bfloat16) down to ~18GB (4-bit) with minimal quality loss, enabling deployment on consumer GPUs.

## Quick Start

```bash
# 1. Quantize the model
python quantize.py \
    --model-path ./output/stack-2.9-merged \
    --output-path ./output/stack-2.9-quantized \
    --method bnb \
    --bits 4

# 2. Benchmark the optimized model
python benchmark_optimized.py \
    --optimized-model ./output/stack-2.9-quantized

# 3. Upload to HuggingFace
python upload_hf.py \
    --model-path ./output/stack-2.9-quantized \
    --repo-id your-username/stack-2.9
```

## Quantization Methods

### 1. BitsAndBytes (Recommended)

Most compatible, good quality, fast inference.

```bash
python quantize.py --method bnb --bits 4
```

**Pros:**
- Works on any GPU
- Fast inference
- No calibration data needed
- Good quality preservation

**Cons:**
- ~4x compression (not the best)

### 2. AWQ (Activation-Aware Weight Quantization)

Best quality/performance ratio, but requires specific hardware.

```bash
python quantize.py --method awq
```

**Pros:**
- Best quality preservation
- Hardware-aware
- Good for specific tasks

**Cons:**
- Requires recent GPU
- May need calibration data

### 3. GPTQ

Good compression, slower inference.

```bash
python quantize.py --method gptq --bits 4
```

**Pros:**
- Excellent compression
- Well-studied method

**Cons:**
- Requires calibration
- Slower inference than AWQ/BNB

## Model Sizes

| Precision | Size | Min GPU VRAM | Quality |
|------------|------|--------------|---------|
| bfloat16 | 64 GB | 80 GB | 100% |
| float16 | 64 GB | 64 GB | 99% |
| int8 | 32 GB | 40 GB | 95% |
| int4 | 18 GB | 24 GB | 90-95% |

## Benchmarking

Compare optimized vs base model:

```bash
python benchmark_optimized.py \
    --base-model Qwen/Qwen2.5-Coder-32B \
    --optimized-model ./output/stack-2.9-quantized \
    --num-runs 5 \
    --test-mmlu
```

Expected results (int4 vs bf16):
- **Speed**: 2-3x faster
- **Memory**: 60-70% reduction
- **Quality**: ~92-95% preserved

## API Server

Deploy an OpenAI-compatible API:

```bash
# Install dependencies
pip install fastapi uvicorn transformers torch

# Start server
python convert_openai.py \
    --model-path ./output/stack-2.9-quantized \
    --port 8000

# Test
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "stack-2.9",
        "messages": [{"role": "user", "content": "Hello!"}]
    }'
```

## vLLM Deployment

For production, use vLLM:

```bash
pip install vllm

vllm serve ./output/stack-2.9-quantized \
    --dtype half \
    --tensor-parallel-size 2 \
    --max-model-len 32768
```

## HuggingFace Upload

```bash
# Upload model
python upload_hf.py \
    --model-path ./output/stack-2.9-quantized \
    --repo-id your-username/stack-2.9 \
    --token hf_your_token

# Upload with Gradio Spaces demo
python upload_hf.py \
    --model-path ./output/stack-2.9-quantized \
    --repo-id your-username/stack-2.9 \
    --add-spaces
```

## Expected Performance

With int4 quantization:

| Metric | Value |
|--------|-------|
| Tokens/sec | 30-50 |
| Memory (GPU) | 18-22 GB |
| Model size | ~18 GB |
| Cold start | 10-20s |

## Quality Preservation

Stack 2.9 maintains ~92-95% quality after int4 quantization:

- Code generation: ~95% (excellent for most tasks)
- Reasoning: ~90% (may struggle with complex logic)
- General knowledge: ~92%

## Troubleshooting

### Out of Memory

```bash
# Try int8 instead of int4
python quantize.py --method bnb --bits 8

# Or use CPU offloading
python convert_openai.py --device-map cpu
```

### Slow Inference

- Use vLLM for 2-3x speedup
- Enable flash attention (if supported)
- Use shorter context

### Quality Issues

- Try GPTQ instead of BNB
- Use int8 instead of int4
- Increase tokens per generation

## Production Checklist

- [ ] Quantize model
- [ ] Benchmark against base
- [ ] Run quality tests
- [ ] Test API endpoints
- [ ] Set up monitoring
- [ ] Configure rate limiting
- [ ] Set up autoscaling
- [ ] Document deployment

## Resources

- [AWQ Paper](https://arxiv.org/abs/2306.06965)
- [GPTQ Paper](https://arxiv.org/abs/2210.17323)
- [vLLM Documentation](https://docs.vllm.ai/)
- [HuggingFace Hub](https://huggingface.co/docs/hub/)