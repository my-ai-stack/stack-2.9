import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer

SYSTEM_PROMPT = """You are Stack 2.9, an expert AI coding assistant.
- Answer questions naturally and helpfully
- When the user asks for code, write clean complete code
- When the user asks a question, answer in plain language
- Be concise and practical
- If asked to search the internet, use the search: command"""

MODEL_NAME = "/Users/walidsobhi/stack-2-9-final-model"

print(f"Loading {MODEL_NAME} from HuggingFace...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
print("✅ Ready!\n")

# Generation settings
MAX_TOKENS = 200
TEMPERATURE = 0.4
TOP_P = 0.9
REP_PENALTY = 1.2

print(f"Settings: max_tokens={MAX_TOKENS}, temperature={TEMPERATURE}, top_p={TOP_P}")
print("Commands: search:<query> - search the web, quit/exit - stop\n")

def web_search(query, count=5):
    """Search the web using DuckDuckGo JSON API"""
    try:
        url = f"https://duckduckgo.com/?q={query}&format=json&no_redirect=1"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Stack29Bot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "results": [{"query": query, "source": "duckduckgo"}]}
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Interactive loop
while True:
    try:
        prompt = input("You: ")
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        if not prompt.strip():
            continue

        # Handle search command
        if prompt.lower().startswith("search:"):
            query = prompt[7:].strip()
            print("🔍 Searching...")
            result = web_search(query)
            if result["success"]:
                print(f"✅ Found results for: {query}")
                print(f"   (Web search results would appear here)")
            else:
                print(f"❌ Search failed: {result['error']}")
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
