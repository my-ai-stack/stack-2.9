# Using Stack 2.9 with Together AI

This guide explains how to use Stack 2.9 with Together AI as the model provider.

## Overview

Together AI provides powerful cloud-hosted models with high performance and competitive pricing. Stack 2.9 supports Together AI through its OpenAI-compatible API, allowing you to use models like:

- `togethercomputer/meta-llama-3-70b-instruct`
- `togethercomputer/CodeLlama-34b-instruct`
- `togethercomputer/Qwen2.5-Coder-32B-Instruct` (recommended for Stack 2.9)
- And many others from Together's model library

## Prerequisites

1. **Together AI Account**: Sign up at [together.ai](https://together.ai)
2. **API Key**: Obtain your API key from the Together dashboard
3. **OpenAI Python Package**: Install `openai>=1.0.0` (required for Together client)

```bash
pip install openai
```

## Environment Variables

Configure your environment with the following variables:

```bash
# Required: Together AI API key
export TOGETHER_API_KEY="your-together-api-key-here"

# Optional: Model selection (default: togethercomputer/Qwen2.5-Coder-32B-Instruct)
export TOGETHER_MODEL="togethercomputer/Qwen2.5-Coder-32B-Instruct"

# Optional: Provider configuration (for auto-detection)
export MODEL_PROVIDER="together"
```

### Setting up in Shell

Add these lines to your `~/.zshrc`, `~/.bashrc`, or shell profile:

```bash
# Together AI configuration
export TOGETHER_API_KEY="tog-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TOGETHER_MODEL="togethercomputer/Qwen2.5-Coder-32B-Instruct"
```

Then reload your shell:

```bash
source ~/.zshrc  # or ~/.bashrc
```

### Using .env file (recommended for development)

Create a `.env` file in your project root:

```env
TOGETHER_API_KEY=tog-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TOGETHER_MODEL=togethercomputer/Qwen2.5-Coder-32B-Instruct
MODEL_PROVIDER=together
```

Then load it with `python-dotenv`:

```bash
pip install python-dotenv
```

And in your Python script:

```python
from dotenv import load_dotenv
load_dotenv()  # loads .env file
```

## Usage Examples

### Command Line

Use the built-in CLI with Together provider:

```bash
# Using default model (Meta-Llama-3-70B)
python stack.py --provider together "Write a Python function to reverse a string"

# Using a specific model (override env var)
TOGETHER_MODEL=togethercomputer/Qwen2.5-Coder-32B-Instruct python stack.py --provider together "def factorial(n):"
```

### Python API

```python
from stack_2_9_eval.model_client import create_model_client

# Create Together client (reads TOGETHER_API_KEY from env)
client = create_model_client(provider="together")

# Or specify explicitly
client = create_model_client(
    provider="together",
    model="togethercomputer/Qwen2.5-Coder-32B-Instruct",
    api_key="your-api-key"
)

# Generate code
result = client.generate(
    prompt="Write a Python function to sort a list using quicksort",
    temperature=0.2,
    max_tokens=1024
)

print(result.text)
```

### Chat Mode

```python
from stack_2_9_eval.model_client import create_model_client, ChatMessage

client = create_model_client(provider="together")

messages = [
    ChatMessage(role="system", content="You are an expert Python programmer."),
    ChatMessage(role="user", content="How do I read a JSON file in Python?"),
]

result = client.chat(messages, temperature=0.2, max_tokens=512)
print(result.text)
```

### Using with Tool Calls

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "FileReadTool",
            "description": "Read file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    }
]

messages = [
    ChatMessage(role="user", content="Read the file 'config.yaml' and tell me what's in it")
]

result = client.chat(messages, temperature=0.2, tools=tools)
print(result.text)
# Check result.raw_response for tool_calls if model requested a tool
```

## Recommended Models

For Stack 2.9 use cases (coding + tool use), these Together models are recommended:

### Primary Recommendation

**`togethercomputer/qwen2.5-coder-32b-instruct`**
- Matches Stack 2.9's base model (Qwen2.5-Coder-32B)
- Excellent code generation
- Strong tool-calling capabilities
- Cost-effective: ~$0.22 / 1M tokens (input)
- Use this for production Stack 2.9 deployments

### Alternatives

**`togethercomputer/meta-llama-3-70b-instruct`**
- Larger model (70B) with strong reasoning
- Slightly higher cost but excellent quality
- Good for complex problem-solving

**`togethercomputer/codellama-34b-instruct`**
- Code-specialized Llama 34B
- Good performance, lower cost than 70B models

**`togethercomputer/qwen2.5-72b-instruct`**
- 72B variant of Qwen2.5 (if you need maximum quality)
- Higher cost and latency

### Model Selection Tips

- **Match training distribution**: Use Qwen models for Stack 2.9 pattern compatibility
- **Budget**: 34B models offer best price/performance for coding tasks
- **Latency**: Smaller models (7B-13B) are faster but less capable
- **Throughput**: Consider batching for large-scale usage

## Cost Estimation

Together AI pricing (as of 2025, check their site for current rates):

| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|---------------------|----------------------|
| Qwen2.5-Coder-32B | ~0.22 | ~0.22 |
| Meta-Llama-3-70B | ~0.70 | ~0.70 |
| CodeLlama-34B | ~0.22 | ~0.22 |
| Qwen2.5-72B | ~0.70 | ~0.70 |

### Example Cost Calculation

If your typical usage:
- 100 queries/day
- Average 2,000 tokens per query (input + output)
- Using Qwen2.5-Coder-32B

Daily cost: `(100 * 2000 / 1,000,000) * $0.22 ≈ $0.044`
Monthly cost: ~$1.32

**Very affordable for development and light production use.**

## Performance Considerations

- **Latency**: Expect 100-500ms per request depending on model size and complexity
- **Rate Limits**: Together provides generous rate limits (check your plan)
- **Throughput**: Use concurrent requests for batch processing (respect rate limits)
- **Streaming**: Together supports streaming; use `stream=True` in client for long generations

## Error Handling

Implement robust error handling for production:

```python
from stack_2_9_eval.model_client import create_model_client
import time

