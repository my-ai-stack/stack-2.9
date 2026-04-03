# Google Colab Training Guide for Stack 2.9

This guide walks through training Stack 2.9 Pattern Memory LoRA adapters using **free Google Colab** T4 GPUs.

---

## ⚡ Quick Start (3-5 hours)

1. **Open Colab**: https://colab.research.google.com/
2. **Upload** `colab_train_stack29.ipynb`
3. **Runtime → Change runtime type → GPU (T4)**
4. **Run all cells sequentially**

That's it! The notebook handles everything.

---

## 📋 Prerequisites

- Google account (for Colab)
- Basic understanding of notebook execution
- (Optional) Google Drive for persistent storage

---

## 🎯 What This Covers

1. **Setting up the environment** on Colab
2. **Mounting Google Drive** to keep your data between sessions
3. **Installing dependencies** (PyTorch, Transformers, PEFT, etc.)
4. **Preparing training data** (either full or mini dataset)
5. **Training LoRA adapter** on Qwen2.5-Coder-7B (or 32B if you have A100)
6. **Merging adapter** with base model
7. **Testing inference** with the trained model
8. **Exporting to Hugging Face Hub** (optional)

---

## ⏱️ Estimated Timings (T4 GPU)

| Step | Duration |
|------|----------|
| Environment setup | 5-10 min |
| Data preparation | 2-5 min (using mini dataset) / 30-60 min (full dataset) |
| Training (2 epochs, 7B) | 3-5 hours |
| Adapter merging | 2-3 min |
| Inference testing | 1-2 min |
| **Total** | **~4-6 hours** |

**Note:** Colab free tier has ~12 hour runtime limit. Training fits within this.

---

## 💾 Storage Strategy

### Option A: Google Drive (Recommended for persistence)

```python
from google.colab import drive
drive.mount('/content/drive')
# Data stored in /content/drive/MyDrive/stack-2.9/
```

**Pros:** Data persists after runtime disconnect, no re-upload needed.

### Option B: Local Colab storage (ephemeral)

```bash
# Data stored in /content/stack-2.9/
# Lost when runtime disconnects (~12 hours max)
```

**Use for:** Quick experiments, one-off training runs.

---

## 🧠 Memory Optimization for T4 (15GB VRAM)

The provided `train_config_colab.yaml` is tuned specifically for T4:

- **Base model**: `Qwen/Qwen2.5-Coder-7B` (4-bit ≈ 4.5GB)
- **Context length**: 8192 (instead of 131072)
- **Batch size**: 1 (with gradient accumulation 16)
- **LoRA rank**: 16 (instead of 64)
- **4-bit quantization**: `load_in_4bit=True`
- **8-bit optimizer**: `paged_adamw_8bit`
- **Gradient checkpointing**: Enabled
- **BF16 precision**: Enabled

**Total expected VRAM usage**: ~10-12GB (leaves headroom)

---

## 🛠️ Step-by-Step Instructions

### 1. Notebook Setup

Open `colab_train_stack29.ipynb` in Colab. It contains pre-filled cells with:

- Dependency installation
- Drive mounting (optional)
- Clone repo / upload data
- Copy training config
- Run training
- Merge adapter
- Test inference

### 2. Install Dependencies

The notebook installs:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers==4.40.0 peft==0.10.0 accelerate bitsandbytes==0.43.0 datasets pyyaml
```

Takes ~5 minutes.

### 3. Prepare Training Data

**For quick prototyping** (recommended first run):

```bash
python scripts/create_mini_dataset.py --size 5000 --output data_mini/train_mini.jsonl
```

This creates a 5K stratified sample in ~30 seconds.

**For full training:**

Download your existing `training-data/final/train.jsonl` to Colab (upload to Drive or local).

### 4. Prepare Configuration

Copy the Colab-optimized config:

```bash
cp stack_2_9_training/train_config_colab.yaml stack_2_9_training/train_config.yaml
```

Or edit `train_config.yaml` directly to match the Colab settings.

### 5. Run Training

```bash
cd stack-2.9-training
python -m stack_2_9_training.train_lora --config train_config.yaml
```

**Monitor progress:**

- Watch `nvidia-smi` in a separate cell: `!nvidia-smi --loop=5`
- Training logs show loss per step
- Checkpoints saved every 500 steps to `./adapters/`

**Expected output:**
```
Train loss: 1.234
Step 100/2000 - loss 1.234
...
Training completed. Model saved to ./adapters/
```

### 6. Merge Adapter

After training finishes:

```bash
python -m stack_2_9_training.merge_adapter --base-model Qwen/Qwen2.5-Coder-7B
```

Output: `./model_final/` with full model + tokenizer.

Takes 2-3 minutes.

### 7. Test Inference

Quick test:

```python
from stack_2_9_eval.model_client import create_model_client

