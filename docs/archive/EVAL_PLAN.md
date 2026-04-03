# Evaluation Plan - Stack 2.9

## Overview

This document outlines the comprehensive evaluation plan for Stack 2.9, detailing the methodology, hardware requirements, timeline, and result publication strategy. The evaluation will be conducted post-training to provide rigorous performance benchmarks across multiple dimensions.

## Evaluation Objectives

1. **Quantify Coding Ability**: Measure performance on standard coding benchmarks (HumanEval, MBPP, SWE-bench)
2. **Assess Tool Use Proficiency**: Evaluate OpenClaw-specific tool calling accuracy and workflow completion
3. **Validate Voice Integration**: Test voice command processing and response generation quality
4. **Benchmark Efficiency**: Measure throughput, latency, and hardware requirements
5. **Ensure Quality**: Comprehensive testing before OpenRouter listing and public release

## Hardware Requirements

### Primary Evaluation Environment
- **GPU**: NVIDIA A100 80GB (or equivalent) with CUDA 12.x
- **Count**: Minimum 2 GPUs for parallel evaluation (reduces total time)
- **CPU**: 16+ cores (AMD EPYC / Intel Xeon)
- **RAM**: 128GB+ system memory
- **Storage**: 2TB NVMe SSD for datasets and model checkpoints
- **Network**: High-speed interconnect (NVLink) for multi-GPU setups

### Optional/Alternative Configurations
- **H100 80GB**: Faster inference for time-sensitive evaluations
- **A100 40GB**: Sufficient for quantization tests (4-bit models)
- **Multi-node cluster**: For distributed evaluation across multiple machines

### Software Stack
- **OS**: Ubuntu 22.04 LTS (or similar)
- **Deep Learning Framework**: PyTorch 2.1+ with CUDA support
- **Inference Engine**: vLLM 0.4+ for throughput benchmarking; Hugging Face Transformers for accurate sampling
- **Quantization**: AWQ, GPTQ, bitsandbytes for 4-bit/8-bit evaluations
- **Evaluation Libraries**: LangChain (for tool use), pytest (for code execution), custom scripts

## Benchmark Suite

### 1. HumanEval (OpenAI)
- **Description**: 164 Python coding problems requiring function completion
- **Metrics**: Pass@1, Pass@10, Pass@100 (with 100+ generations for robust estimates)
- **Format**: Single function completion with unit test verification
- **Expected Time**: 2-4 hours (depending on batch size and parallelism)
- **Resource Estimate**: ~20GB VRAM for 32B model in FP16; ~10GB for 4-bit quantized

### 2. MBPP (Mostly Basic Python Programming)
- **Description**: 500 Python function synthesis problems from Google
- **Metrics**: Pass@1, execution accuracy, time to solution
- **Format**: Function generation with multiple test cases per problem
- **Expected Time**: 6-10 hours
- **Resource Estimate**: Similar to HumanEval

### 3. SWE-bench
- **Description**: Real-world GitHub issues requiring code modifications (full repository context)
- **Metrics**: Resolution rate (percentage of issues fully resolved), edit similarity, test pass rate
- **Format**: Multi-file problem solving with repository-level context
- **Expected Time**: 24-48 hours (most intensive)
- **Resource Estimate**: 80GB VRAM required for 128K context; may need sequence parallelism

### 4. Custom Tool Use Benchmark (OpenClaw)
- **Description**: 500 tasks covering OpenClaw-specific operations:
  - File operations (read, write, move, delete, search)
  - System commands (process management, environment queries)
  - API calls (HTTP requests, data transformation)
  - Multi-step workflows (combining multiple tools)
  - Error handling and recovery
- **Metrics**: Task completion rate (%), tool call accuracy (%), parameter correctness (%), workflow success (%)
- **Expected Time**: 4-6 hours
- **Resource Estimate**: Similar to HumanEval

### 5. Long Context Benchmark (Custom)
- **Description**: Synthetic and real-world tasks requiring 64K-128K token context
- **Metrics**: Accuracy at different context lengths (8K, 32K, 64K, 128K)
- **Format**: Needle-in-haystack tests, multi-document Q&A, long codebase reasoning
- **Expected Time**: 2-3 hours
- **Resource Estimate**: 80GB VRAM for full context; may need FlashAttention or similar optimizations

