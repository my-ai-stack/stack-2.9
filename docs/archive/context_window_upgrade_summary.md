# Context Window Upgrade Summary: 32K → 128K

**Date:** 2026-04-01
**Model:** Qwen2.5-Coder-32B
**Context Window:** Extended from 32,768 tokens to 131,072 tokens (128K)

---

## ✅ Completed Tasks

### 1. Configuration Updates

All configuration files have been updated to reflect 128K context:

- ✅ `training-data/manifest.json` (root & stack-2.9 copies)
- ✅ `training-data/training-config.json` (root & stack-2.9 copies)
- ✅ `stack-2.9-training/prepare_dataset.py` (both copies)
- ✅ `stack-2.9-training/train_lora.py` (both copies)
- ✅ `stack-2.9-deploy/vllm_server.py` (added `max_model_len` and `block_size` support)
- ✅ `training-data-extractor.js` (manifest and training config generation)

### 2. Documentation Updates

- ✅ `stack-2.9-docs/API.md` - Model table shows 131072 context
- ✅ `stack-2.9-docs/OPENROUTER_SUBMISSION.md` - Context Length: 131072 tokens
- ✅ `stack-2.9-docs/OPENROUTER_PACKAGE/modelcard.json` - Updated `context_length` and `max_context`
- ✅ Training READMEs - Tokenization length updated to 131072

### 3. Testing & Benchmarking Infrastructure

Created two comprehensive scripts in `benchmarks/`:

#### test_context_window.py
- Verifies model loads with 128K configuration
- Tests incremental context lengths: 8K, 32K, 64K, 96K, 128K
- Tests with real codebase (entire project)
- Measures memory, throughput, and sample output

#### benchmark_context_lengths.py
- Systematically compares 32K, 64K, 128K
- Runs 5 different coding tasks per context length
- Produces detailed JSON with metrics and summary statistics
- Configurable number of tasks and context lengths

### 4. Documentation

Created `BENCHMARKS.md` with:
- Detailed explanation of changes
- Expected performance characteristics
- Instructions for running tests
- Template for recording results
- Recommendations based on use cases

---

## 🎯 vLLM Configuration for 128K

The vLLM server now defaults to:

```python
LLM(
    model="Qwen/Qwen2.5-Coder-32B",
    max_model_len=131072,     # 128K tokens
    block_size=64,            # Optimized for large context
    gpu_memory_utilization=0.9,
    scheduler_config={'policy': 'fcfs', 'max_batch_size': 16}
)
```

### Environment Variables (Optional)

```bash
export MAX_MODEL_LEN=131072      # Override max context
export BLOCK_SIZE=64            # Block size for PagedAttention
export GPU_MEMORY_UTILIZATION=0.9  # GPU memory fraction
```

---

## 📊 Expected Performance

| Context | VRAM (A100 80GB) | Throughput | Latency Impact |
|---------|-------------------|------------|----------------|
| 32K | ~20-25 GB | Baseline (1.0x) | Fastest |
| 64K | ~35-45 GB | ~0.85x | +15% |
| 128K | ~60-75 GB | ~0.70x | +30% |

**Memory scaling:** Approximately 0.5-1 MB per 1K tokens of context.

---

## 🚀 Next Steps

### Immediate

1. **Run the test script** to verify 128K works:
   ```bash
   python benchmarks/test_context_window.py \
     --max-model-len 131072 \
     --block-size 64
   ```

2. **Run the full benchmark** to collect performance data:
   ```bash
   python benchmarks/benchmark_context_lengths.py
   ```

3. **Update the results** in `BENCHMARKS.md` after testing.

### Deployment

4. **For new deployments:**
   - No changes needed - vLLM defaults are already configured
   - Ensure GPU has sufficient memory (≥ 64GB for 128K)
   - Consider using 4-bit quantization (AWQ) for 48GB+ GPUs

5. **For existing deployments:**
   - Restart vLLM server (it will use new defaults automatically)
   - Monitor GPU memory usage
   - Consider setting explicit `MAX_MODEL_LEN` in environment if needed

### Optimization

6. **Adjust based on workload:**
   - If most requests are < 32K, you can keep `max_model_len=131072` but throughput for small prompts remains unaffected
   - For memory-constrained environments, reduce `max_model_len` to 65536 (still better than original 32768)
   - Tune `block_size` (larger = fewer blocks = slightly less overhead, but less flexible)

