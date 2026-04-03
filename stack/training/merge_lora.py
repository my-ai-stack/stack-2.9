import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

# Load base model and LoRA weights
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-32B",
    torch_dtype=torch.float16,
    load_in_4bit=True,
    device_map="auto"
)

# Load LoRA adapter
lora_adapter = PeftModel.from_pretrained(
    base_model,
    "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-lora/adapter_model.bin"
)

# Merge LoRA weights into base model
merged_model = lora_adapter.merge_and_unload()

# Save merged model
output_dir = "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-merged"
os.makedirs(output_dir, exist_ok=True)

merged_model.save_pretrained(output_dir)

print(f"Successfully merged LoRA weights into base model")
print(f"Merged model saved to: {output_dir}")
print(f"Model has {merged_model.num_parameters()} parameters")