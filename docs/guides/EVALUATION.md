# Evaluation Audit & Methodology

**Status:** Under Independent Verification

## Critical Findings

After comprehensive audit of the Stack 2.9 evaluation infrastructure, the following issues were identified:

### 1. Incomplete Test Sets

- **HumanEval**: Only **20 out of 164 problems** (~12%) were evaluated
- **MBPP**: Only **20 out of 500 problems** (~4%) were evaluated

The claimed scores (76.8% HumanEval, 82.3% MBPP) are therefore **not representative** of full benchmark performance.

### 2. Missing Model Inference

Investigation of the evaluation scripts (`human_eval.py`, `mbpp_eval.py`) revealed:

- The scripts return **pre-written canonical solutions** instead of actual model inference
- No API calls to Ollama/OpenAI/Anthropic providers were made
- No model-generated outputs exist in the `results/` directory
- The `results/humaneval.json` file contains 0% failure rate from a broken run

**Conclusion:** The benchmark numbers appear to be fabricated or at best, unverified.

### 3. Tool Use Benchmark Unimplemented

The claimed 94.1% Tool Use score lacks:
- Any proper benchmark dataset
- Defined evaluation methodology
- Reproduction instructions
- Actual model calls to test tool selection accuracy

It appears to be a custom, non-standard metric with no basis in accepted benchmarks.

---

## Proper Evaluation Framework

We have built a new, rigorous evaluation infrastructure:

### Official Datasets

```bash
# Download HumanEval (164 problems) and MBPP (500 problems)
python scripts/download_benchmark_datasets.py --data-dir ./data
```

This script fetches:
- HumanEval from OpenAI's official dataset
- MBPP from Google'sbenchmark suite
- Ensures correct formatting and ground truth solutions

### Unified Evaluation Runner

`stack-2.9-eval/run_proper_evaluation.py` provides:

```bash
python stack_2_9_eval/run_proper_evaluation.py \
    --benchmark humaneval \
    --provider ollama \
    --model qwen2.5-coder:32b \
    --k-samples 100 \
    --output-dir ./results/humaneval_run
```

Features:
- Multi-provider support (Ollama, OpenAI, Anthropic, OpenRouter)
- Proper `pass@k` calculation with confidence intervals
- Per-problem detailed logs (JSON)
- Reproducible random sampling (seeds)
- Parallel evaluation (configurable workers)

### Evaluation Checklist

To ensure transparency, every proper evaluation must:

1. ✅ Use full official benchmark (164 HumanEval, 500 MBPP)
2. ✅ Call real model inference via `model_client.py`
3. ✅ Run with k≥100 samples for pass@1 estimation
4. ✅ Store all generation outputs for audit
5. ✅ Compute standard deviation and confidence intervals
6. ✅ Publish full JSON logs to `results/` directory
7. ✅ Document exact model version, quantization, and provider settings

---

## Current Status

The previously claimed scores have been **removed** from README.md and BENCHMARKS.md. They are replaced with:

| Benchmark | Status | Notes |
|-----------|--------|-------|
| HumanEval | Pending verification | Full 164-problem evaluation setup ready |
| MBPP | Pending verification | Full 500-problem evaluation setup ready |
| Tool Use | Needs benchmark design | 500+ realistic OpenClaw tool-calling test cases required |
| GSM8K | Not started | Math reasoning evaluation planned |

Expected baseline (Qwen2.5-Coder-32B):
- HumanEval: ~70-72% Pass@1
- MBPP: ~75-77% Pass@1

Stack 2.9's fine-tuned performance will be published after running proper evaluations.

---

## What Changed

- Created `scripts/download_benchmark_datasets.py` for official datasets
- Created `stack-2.9-eval/run_proper_evaluation.py` unified runner
- Created `stack-2.9-eval/test_evaluation_setup.py` to validate environment
- Added deprecation warnings to flawed `human_eval.py`, `mbpp_eval.py`, `tool_use_eval.py`
- Updated README.md, BENCHMARKS.md, website pages to remove false claims

---

## How to Publish Verified Scores

1. Prepare datasets: `python scripts/download_benchmark_datasets.py --data-dir ./data`
2. Run evaluation: `python stack-2.9-eval/run_proper_evaluation.py --benchmark humaneval --provider ollama --model qwen2.5-coder:32b --k-samples 100`
3. Review logs in `./results/humaneval_run/` (includes per-problem generations)
4. Update README.md with actual numbers once verified
5. Commit full JSON results to `stack-2.9-eval/results/` for reproducibility

**Do NOT publish** the previously claimed percentages. They are invalid.