### 6. Additional Evaluations (Optional)
- **GSM8K**: Mathematical reasoning (1319 problems) — 2-3 hours
- **MMLU**: Multidisciplinary knowledge (optional) — 4-6 hours
- **Voice Integration**: Speech-to-text + code generation latency and accuracy (requires additional audio dataset)
- **Throughput Benchmark**: Tokens/second under various configurations (batch sizes, quantization)

## Evaluation Process

### Phase 1: Preparation (Pre-Evaluation)
1. **Environment Setup**
   - Provision hardware with appropriate drivers and CUDA
   - Install dependencies (PyTorch, vLLM, evaluation scripts)
   - Download model weights from Hugging Face or local storage
   - Prepare datasets (HumanEval, MBPP, SWE-bench, custom tool benchmark)

2. **Validation**
   - Smoke test: Generate on 5 examples from each benchmark
   - Verify evaluation scripts are functioning correctly
   - Check that output format matches expected submission format
   - Ensure results are being recorded in structured format (JSON/CSV)

### Phase 2: Execution (Core Evaluation)

#### Schedule (Parallelized Where Possible)
```
Day 1:
- Morning (4h): HumanEval (batch on 2 GPUs)
- Afternoon (4h): MBPP (batch on 2 GPUs)
- Evening: Preliminary results review

Day 2:
- Morning (4h): Tool Use Benchmark (batch on 2 GPUs)
- Afternoon (4h): Long Context Benchmark (single GPU with 80GB)
- Evening: Throughput benchmarking (various configs)

Day 3:
- Full day (12h): SWE-bench (single GPU, longest-running)
- Night: GSM8K and optional evaluations (if hardware available)

Day 4:
- Morning: Final data collection
- Afternoon: Result aggregation and verification
- Evening: Generate preliminary report draft
```

#### Parallelization Strategy
- **Independent benchmarks** (HumanEval, MBPP, Tool Use) can run concurrently on separate GPUs
- **SWE-bench** requires most memory; run sequentially on dedicated GPU
- **Long context** tests require full 80GB; schedule during off-peak
- **Throughput tests** can interleave with other benchmarks (minimal impact)

### Phase 3: Analysis and Reporting

1. **Data Aggregation**
   - Collect all JSON results into master spreadsheet
   - Compute pass@k metrics with confidence intervals
   - Cross-validate between benchmark runs (re-run if variance >2%)

2. **Comparative Analysis**
   - Compare against Qwen2.5-Coder-32B baseline (where publicly available)
   - Benchmark against similar models (CodeLlama-34B, StarCoder2-15B, etc.)
   - Tabulate results in standardized format

3. **Report Generation**
   - Create detailed markdown report with methodology
   - Generate summary tables for quick reference
   - Include error analysis and failure case examples
   - Document any issues or anomalies encountered

4. **Result Verification**
   - Have 2+ team members independently verify calculations
   - Re-run suspicious or outlier results
   - Ensure reproducibility claims are valid

## Result Publication Strategy

### 1. Immediate Release (Upon Completion)
- **BENCHMARKS.md**: High-level summary table with scores and basic metrics
- **BENCHMARKS_DETAILED.md**: Full results, methodology, and sample outputs
- **GitHub Release**: Tag with benchmark results and evaluation scripts
- **OpenRouter Dashboard Update**: Push verified metrics to model listing

### 2. Comprehensive Report (Within 1 Week)
- **PDF Report**: Professional formatted document for archival
- **Blog Post**: Community announcement with key findings and insights
- **Social Media**: Twitter/LinkedIn posts highlighting achievements
- **Conference Submission**: Consider submitting to ML/AI conferences

### 3. Long-term Archiving
- **Zenodo/Figshare**: DOI-minted archive of datasets and results
- **Papers with Code**: Submission for reproducibility tracking
- **Model Cards**: Update Hugging Face model card with final metrics
- **OpenRouter Documentation**: Permanent listing of verified performance

## Quality Assurance

### Reproducibility
- Publish all evaluation scripts and configuration files
- Provide Docker containers or conda environments for exact replication
- Document random seeds and sampling parameters
- Include generated outputs for sampling-based benchmarks

### Validation Checks
- **Consistency**: Same results across multiple runs (within statistical variance)
- **Sanity Checks**: No impossible scores (>100% pass@k), reasonable standard errors
- **Baseline Comparison**: Qwen2.5-Coder-32B baseline reproduced if possible
- **Failure Analysis**: Review failed cases for systematic issues

