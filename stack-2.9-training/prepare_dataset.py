import json
import os
from pathlib import Path
from datasets import Dataset
from transformers import AutoTokenizer
import pandas as pd

# Load the synthetic examples
examples_file = Path("/Users/walidsobhi/.openclaw/workspace/training-data/synthetic/examples.jsonl")

if not examples_file.exists():
    raise FileNotFoundError(f"Training data file not found: {examples_file}")

# Load JSONL data
with open(examples_file, 'r') as f:
    data = [json.loads(line) for line in f]

# Convert to DataFrame
if not data:
    raise ValueError("No data found in the examples file")

df = pd.DataFrame(data)

# Apply chat template
if 'instruction' in df.columns and 'response' in df.columns:
    df['prompt'] = df.apply(lambda row: f"### Instruction:\n{row['instruction']}\n\n### Response:\n{row['response']}", axis=1)
elif 'prompt' in df.columns and 'completion' in df.columns:
    df['prompt'] = df.apply(lambda row: f"### Prompt:\n{row['prompt']}\n\n### Completion:\n{row['completion']}", axis=1)
else:
    raise ValueError("Data format not recognized. Expected 'instruction' and 'response' or 'prompt' and 'completion' columns")

# Create dataset
dataset = Dataset.from_pandas(df[['prompt']])

dataset = dataset.map(
    lambda x: AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B").batch_encode_plus(
        x["prompt"],
        padding="max_length",
        truncation=True,
        max_length=32768,
        return_tensors="np"
    ),
    batched=True,
    remove_columns=["prompt"]
)

dataset = dataset.rename_column("input_ids", "input_ids")
dataset = dataset.rename_column("attention_mask", "attention_mask")

# Split into train and eval (90/10)
train_dataset, eval_dataset = dataset.train_test_split(test_size=0.1)

# Save datasets
output_dir = Path("/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/data")
train_dataset.save_to_disk(str(output_dir / "train"))
eval_dataset.save_to_disk(str(output_dir / "eval"))

print(f"Successfully created datasets:")
print(f"- Train: {output_dir / \"train\"}")
print(f"- Eval: {output_dir / \"eval\"}")
print(f"Total examples: {len(dataset)}")
print(f"Train examples: {len(train_dataset)}")
print(f"Eval examples: {len(eval_dataset)}")