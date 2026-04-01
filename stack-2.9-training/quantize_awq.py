import torch
from transformers import AutoModelForCausalLM
from awq import AWQ4BitConfig, prepare_model
import os

# Load merged model
merged_model = AutoModelForCausalLM.from_pretrained(
    "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-merged",
    torch_dtype=torch.float16,
    load_in_4bit=True,
    device_map="auto"
)

# Setup AWQ quantization
awq_config = AWQ4BitConfig(
    num_groups=32,
    min_coeff=0.01,
    max_coeff=1.0,
    bnb_config={
        "bnb_4bit": True,
        "bnb_use_double_quant": True,
        "bnb_use_mixed_qembedding": True
    }
)

# Apply AWQ quantization
quantized_model = prepare_model(merged_model, awq_config)

# Save quantized model
output_dir = "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/output/stack-2.9-awq"
os.makedirs(output_dir, exist_ok=True)

quantized_model.save_pretrained(output_dir)

print(f"Successfully applied AWQ quantization")
print(f"Quantized model saved to: {output_dir}")
print(f"Quantized model has {quantized_model.num_parameters()} parameters")