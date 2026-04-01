# Stack 2.9 API Documentation

## Overview

Stack 2.9 provides OpenAI-compatible API endpoints for seamless integration with existing tools and workflows.

## Base URL

```
https://api.stack2.9.openclaw.org/v1
```

## Authentication

### API Key

Include your API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "qwen/qwen2.5-coder-32b", "messages": [{"role": "user", "content": "Write a Python function to calculate Fibonacci numbers"}]}' \
     https://api.stack2.9.openclaw.org/v1/chat/completions
```

### Rate Limits

- **Free Tier**: 100 requests/minute
- **Pro Tier**: 1,000 requests/minute
- **Enterprise**: Custom limits

## Endpoints

### Chat Completions

**Endpoint**: `POST /chat/completions`

**Description**: Generate chat completions with streaming support.

**Request Body**:

```json
{
  "model": "qwen/qwen2.5-coder-32b",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful coding assistant."
    },
    {
      "role": "user",
      "content": "Write a function to sort an array of numbers."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": true,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "execute_code",
        "description": "Execute code in a sandboxed environment",
        "parameters": {
          "type": "object",
          "properties": {
            "code": {"type": "string"},
            "language": {"type": "string"}
          },
          "required": ["code", "language"]
        }
      }
    }
  ],
  "tool_calls": 5
}
```

**Response (Streaming)**:

```json
{
  "id": "chatcmpl-123456789",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen/qwen2.5-coder-32b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "def sort_array(arr):\n    return sorted(arr)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 25,
    "total_tokens": 75
  }
}
```

### Streaming Example

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "qwen/qwen2.5-coder-32b", "messages": [{"role": "user", "content": "Write a hello world function"}], "stream": true}' \
     https://api.stack2.9.openclaw.org/v1/chat/completions | \
     while read -r chunk; do
         echo "$chunk" | jq -r '.choices[0].delta.content // .choices[0].content'
     done
```

### Tool Calling

Stack 2.9 supports OpenAI-compatible tool calling:

```json
{
  "name": "tool_calls",
  "arguments": "{\"name\":\"execute_code\",\"arguments\":{\"code\":\"print(\"Hello, World!\")\",\"language\":\"python\"}}",
  "input_token_count": 10,
  "output_token_count": 5
}
```

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `auth_error` | Invalid API key | 401 |
| `rate_limit` | Too many requests | 429 |
| `model_not_found` | Model not available | 404 |
| `invalid_request` | Malformed request | 400 |
| `tool_error` | Tool execution failed | 422 |
| `internal_error` | Server error | 500 |

### Error Response Format

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "auth_error",
    "param": "authorization",
    "code": 401
  }
}
```

## Rate Limits

### Free Tier
- **Requests**: 100/minute
- **Tokens**: 100,000/day
- **Concurrent Requests**: 5

### Pro Tier
- **Requests**: 1,000/minute
- **Tokens**: 10M/month
- **Concurrent Requests**: 20

### Enterprise
- **Custom**: Contact sales

## Models

### Available Models

| Model | Description | Context Length |
|-------|-------------|----------------|
| `qwen/qwen2.5-coder-32b` | Main coding model | 131072 |
| `qwen/qwen2.5-coder-14b` | Lightweight version | 16384 |

### Model Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | required | Model name |
| `temperature` | number | 0.7 | Sampling temperature |
| `max_tokens` | integer | 1000 | Max tokens to generate |
| `top_p` | number | 1.0 | Nucleus sampling |
| `frequency_penalty` | number | 0.0 | Frequency penalty |
| `presence_penalty` | number | 0.0 | Presence penalty |

## Webhooks

### Tool Call Webhook

```json
{
  "type": "tool_calls",
  "tool_calls": [
    {
      "id": "call_123",
      "name": "execute_code",
      "input_token_count": 10,
      "arguments": "{\"code\":\"print(\"Hello\")\",\"language\":\"python\"}"
    }
  ]
}
```

## SDKs

### Python SDK

```python
from stack29 import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="qwen/qwen2.5-coder-32b",
    messages=[{"role": "user", "content": "Write a function"}],
    stream=True
)
```

### Node.js SDK

```javascript
const { OpenAI } = require('openai');

const openai = new OpenAI({
  apiKey: 'your-api-key',
});

const response = await openai.chat.completions.create({
  model: 'qwen/qwen2.5-coder-32b',
  messages: [{ role: 'user', content: 'Write a function' }],
  stream: true,
});
```

## Best Practices

### 1. Use Streaming

For better user experience, always use streaming for long responses.

### 2. Handle Errors Gracefully

Implement proper error handling for rate limits and authentication errors.

### 3. Monitor Usage

Keep track of token usage to stay within limits.

### 4. Cache Responses

Cache frequent responses to reduce API calls.

### 5. Use Appropriate Temperature

Lower temperature for deterministic code, higher for creative tasks.

## Support

- **Documentation**: [Stack 2.9 API Docs](https://api.stack2.9.openclaw.org/docs)
- **Issues**: [GitHub Issues](https://github.com/openclaw/stack-2.9/issues)
- **Email**: api@stack2.9.openclaw.org

---

**API Version**: 1.0
**Last Updated**: 2026-04-01
**Status**: Active