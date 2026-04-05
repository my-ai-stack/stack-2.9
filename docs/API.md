# Stack 2.9 Inference API Documentation

REST API for code generation using the Stack 2.9 fine-tuned Qwen model.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_api.txt
pip install -r requirements.txt  # Core dependencies (transformers, torch, etc.)
```

### 2. Set Model Path

```bash
# Option A: Environment variable
export MODEL_PATH=/path/to/your/merged/model

# Option B: Direct parameter
MODEL_PATH=/path/to/model uvicorn inference_api:app --port 8000
```

### 3. Start the Server

```bash
# Basic usage
uvicorn inference_api:app --host 0.0.0.0 --port 8000

# With auto-reload (development)
uvicorn inference_api:app --reload --port 8000

# Using Python directly
python inference_api.py
```

### 4. Verify It's Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_path": "base_model_qwen7b",
  "device": "cuda",
  "cuda_available": true
}
```

---

## API Endpoints

### `GET /health`

Health check endpoint to verify API and model status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_path": "/path/to/model",
  "device": "cuda",
  "cuda_available": true
}
```

---

### `GET /model-info`

Get information about the currently loaded model.

**Response:**
```json
{
  "model_path": "/path/to/model",
  "device": "cuda:0",
  "dtype": "torch.float16"
}
```

---

### `POST /generate`

Generate code completion for a prompt.

**Request Body:**
```json
{
  "prompt": "def two_sum(nums, target):\n    \"\"\"Return indices of two numbers that add up to target.\"\"\"\n",
  "max_tokens": 128,
  "temperature": 0.2,
  "top_p": 0.95,
  "do_sample": true,
  "repetition_penalty": 1.1,
  "num_return_sequences": 1
}
```

**Parameters:**
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `prompt` | string | required | - | Input prompt to complete |
| `max_tokens` | int | 512 | 1-4096 | Maximum tokens to generate |
| `temperature` | float | 0.2 | 0.0-2.0 | Sampling temperature (higher = more creative) |
| `top_p` | float | 0.95 | 0.0-1.0 | Nucleus sampling threshold |
| `do_sample` | bool | true | - | Whether to use sampling vs greedy |
| `repetition_penalty` | float | 1.1 | 1.0-2.0 | Penalize repeated tokens |
| `num_return_sequences` | int | 1 | 1-10 | Number of sequences to generate |

**Response:**
```json
{
  "generated_text": "    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
  "prompt": "def two_sum(nums, target):\n    \"\"\"Return indices of two numbers that add up to target.\"\"\"\n",
  "model": "base_model_qwen7b",
  "num_tokens": 45,
  "finish_reason": "stop"
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n):\n    \"\"\"Return first n Fibonacci numbers.\"\"\"\n",
    "max_tokens": 100,
    "temperature": 0.2
  }'
```

---

### `POST /chat`

Conversational interface for multi-turn interactions.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Write a function to reverse a string in Python"},
    {"role": "assistant", "content": "def reverse_string(s):\n    return s[::-1]"},
    {"role": "user", "content": "Make it recursive instead"}
  ],
  "max_tokens": 128,
  "temperature": 0.2,
  "top_p": 0.95
}
```

**Message Roles:**
- `user` - User's message
- `assistant` - Model's previous response (for conversation history)

**Response:**
```json
{
  "message": {
    "role": "assistant",
    "content": "def reverse_string(s):\n    if len(s) <= 1:\n        return s\n    return s[-1] + reverse_string(s[:-1])"
  },
  "model": "base_model_qwen7b",
  "num_tokens": 67,
  "finish_reason": "stop"
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a binary search function"}
    ],
    "max_tokens": 150
  }'
```

---

### `POST /generate/raw`

Same as `/generate` but returns raw output without extracting code from markdown blocks.

**Example with curl:**
```bash
curl -X POST http://localhost:8000/generate/raw \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def quick_sort(arr):",
    "max_tokens": 200
  }'
```

---

### `POST /extract-code`

Extract code from a text response that may contain markdown code blocks.

**Request Body:**
```json
{
  "prompt": "```python\ndef hello():\n    print(\"world\")\n```"
}
```

**Response:**
```json
{
  "code": "def hello():\n    print(\"world\")"
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `base_model_qwen7b` | Path to model directory |
| `DEVICE` | `cuda` (if available) | Device to use: `cuda` or `cpu` |
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `RELOAD` | `false` | Enable auto-reload for development |
| `DEFAULT_MAX_TOKENS` | `512` | Default max tokens |
| `DEFAULT_TEMPERATURE` | `0.2` | Default temperature |
| `DEFAULT_TOP_P` | `0.95` | Default top_p |

---

## Usage Examples

### Python Client

```python
import requests

API_URL = "http://localhost:8000"

# Health check
health = requests.get(f"{API_URL}/health").json()
print(f"Model loaded: {health['model_loaded']}")

# Code completion
response = requests.post(
    f"{API_URL}/generate",
    json={
        "prompt": "def merge_sort(arr):\n    \"\"\"Return sorted array.\"\"\"\n",
        "max_tokens": 200,
        "temperature": 0.3,
    }
).json()

print(response["generated_text"])
```

### JavaScript/Node.js Client

```javascript
const API_URL = "http://localhost:8000";

// Code completion
async function generate(prompt) {
  const response = await fetch(`${API_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      max_tokens: 128,
      temperature: 0.2,
    }),
  });
  return response.json();
}

const result = await generate("def binary_search(arr, target):");
console.log(result.generated_text);
```

### Using with OpenAI SDK (with base_url replacement)

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000"
)

# Note: This works for basic completions but may need adapter code
# for full OpenAI compatibility
response = client.completions.create(
    model="stack-2.9",
    prompt="def factorial(n):",
    max_tokens=100,
)
```

---

## Performance Tips

1. **GPU Recommended**: For fastest inference, run on GPU with CUDA
2. **Batch Processing**: For multiple prompts, process sequentially (model is loaded once)
3. **Memory**: Ensure adequate GPU memory; reduce `max_tokens` if needed
4. **Temperature**: Use lower temperature (0.1-0.3) for deterministic code, higher for creative tasks

---

## Error Handling

**503 Service Unavailable**: Model not loaded or loading failed
```json
{"detail": "Model not loaded. Check /health for status."}
```

**500 Internal Server Error**: Generation failed
```json
{"detail": "Generation failed: <error message>"}
```

**400 Bad Request**: Invalid input
```json
{"detail": "Last message must be from user"}
```

---

## Architecture Notes

- **Single Model Instance**: Model is loaded once at startup and reused
- **Synchronous Generation**: Uses `torch.no_grad()` for inference
- **CORS Enabled**: Accepts requests from any origin (configure for production)
- **No Authentication**: Add middleware (e.g., API key) for production deployments
