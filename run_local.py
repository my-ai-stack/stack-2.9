"""
Stack 2.9 - Local Inference Script
Run the fine-tuned model locally on your machine
"""
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Model path
MODEL_PATH = "/Users/walidsobhi/stack-2-9-final-model"

# Or use HuggingFace Hub
# MODEL_PATH = "Qwen/Qwen2.5-Coder-1.5B"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("Model loaded!\n")

def generate(prompt, max_tokens=512, temperature=0.7):
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)[len(text):].strip()
    return response

# Test
prompt = "Write a Python function to calculate fibonacci numbers"
print(f"Prompt: {prompt}\n")
print("Response:", generate(prompt))
