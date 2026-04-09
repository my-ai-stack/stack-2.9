"""
Stack 2.9 - Local Inference Script
Run the fine-tuned model locally on your machine
"""
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Model path (your fine-tuned model)
MODEL_PATH = "/Users/walidsobhi/stack-2-9-final-model"

# Or use HuggingFace Hub version (if you want to test base model)
# MODEL_PATH = "Qwen/Qwen2.5-Coder-1.5B"

def load_model():
    """Load model and tokenizer"""
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,  # Half precision - faster
        device_map="auto",          # Auto-detect device (GPU/CPU)
        trust_remote_code=True
    )
    print("Model loaded!")
    return model, tokenizer

def generate(prompt, system_prompt="You are a helpful coding assistant.", max_tokens=512, temperature=0.7):
    """Generate response from the model"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # Apply chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenize
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # Generate
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )

    # Decode - remove input prompt from response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response[len(text):].strip()

def chat():
    """Interactive chat loop"""
    print("\n" + "="*50)
    print("Stack 2.9 - Local Chat")
    print("="*50)
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        response = generate(user_input)
        print(f"\nAssistant: {response}\n")

# Load model once
model, tokenizer = load_model()

# Run chat
if __name__ == "__main__":
    chat()
