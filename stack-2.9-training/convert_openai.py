#!/usr/bin/env python3
"""
Stack 2.9 OpenAI-Compatible API Server
Provides OpenAI API format with vLLM backend for Stack 2.9.
"""

import argparse
import os
import sys
import time
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stack-2.9-api")


# Rate limiting storage (in production, use Redis)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, api_key: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[api_key] = [t for t in self.requests[api_key] if t > minute_ago]
        
        if len(self.requests[api_key]) >= self.requests_per_minute:
            return False
        
        self.requests[api_key].append(now)
        return True


# Request/Response models
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, ge=1, le=32768)
    stream: bool = False
    stop: Optional[List[str]] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Usage


# Metrics
class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.errors = 0
        self.start_time = time.time()
    
    def record(self, tokens: int, latency: float, error: bool = False):
        self.total_requests += 1
        self.total_tokens += tokens
        self.total_latency += latency
        if error:
            self.errors += 1
    
    def get(self) -> Dict:
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": (self.total_latency / self.total_requests * 1000) if self.total_requests > 0 else 0,
            "requests_per_minute": self.total_requests / (uptime / 60) if uptime > 0 else 0,
            "errors": self.errors,
            "uptime_seconds": uptime
        }


# Global state
rate_limiter = RateLimiter()
metrics = Metrics()
model = None
tokenizer = None


def get_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Extract API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    return authorization[7:]


def verify_api_key(api_key: str, valid_keys: List[str]) -> bool:
    """Verify API key against valid keys list."""
    if not valid_keys:
        return True  # No keys configured, allow all
    return api_key in valid_keys


def load_model(model_path: str):
    """Load the model with vLLM or transformers."""
    global model, tokenizer
    
    try:
        # Try vLLM first
        from vllm import LLM, SamplingParams
        logger.info(f"Loading with vLLM: {model_path}")
        model = LLM(model=model_path, trust_remote_code=True)
        tokenizer = None
        logger.info("vLLM loaded successfully")
    except ImportError:
        logger.info("vLLM not available, trying transformers...")
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True
            )
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            logger.info("Transformers loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise


def generate_with_transformers(prompt: str, params: dict) -> str:
    """Generate using transformers (fallback)."""
    global model, tokenizer
    
    messages = [
        {"role": "system", "content": "You are Stack, a helpful coding assistant."},
        {"role": "user", "content": prompt}
    ]
    
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=params.get("max_tokens", 512),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 1.0),
            do_sample=params.get("temperature", 0.7) > 0
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("assistant")[-1].strip()


# Initialize FastAPI
app = FastAPI(title="Stack 2.9 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    global model, tokenizer
    
    model_path = os.environ.get("MODEL_PATH", "./output/stack-2.9-quantized")
    logger.info(f"Loading model from {model_path}...")
    
    try:
        load_model(model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible endpoint)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "stack-2.9",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "stack-team"
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """OpenAI-compatible chat completions endpoint."""
    start_time = time.time()
    
    # Verify API key if configured
    valid_keys = os.environ.get("API_KEYS", "").split(",")
    valid_keys = [k.strip() for k in valid_keys if k.strip()]
    
    if authorization:
        api_key = authorization[7:] if authorization.startswith("Bearer ") else authorization
        if valid_keys and api_key not in valid_keys:
            metrics.record(0, time.time() - start_time, error=True)
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Rate limiting
    if not rate_limiter.is_allowed(api_key if authorization else "anonymous"):
        metrics.record(0, time.time() - start_time, error=True)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        # Build prompt from messages
        prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
        
        # Generate
        params = {
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }
        
        if tokenizer:
            response_text = generate_with_transformers(prompt, params)
        else:
            # vLLM would need different handling
            response_text = "[vLLM streaming not implemented - use transformers]"
        
        latency = time.time() - start_time
        
        # Estimate tokens (rough)
        output_tokens = len(response_text.split()) * 1.3
        input_tokens = len(prompt.split()) * 1.3
        
        metrics.record(int(output_tokens), latency)
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{int(time.time() * 1000)}",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }],
            usage=Usage(
                prompt_tokens=int(input_tokens),
                completion_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens)
            )
        )
    
    except Exception as e:
        metrics.record(0, time.time() - start_time, error=True)
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get API metrics."""
    return metrics.get()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}


@app.get("/")
async def root():
    """Root endpoint with usage info."""
    return {
        "name": "Stack 2.9 API",
        "version": "1.0.0",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "metrics": "/metrics",
            "health": "/health"
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model-path", type=str, default="./output/stack-2.9-quantized")
    parser.add_argument("--api-keys", type=str, help="Comma-separated API keys (optional)")
    parser.add_argument("--rate-limit", type=int, default=60, help="Requests per minute")
    args = parser.parse_args()
    
    # Set environment
    os.environ["MODEL_PATH"] = args.model_path
    if args.api_keys:
        os.environ["API_KEYS"] = args.api_keys
    
    rate_limiter.requests_per_minute = args.rate_limit
    
    print("=" * 60)
    print("Stack 2.9 OpenAI-Compatible API Server")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Model: {args.model_path}")
    print(f"Rate limit: {args.rate_limit} req/min")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /v1/chat/completions - Chat completions")
    print("  GET  /v1/models           - List models")
    print("  GET  /metrics             - API metrics")
    print("  GET  /health              - Health check")
    print("=" * 60)
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()