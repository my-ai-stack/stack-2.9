"""
HuggingFace Spaces Deployment for Stack 2.9

Free inference API on HuggingFace Spaces.
https://huggingface.co/docs/hub/spaces-sdks-docker
"""

# =============================================================================
# app.py - Stack 2.9 Inference API
# Deploy this to HuggingFace Spaces for free inference
# =============================================================================

import os
import json
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="Stack 2.9 API")

# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-Coder-7B-Instruct")
API_URL = os.environ.get("API_URL", "")  # Your model API URL
HF_TOKEN = os.environ.get("HF_TOKEN", "")  # HuggingFace token

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict] = None

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME}

@app.get("/")
async def root():
    return {
        "name": "Stack 2.9",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "endpoints": {
            "chat": "/v1/chat/completions",
            "complete": "/v1/completions",
            "health": "/health"
        }
    }

# ============================================================================
# OpenAI-Compatible API
# ============================================================================

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat endpoint"""

    if API_URL:
        # Use external API
        response = requests.post(
            f"{API_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={
                "messages": [m.dict() for m in request.messages],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
            timeout=60
        )
        return response.json()

    # Placeholder for local model
    raise HTTPException(
        status_code=503,
        detail="No model API configured. Set API_URL environment variable."
    )

@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """OpenAI-compatible completion endpoint"""

    if API_URL:
        response = requests.post(
            f"{API_URL}/v1/completions",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
            timeout=60
        )
        return response.json()

    raise HTTPException(
        status_code=503,
        detail="No model API configured"
    )

# ============================================================================
# Model Info
# ============================================================================

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 1700000000,
                "owned_by": "stack-2.9"
            }
        ]
    }

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)