def generate_with_retry(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = client.generate(prompt, temperature=0.2, max_tokens=1024)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # exponential backoff
            print(f"Error: {e}. Retrying in {wait}s...")
            time.sleep(wait)

client = create_model_client(provider="together", api_key=os.getenv("TOGETHER_API_KEY"))
result = generate_with_retry(client, "Write a function to calculate prime numbers")
```

## Comparison with Other Providers

| Feature | Together AI | Ollama (local) | OpenAI | Anthropic |
|---------|-------------|----------------|--------|-----------|
| Cost (32B class) | Low (~$0.22/M) | Free (your hardware) | High (~$3/M) | High (~$3/M) |
| Qwen2.5-Coder | ✅ Supported | ✅ Via pull | ❌ No | ❌ No |
| Privacy | Cloud (check TOS) | Full local | Cloud | Cloud |
| Latency | Medium | Fast (local) | Medium | Medium |
| Setup Complexity | Low (API key) | Medium (install) | Low | Low |
| Rate Limits | Generous | Unlimited | Pay-as-you-go | Pay-as-you-go |
| Tool Calling | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

**Best for Stack 2.9**: Together AI when you need cloud access and Qwen models without running locally.

## Troubleshooting

### API Key Errors

```
ValueError: Together AI API key required.
```

**Solution**: Set `TOGETHER_API_KEY` environment variable or pass `api_key` param.

### Model Not Found

```
openai.BadRequestError: The model '...' does not exist
```

**Solution**: Check model name spelling. Browse available models at [Together Models](https://together.ai/models). Use full model ID like `togethercomputer/qwen2.5-coder-32b-instruct`.

### Rate Limit Exceeded

**Solution**: Add retry logic with exponential backoff. Consider upgrading your Together plan.

### Import Errors

```
ImportError: openai package required
```

**Solution**: `pip install openai` (version 1.0+)

## Advanced Configuration

### Custom Base URL

If you need to use a custom endpoint (e.g., for regional deployments):

```python
client = create_model_client(
    provider="together",
    model="togethercomputer/qwen2.5-coder-32b-instruct",
    base_url="https://your-custom-endpoint.together.ai/v1"
)
```

### Timeouts and Retries

```python
client = TogetherClient(
    model="togethercomputer/qwen2.5-coder-32b-instruct",
    api_key=os.getenv("TOGETHER_API_KEY"),
    timeout=300  # 5 minute timeout
)
```

### Streaming Responses

For long generations, use streaming (requires modifying client or using OpenAI library directly):

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("TOGETHER_API_KEY"), base_url="https://api.together.xyz/v1")

stream = client.chat.completions.create(
    model="togethercomputer/qwen2.5-coder-32b-instruct",
    messages=[{"role": "user", "content": "Write a detailed explanation of binary search"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Integration with Stack 2.9 CLI

To make Together AI the default provider:

```bash
# Set environment variables permanently
echo 'export MODEL_PROVIDER="together"' >> ~/.zshrc
echo 'export TOGETHER_MODEL="togethercomputer/qwen2.5-coder-32b-instruct"' >> ~/.zshrc
source ~/.zshrc
```

Now `stack.py` will automatically use Together AI without `--provider` flag.

## Security Best Practices

1. **Never commit API keys** to version control. Use `.env` files or environment variables.
2. **Rotate keys** periodically from Together dashboard.
3. **Use minimal permissions** - Together API keys have full access; protect them.
4. **Enable billing alerts** to avoid unexpected charges.
5. **Review Together's TOS** for data usage and privacy policies.

## Support

- **Together Documentation**: https://docs.together.io/
- **Stack 2.9 Issues**: https://github.com/my-ai-stack/stack-2.9/issues
- **Model Cards**: See `MODEL_CARD.md` for Stack 2.9 details

---

**Last Updated**: 2025-04-02  
**Compatible Stack 2.9 Version**: 2.9.0+