---

## ⚖️ Trade-offs

### 128K Advantages
- Can process entire codebases in single prompt
- Long conversations without context truncation
- Multi-file analysis and cross-referencing
- Better support for large configuration files

### 128K Costs
- 2.5-3x VRAM usage compared to 32K
- ~30% reduction in decode throughput
- Requires high-end GPUs (≥ 64GB VRAM) for full utilization

**Recommendation:** Use 128K as the maximum. The vLLM engine efficiently handles smaller prompts, so there's no penalty for supporting 128K if you occasionally need it. Just ensure you have enough GPU memory to handle the worst-case scenarios.

---

## 📝 Files Modified

Here's a complete list of all modified files:

### Configuration
```
training-data/manifest.json
training-data/training-config.json
stack-2.9-training/prepare_dataset.py
stack-2.9/stack-2.9-training/prepare_dataset.py
stack-2.9-training/train_lora.py
stack-2.9/stack-2.9-training/train_lora.py
stack-2.9-deploy/vllm_server.py
training-data-extractor.js
```

### Documentation
```
stack-2.9-docs/API.md
stack-2.9-docs/OPENROUTER_SUBMISSION.md
stack-2.9-docs/OPENROUTER_PACKAGE/modelcard.json
stack-2.9-training/README.md
stack-2.9/stack-2.9-training/README.md
```

### New Files
```
BENCHMARKS.md
benchmarks/test_context_window.py
benchmarks/benchmark_context_lengths.py
context_window_upgrade_summary.md (this file)
```

---

## 🔍 Validation Checklist

Use this checklist to validate the upgrade:

- [ ] `training-data/manifest.json` shows `"max_seq_length": 131072`
- [ ] `training-data/training-config.json` shows `"max_seq_length": 131072`
- [ ] All `prepare_dataset.py` files show `max_length=131072`
- [ ] All `train_lora.py` files show `max_seq_length=131072`
- [ ] `vllm_server.py` has `MAX_MODEL_LEN` environment variable with default 131072
- [ ] `vllm_server.py` includes `block_size` in LLM initialization
- [ ] Documentation files (API.md, modelcard.json) show 131072 context
- [ ] Test script runs successfully and tests up to 128K
- [ ] Benchmark script runs and produces results JSON

---

## 📈 Performance Recommendations

After running benchmarks, adjust these parameters based on your findings:

### For High Throughput (many small requests)
```bash
MAX_MODEL_LEN=131072    # Still support 128K
BLOCK_SIZE=128          # Larger blocks = less overhead
MAX_BATCH_SIZE=32       # Increase if memory allows
```

### For Maximum Context (all 128K requests)
```bash
MAX_MODEL_LEN=131072
BLOCK_SIZE=64           # Default, good balance
MAX_BATCH_SIZE=8        # Reduce to fit memory
GPU_MEM_UTIL=0.95       # Use more of GPU memory
```

### For Mixed Workloads (recommended default)
```bash
MAX_MODEL_LEN=131072
BLOCK_SIZE=64
MAX_BATCH_SIZE=16
GPU_MEM_UTIL=0.9
```

---

## 🆘 Troubleshooting

**Issue:** Out of memory when processing 128K context
**Solution:**
- Enable 4-bit quantization (AWQ/GPTQ)
- Reduce batch size or use tensor parallelism across multiple GPUs
- Consider using CPU offloading for partial layers (not recommended for production)

**Issue:** Throughput seems low with short prompts
**Solution:**
- Verify you're not running in prefill-only mode; the model should handle short prompts efficiently
- Check batch size - smaller batches may be underutilizing GPU

**Issue:** Test script fails to load model
**Solution:**
- Ensure vLLM is installed: `pip install vllm`
- Check CUDA drivers are up to date
- Verify model name/path is correct
- Check GPU memory with `nvidia-smi`

---

## ✨ Summary

The Qwen2.5-Coder-32B model now fully supports its native 128K context window. All configuration, training, and deployment files have been updated. Testing scripts are in place to validate performance across different context lengths.

**Next:** Run the benchmarks, collect measurements, and update `BENCHMARKS.md` with actual performance data to finalize optimal deployment parameters.

---

**Status:** ✅ Configuration Complete | ⏳ Testing Pending
