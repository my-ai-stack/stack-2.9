# Training Infrastructure Improvements

## Status: Audit Complete — Issues Found & Documented

---

## 🔴 CRITICAL: Data Format Mismatch (Training Won't Run)

### The Problem
All training scripts expect simple text/chat formats, but the actual training data uses a **messages-array format with tool calls**:

```python
# What scripts expect (WRONG):
{"text": "...", "instruction": "...", "output": "..."}

# What the data actually contains (CORRECT):
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": null, "tool_calls": [...]}, {"role": "tool", ...}], "tools": [...]}
```

### Affected Scripts
| Script | Issue |
|--------|-------|
| `train_simple_nobnb.py` | `tokenize_function` looks for `instruction`/`output` fields — these don't exist |
| `train_local.py` | References `./data/final/train.jsonl` — wrong path and wrong format |
| `train_extended_context.py` | Same `text` field assumption — won't tokenize properly |
| `t4-qlora.yaml` | `text_field: "text"` and `dataset_path: "./data/final/train_combined.jsonl"` — wrong |
| `extended-context-128k.yaml` | `dataset_path: "./training-data/final/train.jsonl"` — file doesn't exist |

### Fix Required
A proper data loader that converts the `messages` format to training tokens, handling:
- System message prepending
- Tool-call turns (skip or flatten)
- User/assistant turns for language modeling
- Padding and truncation at `max_length`

---

## 🔴 train_local.py Issues

1. **Broken import path** — `sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stack/training'))` points to a directory that doesn't exist
2. **Wrong data path** — `./data/final/train.jsonl` should be `./training-data/tool_examples_combined.jsonl`
3. **Wrong config path** — `stack/training/train_config_local.yaml` doesn't exist
4. **MPS check bug** — `torch.backends.mps.is_built()` would raise `AttributeError` on non-Apple hardware
5. **No 4-bit quantization** — loads full model in FP32, will OOM on Mac MPS

---

## 🟡 t4-qlora.yaml Issues

1. **Wrong data path**: `./data/final/train_combined.jsonl` doesn't exist
2. **Wrong format field**: `text_field: "text"` won't work with messages format
3. **Includes `neat_ft: false`** — this is not a valid HF TrainingArguments field
4. **No `push_to_hub_model_id`** despite `push_to_hub: true` being templated

---

## 🟡 extended-context-128k.yaml Issues

1. **Wrong data path**: `./training-data/final/train.jsonl` doesn't exist
2. **File references `Qwen/Qwen2.5-Coder-1.5B`** but it's not clear if this model already has extended RoPE config
3. **No verification** that the base model actually has `rope_scaling` in its config.json

---

## 🟡 evaluate_model.py Issues

1. **Wrong HumanEval format** — expects `test_cases` in problem dict, but HumanEval typically uses `canonical_solution` + `test` strings that need to be executed
2. **Code execution sandbox is limited** — only allows specific builtins; many standard library functions missing
3. **No handling** of `assert` statements in test code
4. **`calculate_pass_at_k`** has a bug: `correct_in_k = sum(correct_flags[:min(k, len(correct_flags))])` is wrong for pass@k — should be number of correct out of k samples drawn, not just first k

---

## 🟢 What's Working Well

- **`train_simple_nobnb.py`** — Good mixed precision logic, proper bf16/fp16 detection, paged AdamW optimizer, gradient checkpointing with `use_reentrant=False`
- **Training configs** — Comprehensive hardware-specific settings, well-documented
- **Recipes** — Good documentation of GPU requirements and expected runtimes
- **LoRA config** — Properly targets all relevant modules for Qwen

---

## ✅ Recommended Fixes (Priority Order)

### 1. Fix Data Loaders (Highest Priority)
Add a proper `load_chat_data()` function to `train_simple_nobnb.py`:

```python
def load_chat_data(data_path: str, tokenizer, max_length: int = 2048, train_split: float = 0.9):
    """Load messages-format dataset and convert to training tokens."""
    raw_dataset = load_dataset("json", data_files=data_path, split="train")
    
    def tokenize_messages(example):
        messages = example["messages"]
        # Flatten to: system + user + assistant turns
        text = ""
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "") or ""
            if role == "system":
                text += f"<|system|>\n{content}\n"
            elif role == "user":
                text += f"<|user|>\n{content}\n"
            elif role == "assistant":
                # Skip tool calls in content for now, just use text response
                text += f"<|assistant|>\n{content}\n"
            elif role == "tool":
                text += f"<|tool|>\n{content}\n"
        text += "<|assistant|>"
        
        result = tokenizer(text, truncation=True, max_length=max_length, padding="max_length")
        result["labels"] = result["input_ids"].copy()
        return result
    
    tokenized = raw_dataset.map(tokenize_messages, remove_columns=raw_dataset.column_names)
    # ... train/test split
    return train_dataset, eval_dataset
```

### 2. Fix All Data Paths
| Config File | Current (Wrong) | Correct |
|-------------|-----------------|---------|
| `t4-qlora.yaml` | `./data/final/train_combined.jsonl` | `./training-data/tool_examples_combined.jsonl` |
| `extended-context-128k.yaml` | `./training-data/final/train.jsonl` | `./training-data/tool_examples_combined.jsonl` |
| `train_local.py` | `./data/final/train.jsonl` | `./training-data/tool_examples_combined.jsonl` |

### 3. Fix t4-qlora.yaml
- Remove `neat_ft: false` (not a valid field)
- Add `output_dir` override or create `training-configs/t4-qlora-data-fix.yaml`

### 4. Fix evaluate_model.py
- Add proper HumanEval problem loading (use `openai/humaneval` dataset from HuggingFace)
- Fix pass@k calculation
- Expand safe builtins for code execution

### 5. Fix train_local.py
- Remove broken `stack/training` import path
- Add proper 4-bit quantization support for MPS (or detect CUDA availability)
- Fix data and config paths

---

## 📁 Actual Training Data Location

```
/Users/walidsobhi/stack-2.9/training/training-data/
├── tool_examples.jsonl           (1000 lines)
├── tool_examples_combined.jsonl  (1500 lines)
└── tool_examples.json            (same data, json format)
```

Format: `{"messages": [...], "tools": [...]}` — messages-array with tool calls.

---

## 🚀 Quick Test Command

To verify training would work after fixes:

```bash
cd /Users/walidsobhi/stack-2.9/training
python -c "
from datasets import load_dataset
ds = load_dataset('json', data_files='training-data/tool_examples_combined.jsonl', split='train')
print(f'Total examples: {len(ds)}')
print(f'Keys: {ds.column_names}')
print(f'Example: {ds[0]}')
"
```

Expected output: `['messages', 'tools']` — not `['text']` or `['instruction', 'output']`.

---

## Next Steps

1. Write a proper `load_chat_data()` function in a shared `data_utils.py`
2. Update `train_simple_nobnb.py` to use it
3. Update all YAML configs with correct data paths
4. Test with 1 epoch on small sample
5. Then scale to full training on Kaggle/A100
