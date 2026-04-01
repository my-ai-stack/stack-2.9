# Stack 2.9 API Documentation

Complete API reference for integrating Stack 2.9 into your applications.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limits](#rate-limits)
- [REST Endpoints](#rest-endpoints)
- [WebSocket Streaming](#websocket-streaming)
- [Request/Response Formats](#requestresponse-formats)
- [Error Handling](#error-handling)
- [SDKs and Examples](#sdks-and-examples)

---

## Overview

Stack 2.9 provides an OpenAI-compatible API for seamless integration with existing tools and workflows.

### Base URL

```
Production: https://api.stack2.9.openclaw.org/v1
Local:      http://localhost:3000/v1
```

### API Versioning

The current API version is `v1`. Version information is included in all responses.

```json
{
  "api_version": "1.0",
  "deprecation_date": null
}
```

---

## Authentication

### API Key Authentication

Include your API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.stack2.9.openclaw.org/v1/chat/completions
```

### Obtaining an API Key

1. **Self-hosted:** Set `API_KEY` environment variable
2. **Cloud:** Sign up at [stack2.9.openclaw.org](https://stack2.9.openclaw.org)

### Authentication Errors

| Status | Error Type | Description |
|--------|------------|-------------|
| 401 | `invalid_api_key` | API key is missing or invalid |
| 403 | `account_disabled` | Account has been disabled |
| 429 | `rate_limit_exceeded` | Too many requests |

---

## Rate Limits

### Tier Limits

| Tier | Requests/min | Tokens/day | Concurrent | WebSocket |
|------|-------------|------------|------------|-----------|
| **Free** | 100 | 100,000 | 5 | ✅ |
| **Pro** | 1,000 | 10,000,000 | 20 | ✅ |
| **Enterprise** | Custom | Custom | Custom | ✅ |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Used: 5
```

### Handling Rate Limits

```python
import time
import openai

client = openai.OpenAI(api_key="your-api-key")

for i in range(100):
    try:
        response = client.chat.completions.create(
            model="qwen/qwen2.5-coder-32b",
            messages=[{"role": "user", "content": "Hello"}]
        )
    except openai.RateLimitError:
        time.sleep(60)  # Wait 1 minute
        continue
```

---

## REST Endpoints

### Chat Completions

**Endpoint:** `POST /chat/completions`

Generate chat completions with optional streaming.

#### Request Body

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
      "content": "Write a Python function to calculate Fibonacci numbers."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stream": false,
  "stop": null,
  "tools": [],
  "tool_choice": "auto",
  "user": "user-identifier"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | ✅ | - | Model identifier |
| `messages` | array | ✅ | - | Conversation messages |
| `temperature` | number | ❌ | 0.7 | Sampling temperature (0-2) |
| `max_tokens` | integer | ❌ | 1000 | Maximum tokens to generate |
| `top_p` | number | ❌ | 1.0 | Nucleus sampling |
| `frequency_penalty` | number | ❌ | 0.0 | Frequency penalty (-2 to 2) |
| `presence_penalty` | number | ❌ | 0.0 | Presence penalty (-2 to 2) |
| `stream` | boolean | ❌ | false | Enable streaming |
| `stop` | string/array | ❌ | null | Stop sequences |
| `tools` | array | ❌ | [] | Available tools |
| `tool_choice` | string | ❌ | "auto" | Tool selection strategy |
| `user` | string | ❌ | - | User identifier |

#### Response (Non-Streaming)

```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen/qwen2.5-coder-32b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 35,
    "total_tokens": 60
  },
  "system_fingerprint": "fp_1234567890"
}
```

#### Streaming Response Format

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen2.5-coder-32b", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

```json
{"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"qwen/qwen2.5-coder-32b","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}
{"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"qwen/qwen2.5-coder-32b","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}
{"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"qwen/qwen2.5-coder-32b","choices":[{"index":0,"delta":{"content":" How"},"finish_reason":null}]}
{"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"qwen/qwen2.5-coder-32b","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
```

---

### Models List

**Endpoint:** `GET /models`

List available models.

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen/qwen2.5-coder-32b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openclaw",
      "permission": [],
      "root": "qwen/qwen2.5-coder-32b",
      "parent": null,
      "context_window": 131072,
      "Capabilities": {
        "streaming": true,
        "tools": true,
        "voice": true
      }
    },
    {
      "id": "qwen/qwen2.5-coder-14b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openclaw",
      "permission": [],
      "root": "qwen/qwen2.5-coder-14b",
      "parent": null,
      "context_window": 16384,
      "capabilities": {
        "streaming": true,
        "tools": true,
        "voice": false
      }
    }
  ]
}
```

### Get Model

**Endpoint:** `GET /models/{model_id}`

Get details about a specific model.

```bash
curl http://localhost:3000/v1/models/qwen/qwen2.5-coder-32b
```

```json
{
  "id": "qwen/qwen2.5-coder-32b",
  "object": "model",
  "created": 1234567890,
  "owned_by": "openclaw",
  "context_window": 131072,
  "capabilities": {
    "streaming": true,
    "tools": true,
    "voice": true
  }
}
```

---

## WebSocket Streaming

### Connection

```javascript
const ws = new WebSocket('wss://api.stack2.9.openclaw.org/v1/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'start',
    model: 'qwen/qwen2.5-coder-32b',
    messages: [{role: 'user', content: 'Hello'}],
    temperature: 0.7
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);  // Streamed content
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

### WebSocket Message Types

#### Client → Server

| Type | Description |
|------|-------------|
| `start` | Start a new chat session |
| `stop` | Stop current generation |
| `ping` | Keep-alive ping |

#### Server → Client

| Type | Description |
|------|-------------|
| `content` | Streamed content chunk |
| `tool_call` | Tool invocation request |
| `tool_result` | Tool execution result |
| `done` | Generation complete |
| `error` | Error occurred |
| `pong` | Keep-alive response |

### Full WebSocket Example

```javascript
class Stack29WebSocket {
  constructor(apiKey, model = 'qwen/qwen2.5-coder-32b') {
    this.apiKey = apiKey;
    this.model = model;
    this.ws = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('wss://api.stack2.9.openclaw.org/v1/ws/chat');
      
      this.ws.onopen = () => resolve();
      this.ws.onerror = (e) => reject(e);
    });
  }

  async sendMessage(messages, onChunk, onComplete) {
    await this.connect();
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'content') {
        onChunk(data.content);
      } else if (data.type === 'done') {
        onComplete(data);
        this.ws.close();
      } else if (data.type === 'error') {
        console.error('Error:', data.message);
      }
    };

    this.ws.send(JSON.stringify({
      type: 'start',
      model: this.model,
      messages: messages,
      temperature: 0.7
    }));
  }
}

// Usage
const client = new Stack29WebSocket('your-api-key');
client.sendMessage(
  [{role: 'user', content: 'Write a hello world function'}],
  (chunk) => process.stdout.write(chunk),
  (final) => console.log('\n\nDone!')
);
```

---

## Request/Response Formats

### Message Format

```json
{
  "role": "user|assistant|system",
  "content": "Message content",
  "name": "optional-name",
  "tool_calls": [],
  "tool_call_id": "optional-id"
}
```

### Tool Call Format

```json
{
  "type": "function",
  "id": "call_abc123",
  "function": {
    "name": "execute_code",
    "description": "Execute code in a sandboxed environment",
    "parameters": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "The code to execute"
        },
        "language": {
          "type": "string",
          "description": "Programming language"
        }
      },
      "required": ["code", "language"]
    }
  }
}
```

### Tool Call Response Format

```json
{
  "tool_call_id": "call_abc123",
  "output": "Hello, World!",
  "error": null,
  "execution_time_ms": 150
}
```

### Vision Support (Image Input)

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What does this code do?"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "https://example.com/screenshot.png",
        "detail": "low"
      }
    }
  ]
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "invalid_request_error",
    "param": "authorization",
    "code": 401
  }
}
```

### Error Codes

| Code | Type | HTTP Status | Description |
|------|------|-------------|-------------|
| `invalid_api_key` | Authentication | 401 | API key is invalid |
| `account_disabled` | Authentication | 403 | Account disabled |
| `rate_limit_exceeded` | Rate Limit | 429 | Too many requests |
| `context_length_exceeded` | Invalid Request | 400 | Context too long |
| `invalid_request` | Invalid Request | 400 | Malformed request |
| `model_not_found` | Invalid Request | 404 | Model doesn't exist |
| `tool_error` | Tool Error | 422 | Tool execution failed |
| `internal_error` | Server Error | 500 | Server-side error |
| `service_unavailable` | Server Error | 503 | Service temporarily down |

### Handling Errors in Code

```python
import openai
from openai import APIError, RateLimitError