# Point to your merged model
client = create_model_client(
    provider="ollama",  # or use direct HF pipeline
    model="./model_final"
)

result = client.generate("Write a Python function to reverse a string")
print(result.text)
```

For production use, serve via vLLM or Hugging Face TGI.

---

## 🚨 Troubleshooting OOM (Out of Memory)

If you get CUDA OOM errors, try these fixes **in order**:

### 1. Reduce sequence length
Edit `train_config_colab.yaml`:
```yaml
training:
  max_seq_length: 4096  # instead of 8192
```

### 2. Reduce batch size further
```yaml
training:
  per_device_train_batch_size: 1  # already 1
  gradient_accumulation_steps: 32  # increase to 32 (slower but less memory)
```

### 3. Disable gradient checkpointing (memory vs speed trade-off)
```yaml
training:
  gradient_checkpointing: false  # uses more memory but faster
```

### 4. Lower LoRA rank
```yaml
peft:
  r: 8  # or even 4
  lora_alpha: 16
```

### 5. Switch to CPU (last resort)
Very slow (days), but works:
```yaml
model:
  load_in_4bit: false  # CPU cannot handle 4-bit quantization well
```

---

## 📊 Expected Performance

On **Colab T4 (free)** with 7B model:

| Metric | Value |
|--------|-------|
| Training time (2 epochs, 5K examples) | ~3-4 hours |
| Training time (2 epochs, 50K examples) | ~12-18 hours |
| VRAM usage | 10-12 GB |
| Disk space needed | 5-10 GB (model + checkpoints) |
| Inference throughput | ~15-25 tokens/sec |

---

## ☁️ Upgrading to A100 (Colab Pro)

If you have **Colab Pro** with A100 (40GB):

1. Change model in config:
   ```yaml
   model:
     name: "Qwen/Qwen2.5-Coder-32B"
   ```

2. Increase context:
   ```yaml
   tokenizer:
     model_max_length: 32768
   ```

3. Increase batch size:
   ```yaml
   training:
     per_device_train_batch_size: 4
     gradient_accumulation_steps: 4
   ```

4. Training time for 50K examples: ~6-8 hours

---

## 📤 Exporting to Hugging Face Hub

After merging, push to HF:

```python
from huggingface_hub import HfApi

api = HfApi(token="your-hf-token")
api.upload_folder(
    folder_path="./model_final",
    repo_id="your-org/stack-2.9-7b-lora",
    repo_type="model"
)
```

Then update `TOGETHER_AI.md` with your model ID.

---

## 🔄 Resuming Interrupted Training

Colab can disconnect unexpectedly. Use checkpointing:

1. Check if checkpoint exists: `ls -la adapters_colab/checkpoint-*`
2. To resume, add to config:
   ```yaml
   training:
     resume_from_checkpoint: "./adapters_colab/checkpoint-XXX"
   ```
   Or pass CLI arg:
   ```bash
   python -m stack_2_9_training.train_lora --config train_config.yaml --resume_from_checkpoint ./adapters_colab/checkpoint-XXX
   ```

---

## 🧪 Quick Validation Before Full Training

Run a mini training to verify setup:

```bash
python scripts/create_mini_dataset.py --size 100  # 100 examples
python -m stack_2_9_training.train_lora --config train_config_colab.yaml --num_train_epochs 1
```

Should take 15-30 minutes and give you a sense of whether training works.

---

## 📁 Files in This Package

- `COLAB_TRAINING.md` - This guide
- `colab_train_stack29.ipynb` - Ready-to-run Colab notebook
- `train_config_colab.yaml` - Optimized config for T4/7B
- `scripts/create_mini_dataset.py` - Create 5K sample dataset
- `stack_2_9_training/` - Training package (prepare_data, train_lora, merge_adapter)

---

## 🆘 Getting Help

- **Colab issues**: Check Google Colab documentation
- **CUDA OOM**: Reduce `max_seq_length` to 4096, increase `gradient_accumulation_steps`
- **Training crashes**: Ensure you have enough disk space (at least 10GB free)
- **Slow training**: Verify `bf16` is enabled (T4 supports it), check `nvidia-smi` for GPU utilization

---

## ✅ Ready to Go!

The Colab notebook is pre-configured and ready to execute. Just open it, select **GPU runtime**, and run all cells.

**Expected outcome:** Trained LoRA adapter in `./adapters_colab/`, merged model in `./model_final/`, ready for evaluation and Hugging Face publication.