### Transparency
- Report both median and mean scores where applicable
- Include confidence intervals and standard deviations
- Document any exclusions or filtering applied to benchmarks
- Acknowledge limitations of each benchmark

## Sample Evaluation Script (Template)

```bash
#!/bin/bash
# Stack 2.9 Benchmark Evaluation Runner
# Usage: ./run_eval.sh <benchmark_name>

set -e

MODEL_PATH="Qwen/Qwen2.5-Coder-32B-Instruct"
OUTPUT_DIR="./eval_results"
BENCHMARK=$1

mkdir -p $OUTPUT_DIR

case $BENCHMARK in
  "humaneval")
    # HumanEval evaluation
    python -m evaluate.humaneval \
      --model $MODEL_PATH \
      --output $OUTPUT_DIR/humaneval.json \
      --temperature 0.2 \
      --top_p 0.95 \
      --num_samples 100
    ;;

  "mbpp")
    # MBPP evaluation
    python -m evaluate.mbpp \
      --model $MODEL_PATH \
      --output $OUTPUT_DIR/mbpp.json \
      --temperature 0.2 \
      --top_p 0.95
    ;;

  "tool_use")
    # Custom tool use benchmark
    python -m evaluate.tool_use \
      --model $MODEL_PATH \
      --dataset ./data/tool_benchmark_500.json \
      --output $OUTPUT_DIR/tool_use.json
    ;;

  "swebench")
    # SWE-bench evaluation
    python -m evaluate.swe_bench \
      --model $MODEL_PATH \
      --split test \
      --output $OUTPUT_DIR/swebench.json \
      --max_context 128000
    ;;

  *)
    echo "Unknown benchmark: $BENCHMARK"
    exit 1
    ;;
esac

echo "Evaluation complete: $BENCHMARK results saved to $OUTPUT_DIR"
```

## Timeline Summary

| Phase | Duration | Milestones |
|-------|----------|------------|
| **Training** | 2-4 weeks | Model fine-tuning complete |
| **Prep** | 3-5 days | Environment setup, datasets downloaded, smoke tests |
| **Execution** | 4-7 days | Run all benchmarks (parallelized) |
| **Analysis** | 3-5 days | Data aggregation, verification, report writing |
| **Publication** | 2-3 days | Documentation updates, GitHub release, OpenRouter listing |
| **Total** | **3-5 weeks** | From training completion to public results |

### Key Dates
- **Training Completion Target**: [To be determined based on training schedule]
- **Start Evaluation**: Day 0 (immediately after training)
- **Preliminary Results**: Day 7
- **Final Verified Results**: Day 14-21
- **Public Release**: Day 21-28

## Risk Mitigation

### Potential Issues and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Hardware failure** | High downtime | Use cloud GPU instances with auto-recovery; keep backups |
| **Dataset access issues** | Evaluation delay | Pre-download all datasets; mirror critical benchmarks |
| **Model loading crashes** | Evaluation blocking | Test model loading thoroughly before starting; have checkpoint recovery |
| **Memory overflow** | Benchmark crashes | Use gradient checkpointing, quantization; monitor VRAM usage |
| **Variance in results** | Reliability concerns | Run multiple seeds; average results; report confidence intervals |
| **Time overruns** | Delayed publication | Prioritize key benchmarks (HumanEval, Tool Use) if needed; run SWE-bench offline |

## Success Criteria

The evaluation will be considered successful if:

1. ✅ All planned benchmarks (HumanEval, MBPP, Tool Use) complete successfully
2. ✅ SWE-bench evaluation produces valid results (or documented limitations)
3. ✅ Results are reproducible (same script yields consistent scores across runs)
4. ✅ Scores are competitive with base Qwen2.5-Coder-32B model (no significant regression in coding)
5. ✅ Tool use accuracy exceeds 85% (target for fine-tuning success)
6. ✅ Full documentation published within 4 weeks post-training
7. ✅ OpenRouter listing updated with verified metrics

## Contact

For questions about the evaluation plan or to request early access to results, contact:

**Evaluation Lead**: OpenClaw Research Team  
**Email**: evals@openclaw.org  
**GitHub Issues**: https://github.com/openclaw/stack-2.9/issues

---

**Last Updated**: 2025-04-01  
**Status**: Draft - Awaiting training completion
