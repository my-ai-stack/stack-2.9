# Gemma 3 Migration Plan

Switching base model from `Qwen/Qwen2.5-Coder-7B` to `google/gemma-3-7b-it`.

---

## 1. What Needs to Change

### Base Model
```
Qwen/Qwen2.5-Coder-7B  →  google/gemma-3-7b-it
```

### Chat Template
| Aspect | Qwen2.5-Coder | Gemma 3 |
|--------|--------------|---------|
| Turn marker | `<|im_start|>role\ncontent<|im_end|>` | `<start_of_turn>role\ncontent<end_of_turn>` |
| Tool calls | `<tool_call>\n<name>...</name>\n<args>...</args>\n</tool_call>` | `function_call` JSON block |
| System prompt | First message or injected | Direct `role: "system"` message |
| Generation prompt | `<|im_start|>assistant\n` | `<start_of_turn>model\n` |

**Action:** Update `data_utils.py` — the `messages_to_text()` function already uses `tokenizer.apply_chat_template()` which handles this automatically for both models. Just pass the right tokenizer.

### LoRA Target Modules

**Qwen2.5-Coder** (all linear layers):
```python
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
```

**Gemma 3** (attention-only — Gemma does NOT expose MLP projections as separate modules):
```python
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
```
**Do NOT include `gate_proj`, `up_proj`, `down_proj`** for Gemma 3 — these module names don't exist in Gemma 3's attention blocks. Including them will cause training to silently skip those params or fail.

**Action:** Create a new config `gemma-3-7b-lora.yaml` with the correct target modules.

### Tokenizer Differences
| | Qwen2.5-Coder | Gemma 3 |
|--|--|--|
| Vocab size | ~151K | ~256K |
| Padding token | Usually `eos_token` | Separate `<pad>` token |
| Chat template | Custom Qwen template | Native Gemma template |

**Action:** Ensure `tokenizer.padding_side = "right"` and set `tokenizer.pad_token = tokenizer.eos_token` (or dedicated pad token) before training.

---

## 2. LoRA Config for Gemma 3

```yaml
# training/gemma-3-7b-lora.yaml
model:
  name: "google/gemma-3-7b-it"
  trust_remote_code: true

lora:
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules:
    - "q_proj"
    - "k_proj"
    - "v_proj"
    - "o_proj"
  bias: "none"
  task_type: "CAUSAL_LM"

training:
  num_epochs: 3
  batch_size: 1
  gradient_accumulation: 16      # Effective batch = 16
  learning_rate: 1.0e-4
  max_grad_norm: 1.0
  warmup_steps: 100
  gradient_checkpointing: true

data:
  max_length: 8192
  train_split: 0.9

quantization:
  enabled: true                   # Enable 4bit QLoRA for single GPU
  bits: 4

output:
  lora_dir: "./output/gemma-3-7b-lora"
```

**Memory estimate:** Gemma 3 7B in 4bit QLoRA ≈ 6-8GB VRAM (vs Qwen 7B 4bit ≈ 5-7GB). Comparable.

---

## 3. Estimated GPU Requirements

| Model | Precision | VRAM |
|-------|-----------|------|
| Qwen2.5-Coder-7B | FP16 | ~18GB |
| Qwen2.5-Coder-7B | 4bit QLoRA | ~6-8GB |
| Gemma 3-7B | FP16 | ~16GB |
| Gemma 3-7B | 4bit QLoRA | ~6-8GB |

**Both fit on a single A100 40GB or T4 16GB with QLoRA.** Gemma 3 is slightly more memory-efficient.

For full fine-tuning (not LoRA): 2x A100 80GB recommended for either model.

---

## 4. Priority Order of Changes

1. **Verify tokenizer.chat_template** for Gemma 3 works with your training data format
2. **Create `gemma-3-7b-lora.yaml`** — correct target modules + model name
3. **Update training script** — handle Gemma's `pad_token` (set `pad_token = eos_token` if None)
4. **Test with 1.5B first** — try `google/gemma-3-1b-it` locally to validate pipeline before 7B
5. **Run full training** — same pipeline, just new config

---

## 5. Key Code Changes

### In `train_simple_nobnb.py` — add Gemma pad_token handling after tokenizer load:

```python
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
```

### Verify chat template works:

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("google/gemma-3-7b-it", trust_remote_code=True)
messages = [{"role": "user", "content": "Hello"}]
print(tok.apply_chat_template(messages, tokenize=False))
# Should output Gemma-formatted string with <start_of_turn> etc.
```

### Test data pipeline with Gemma tokenizer:

```python
from transformers import AutoTokenizer
from training.data_utils import load_chat_data
tok = AutoTokenizer.from_pretrained("google/gemma-3-7b-it", trust_remote_code=True)
tok.pad_token = tok.eos_token
ds = load_chat_data("training/training-data/tool_examples_combined.jsonl", tok, max_length=2048)
print(f"Train: {len(ds[0])}, Eval: {len(ds[1])}")
# Verify labels are correct — non-masked tokens should decode to assistant response
```

---

## 6. Tool Calls Formatting for Gemma 3 (Critical Issue)

Gemma 3 uses a **different tool call format** than Qwen. The current training data uses Qwen's XML format:

```xml
<tool_call>
<name>FileRead</name>
<args>
{"path": "src/main.py"}
</args>
</tool_call>
```

Gemma 3 expects JSON-style function calls in the generated text:

```json
func["FileRead"]({"path": "src/main.py"})
```

This is the biggest compatibility risk. Options:

1. **Convert training data** — write a preprocessing script to transform tool_calls to Gemma's JSON format
2. **Use system prompt** — tell Gemma to use Qwen-style XML in responses (easiest but risky)
3. **Fine-tune on Qwen format anyway** — Gemma can learn any format with enough data

**Recommendation:** Write a data conversion script (`convert_tool_format.py`) that transforms the JSONL data from Qwen's XML format to Gemma's `func["name"]({args})` format. Test with a small sample first.

---

## 7. Quick Start Commands

```bash
# Verify Gemma tokenizer chat template
python3 -c "
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('google/gemma-3-7b-it', trust_remote_code=True)
print(tok.chat_template[:500])
"

# Test data pipeline with Gemma tokenizer
python3 -c "
from transformers import AutoTokenizer
from training.data_utils import load_chat_data
tok = AutoTokenizer.from_pretrained('google/gemma-3-7b-it', trust_remote_code=True)
tok.pad_token = tok.eos_token
ds = load_chat_data('training/training-data/tool_examples_combined.jsonl', tok, max_length=2048)
print(f'Train: {len(ds[0])}, Eval: {len(ds[1])}')
"

# Run training with new config (requires GPU)
python3 training/train_simple_nobnb.py --config training/gemma-3-7b-lora.yaml
```

---

## 8. 7B Adapter Status

**No 7B adapter weights currently exist.** Training was never completed. The `training/output/` directory does not exist and there are no `adapter_model.safetensors` or `adapter_config.json` files anywhere in the project.

To train a 7B adapter:
1. Get GPU access (see below)
2. Fix the data pipeline (DONE — `data_utils.py` created)
3. Update training config to point to `training/training-data/tool_examples_combined.jsonl`
4. Run `python3 training/train_simple_nobnb.py --config training/training-configs/7b-lora-config.yaml`
