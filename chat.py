import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading your fine-tuned Stack 2.9 model...")
model = AutoModelForCausalLM.from_pretrained(
    '/Users/walidsobhi/stack-2-9-final-model',
    torch_dtype=torch.float16,
    device_map='auto'
)
tokenizer = AutoTokenizer.from_pretrained('/Users/walidsobhi/stack-2-9-final-model')
print("✅ Ready!\n")

# Generation settings
MAX_TOKENS = 150
TEMPERATURE = 0.3
TOP_P = 0.9
REP_PENALTY = 1.2

print(f"Settings: max_tokens={MAX_TOKENS}, temperature={TEMPERATURE}, top_p={TOP_P}\n")

# Interactive loop
while True:
    try:
        prompt = input("You: ")
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        if not prompt.strip():
            continue

        inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            repetition_penalty=REP_PENALTY,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

        # Extract only the new tokens (skip the prompt)
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = full_response[len(prompt):].strip()

        # Stop at common stop points
        for stop in ['\n\n\n', 'You:', 'AI:', 'User:', 'Assistant:']:
            if stop in response:
                response = response.split(stop)[0].strip()

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        print("\nExiting...")
        break

print("Goodbye!")
