import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SYSTEM_PROMPT = """You are Stack 2.9, an expert AI coding assistant.
- Answer questions naturally and helpfully
- When the user asks for code, write clean complete code
- When the user asks a question, answer in plain language
- Be concise and practical"""

print("Loading your fine-tuned Stack 2.9 model...")
model = AutoModelForCausalLM.from_pretrained(
    '/Users/walidsobhi/stack-2-9-final-model',
    torch_dtype=torch.float16,
    device_map='auto'
)
tokenizer = AutoTokenizer.from_pretrained('/Users/walidsobhi/stack-2-9-final-model')
print("✅ Ready!\n")

# Generation settings
MAX_TOKENS = 200
TEMPERATURE = 0.4
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

        # Prepend system prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"
        inputs = tokenizer(full_prompt, return_tensors='pt').to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            repetition_penalty=REP_PENALTY,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

        # Decode full response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the assistant's response (after "Assistant:")
        if "Assistant:" in full_response:
            response = full_response.split("Assistant:")[-1].strip()
        else:
            response = full_response[len(full_prompt):].strip()

        # Stop at common stop points
        for stop in ['\n\n\n', 'User:', 'You:']:
            if stop in response:
                response = response.split(stop)[0].strip()

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        print("\nExiting...")
        break

print("Goodbye!")