client = openai.OpenAI(api_key="your-api-key")

try:
    response = client.chat.completions.create(
        model="qwen/qwen2.5-coder-32b",
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError:
    print("Rate limit exceeded. Please wait.")
    # Implement backoff logic
except APIError as e:
    print(f"API error: {e}")
    # Handle error appropriately
```

```javascript
try {
  const response = await client.chat.completions.create({
    model: 'qwen/qwen2.5-coder-32b',
    messages: [{role: 'user', content: 'Hello'}]
  });
} catch (error) {
  if (error.status === 429) {
    console.log('Rate limit exceeded');
  } else if (error.status === 401) {
    console.log('Invalid API key');
  } else {
    console.error('API error:', error.message);
  }
}
```

---

## SDKs and Examples

### Python SDK

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.stack2.9.openclaw.org/v1"
)

# Non-streaming
response = client.chat.completions.create(
    model="qwen/qwen2.5-coder-32b",
    messages=[
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "Write a Python class for a stack data structure."}
    ],
    temperature=0.7,
    max_tokens=1000
)

print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="qwen/qwen2.5-coder-32b",
    messages=[{"role": "user", "content": "Explain recursion"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### JavaScript/Node.js SDK

```bash
npm install openai
```

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'your-api-key',
  baseURL: 'https://api.stack2.9.openclaw.org/v1'
});

// Non-streaming
const response = await client.chat.completions.create({
  model: 'qwen/qwen2.5-coder-32b',
  messages: [
    {role: 'system', content: 'You are a coding assistant.'},
    {role: 'user', content: 'Write a Python class for a stack data structure.'}
  ],
  temperature: 0.7,
  max_tokens: 1000
});

console.log(response.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: 'qwen/qwen2.5-coder-32b',
  messages: [{role: 'user', content: 'Explain recursion'}],
  stream: true
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0].delta.content || '');
}
```

### cURL Examples

```bash
# Basic chat completion
curl -X POST https://api.stack2.9.openclaw.org/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen2.5-coder-32b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Streaming completion
curl -X POST https://api.stack2.9.openclaw.org/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen2.5-coder-32b", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'

# With system prompt
curl -X POST https://api.stack2.9.openclaw.org/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen2.5-coder-32b",
    "messages": [
      {"role": "system", "content": "You are an expert Python programmer."},
      {"role": "user", "content": "Write a decorator that caches function results."}
    ]
  }'

# With tools
curl -X POST https://api.stack2.9.openclaw.org/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen2.5-coder-32b",
    "messages": [{"role": "user", "content": "Create a file called hello.py"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "write_file",
          "description": "Write content to a file",
          "parameters": {
            "type": "object",
            "properties": {
              "path": {"type": "string"},
              "content": {"type": "string"}
            }
          }
        }
      }
    ]
  }'
```

### OpenAI-Compatible Client Usage

Stack 2.9 is compatible with the OpenAI client library:

```python
# Works with LangChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

chat = ChatOpenAI(
    model="qwen/qwen2.5-coder-32b",
    openai_api_base="https://api.stack2.9.openclaw.org/v1",
    openai_api_key="your-api-key"
)

response = chat([HumanMessage(content="Hello!")])
```

---

## Webhooks

Configure webhooks for asynchronous events:

```json
{
  "webhook_url": "https://your-server.com/webhook",
  "events": [
    "tool_call.started",
    "tool_call.completed",
    "tool_call.failed",
    "generation.done"
  ]
}
```

### Webhook Payload

```json
{
  "event": "tool_call.completed",
  "timestamp": "2026-04-01T12:00:00Z",
  "data": {
    "tool_call_id": "call_abc123",
    "tool_name": "execute_code",
    "execution_time_ms": 150,
    "result": "Hello, World!"
  }
}
```

---

## Best Practices

### 1. Use Streaming for Better UX

Always use streaming for long-form content to provide real-time feedback to users.

### 2. Implement Proper Error Handling

Always handle rate limits and authentication errors gracefully with exponential backoff.

### 3. Cache Responses

Cache frequent queries to reduce API calls and improve response times.

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_completion(prompt_hash):
    # Implement caching logic
    pass
```

### 4. Use Appropriate Temperature

| Task | Temperature |
|------|-------------|
| Code generation | 0.0 - 0.3 |
| Factual Q&A | 0.0 - 0.2 |
| Creative writing | 0.7 - 1.0 |
| brainstorming | 0.8 - 1.2 |

### 5. Monitor Token Usage

Track usage to stay within rate limits:

```python
response = client.chat.completions.create(...)
print(f"Tokens used: {response.usage.total_tokens}")
```

---

## Support

- **Documentation**: [docs/index.html](docs/index.html)
- **API Status**: [status.stack2.9.openclaw.org](https://status.stack2.9.openclaw.org)
- **Issues**: [GitHub Issues](https://github.com/openclaw/stack-2.9/issues)
- **Email**: api@stack2.9.openclaw.org

---

**API Version**: 1.0  
**Last Updated**: 2026-04-01  
**Status**: Active
