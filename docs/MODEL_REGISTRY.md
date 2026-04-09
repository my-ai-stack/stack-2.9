# Stack 2.9 Model Registry

> Version tracking for all Stack 2.9 model variants.

---

## Model Versions

| Version | Status | Date | Base Model | Parameters | Dataset | Performance | Use Case |
|---------|--------|------|------------|------------|---------|-------------|----------|
| `stack-2.9-1.5B` | 🟡 In Training | 2026-04-06 | Llama 3.2-1B | 1.5B | Stack 2.9 dedup | TBD | Research, fine-tuning base |
| `stack-2.9-7B` | 🔴 Planned | TBD | Llama 3.1-8B | 7B | Stack 2.9 dedup | TBD | General-purpose inference |
| `stack-2.9-7B-QLoRA` | 🔴 Planned | TBD | Llama 3.1-8B | 7B (quantized) | Stack 2.9 dedup | TBD | Edge deployment, low-memory |

---

## Version Details

### stack-2.9-1.5B (Current)

- **Status:** In Training
- **Architecture:** Transformer (pretrained)
- **Base Model:** Llama 3.2-1B
- **Parameters:** 1.5B
- **Training Data:** Stack 2.9 deduplicated
- **Context Length:** 128k tokens
- **Vocabulary Size:** ~128K
- **Precision:** BF16
- **Training Hardware:** 8x H100 (TBD确认)
- **Expected Completion:** TBD
- **Notes:** First iteration of Stack 2.9, used as baseline for larger variants

### stack-2.9-7B (Planned)

- **Status:** Planned
- **Architecture:** Transformer (pretrained)
- **Base Model:** Llama 3.1-8B
- **Parameters:** 7B
- **Training Data:** Stack 2.9 deduplicated
- **Context Length:** 128k tokens
- **Vocabulary Size:** ~128K
- **Precision:** BF16
- **Training Hardware:** TBD
- **Expected Start:** TBD
- **Notes:** Scale-up from 1.5B, targeting general-purpose use

### stack-2.9-7B-QLoRA (Planned)

- **Status:** Planned
- **Architecture:** Transformer + QLoRA
- **Base Model:** Llama 3.1-8B
- **Parameters:** 7B (4-bit quantized)
- **Training Data:** Stack 2.9 deduplicated
- **Context Length:** 128k tokens
- **Vocabulary Size:** ~128K
- **Quantization:** 4-bit NF4
- **LoRA Rank:** TBD
- **LoRA Alpha:** TBD
- **LoRA Dropout:** TBD
- **Target Modules:** TBD
- **Notes:** Quantized for consumer GPU deployment (e.g., 24GB VRAM)

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-04-06 | stack-2.9-1.5B | Initial entry — training started |
