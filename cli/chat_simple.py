"""
Stack 2.9 - Simple Local Chat
Run the fine-tuned model locally on your machine
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = "/Users/walidsobhi/stack-2-9-final-model"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("Model loaded!\n")

def chat(prompt):
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response[len(text):].strip()

# Interactive loop
while True:
    prompt = input("You: ")
    if prompt.lower() in ['quit', 'exit']:
        break
    print("Thinking...")
    print(f"Bot: {chat(prompt)}\n")
