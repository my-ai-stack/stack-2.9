# Scaling Plan: Upgrading from 1.5B to 7B and 32B Models

This document provides a roadmap for scaling the Stack 2.9 model training from the initial 1.5B parameter baseline to larger 7B and 32B parameter models.

## 1. VRAM Requirements & Hardware Strategy

Based on current configurations (`t4-qlora.yaml`, `7b-lora-config.yaml`) and recipes, the following memory requirements are estimated:

| Model Size | Training Method | Precision | Min. VRAM | Recommended Hardware | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1.5B** | QLoRA | 4-bit/FP16 | ~12-14GB | T4 (16GB) | Baseline for experimentation |
| **7B** | QLoRA | 4-bit/FP16 | ~14-15GB | T4 (16GB) | Tight fit; reduce `max_seq_length` to 4k |
| **7B** | QLoRA | BF16 | ~40-60GB | A100 (80GB) | Production standard; supports 32k context |
| **7B** | Full Fine-Tune | BF16 | >80GB | 2x A100 (80GB) | Maximum quality; requires multi-GPU |
| **32B** | QLoRA | 4-bit/BF16 | ~80GB | A100 (80GB) | Very slow on single GPU; reduce seq length |
| **32B** | QLoRA | 4-bit/BF16 | ~320GB | 4x A100 (80GB) | Research grade; uses ZeRO-3/FSDP |

## 2. Dataset Scaling & Data Quality

As model capacity increases, the hunger for high-quality tokens increases to avoid overfitting and maximize the benefit of larger weights.

### Recommended Scaling
- **1.5B $\rightarrow$ 7B**: Increase dataset size by **3x - 5x**. Focus on diversifying tool-use patterns. If using `tool_examples_combined.jsonl`, consider expanding to the `training-data-expanded` sets (e.g., `tool_examples_smart_20k.jsonl`).
- **7B $\rightarrow$ 32B**: Increase dataset size by **another 2x - 3x**. At this scale, synthetic data generation (Self-Instruct) becomes critical to maintain the quality of complex reasoning chains.

### Data Focus Areas
- **Complex Tool Chains**: More examples of multi-step tool calls where the output of one tool is the input to another.
- **Error Recovery**: Examples where the model corrects its own tool-call mistakes.
- **Long Context**: For A100 setups, include more samples with `max_seq_length` > 8k to leverage the larger context window.

## 3. Hyperparameter Adjustments

Larger models require different optimization dynamics to maintain stability and converge efficiently.

| Parameter | 1.5B (Baseline) | 7B (Recommended) | 32B (Research) | Reasoning |
| :--- | :--- | :--- | :--- | :--- |
| **LoRA Rank (r)** | 32 | 64 $\rightarrow$ 128 | 128 $\rightarrow$ 256 | Larger models have more capacity; higher rank captures more nuance. |
| **LoRA Alpha** | 64 | 128 $\rightarrow$ 256 | 256 $\rightarrow$ 512 | Usually $\alpha = 2r$ to maintain signal strength. |
| **Learning Rate** | $2.0 \times 10^{-4}$ | $1.0 \times 10^{-4}$ | $5.0 \times 10^{-5}$ | Larger models are more sensitive; lower LR prevents divergence. |
| **Batch Size** | 1 (GA: 16) | 1-4 (GA: 8-32) | 1-4 (GA: 16-64) | Increase effective batch size to stabilize gradients. |
| **Warmup Steps** | 100 | 100 $\rightarrow$ 500 | 500 | Longer warmup helps larger models stabilize. |
| **Max Seq Length**| 8,192 | 4,096 (T4) / 32k (A100)| 8k $\rightarrow$ 32k | Trade-off between VRAM and context capabilities. |

## 4. Step-by-Step Migration Plan

### Phase 1: The 7B Transition (The "Sweet Spot")
1. **Hardware Setup**: Secure an A100 80GB (recommended) or optimize for T4 16GB.
2. **Config Setup**:
   - Create `configs/7b-lora-config.yaml`.
   - Set `target_modules` to all linear layers (q, k, v, o, gate, up, down).
   - Use `bf16: true` if on A100.
3. **Data Validation**: Run the `messages_to_text` check to ensure the chat template matches the 7B base model (e.g., Qwen2.5-Coder-7B or Gemma-3-7B).
4. **Pilot Run**: Train on a 10% subset of data for 1 epoch to verify loss convergence.
5. **Full Train**: Execute 3 epochs with the expanded dataset.

### Phase 2: The 32B Expansion (The "Research Grade")
1. **Distributed Setup**: Configure a multi-GPU environment (4x A100 80GB).
2. **Memory Optimization**:
   - Enable **DeepSpeed ZeRO-3** or **FSDP** to shard model states across GPUs.
   - Use **4-bit QLoRA** (NF4) to fit the 32B model.
3. **Hyperparameter Tuning**: Drop Learning Rate to $5 \times 10^{-5}$ and increase LoRA Rank to 256.
4. **Scaling Data**: Integrate the `training-data-expanded` datasets.
5. **Evaluation**: Use `evaluate_model.py` to compare the 32B adapter against the 7B version on tool-use benchmarks.

### Phase 3: Model Merge & Deployment
1. **Adapter Merge**: Use `merge_lora.py` to fuse the adapters into the base model.
2. **Quantization**: Apply AWQ or GPTQ quantization (`quantize_awq.py`) for efficient inference.
3. **Benchmark**: Run `benchmark_optimized.py` to verify latency and accuracy.
