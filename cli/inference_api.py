#!/usr/bin/env python3
"""
FastAPI Inference Server for Stack 2.9 Model
Provides REST API endpoints for code generation using fine-tuned Qwen models.

Usage:
    # With default settings (model loaded from environment or config)
    uvicorn inference_api:app --host 0.0.0.0 --port 8000
    
    # With custom model path
    MODEL_PATH=/path/to/model uvicorn inference_api:app --host 0.0.0.0 --port 8000
    
    # With reload for development
    uvicorn inference_api:app --reload --port 8000
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_PATH = os.getenv("MODEL_PATH", "base_model_qwen7b")
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "512"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))
DEFAULT_TOP_P = float(os.getenv("DEFAULT_TOP_P", "0.95"))

# Global model and tokenizer (loaded on startup)
model = None
tokenizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    global model, tokenizer
    logger.info(f"Loading model from: {MODEL_PATH}")
    logger.info(f"Using device: {DEVICE}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True,
            padding_side="left",
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device_map="auto" if DEVICE == "cuda" else None,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        
        if DEVICE == "cpu":
            model = model.to(DEVICE)
        
        model.eval()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down, cleaning up model...")
    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="Stack 2.9 Inference API",
    description="REST API for code generation using Stack 2.9 fine-tuned Qwen model",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateRequest(BaseModel):
    """Request body for /generate endpoint."""
    prompt: str = Field(..., description="Input prompt/code to complete", min_length=1)
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, ge=1, le=4096, description="Max tokens to generate")
    temperature: float = Field(DEFAULT_TEMPERATURE, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(DEFAULT_TOP_P, ge=0.0, le=1.0, description="Nucleus sampling threshold")
    do_sample: bool = Field(True, description="Whether to use sampling")
    repetition_penalty: float = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty")
    num_return_sequences: int = Field(1, ge=1, le=10, description="Number of sequences to generate")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": "def two_sum(nums, target):\n    \"\"\"Return indices of two numbers that add up to target.\"\"\"\n",
                "max_tokens": 128,
                "temperature": 0.2,
                "top_p": 0.95,
            }
        }
    }


class GenerateResponse(BaseModel):
    """Response body for /generate endpoint."""
    generated_text: str
    prompt: str
    model: str
    num_tokens: int
    finish_reason: str = "length"


class ChatMessage(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    messages: List[ChatMessage] = Field(..., description="Conversation history")
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, ge=1, le=4096, description="Max tokens to generate")
    temperature: float = Field(DEFAULT_TEMPERATURE, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(DEFAULT_TOP_P, ge=0.0, le=1.0, description="Nucleus sampling threshold")
    do_sample: bool = Field(True, description="Whether to use sampling")
    repetition_penalty: float = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {"role": "user", "content": "Write a function to reverse a string in Python"},
                    {"role": "assistant", "content": "def reverse_string(s):\n    return s[::-1]"},
                    {"role": "user", "content": "Make it recursive"},
                ],
                "max_tokens": 128,
                "temperature": 0.2,
            }
        }
    }


class ChatResponse(BaseModel):
    """Response body for /chat endpoint."""
    message: ChatMessage
    model: str
    num_tokens: int
    finish_reason: str = "length"


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    status: str
    model_loaded: bool
    model_path: str
    device: str
    cuda_available: bool


class ModelInfoResponse(BaseModel):
    """Response body for /model-info endpoint."""
    model_path: str
    device: str
    dtype: str


# ============================================================================
# Helper Functions
# ============================================================================

def format_chat_to_prompt(messages: List[ChatMessage]) -> str:
    """
    Format chat messages into a prompt for code generation.
    Uses a simple instruction format suitable for Qwen.
    """
    formatted = []
    for msg in messages:
        if msg.role == "user":
            formatted.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
        elif msg.role == "assistant":
            formatted.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")
    
    formatted.append("<|im_start|>assistant\n")
    return "\n".join(formatted)


def generate_response(
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    do_sample: bool,
    repetition_penalty: float,
    num_return_sequences: int,
) -> tuple[str, int, str]:
    """
    Generate response from model.
    
    Returns:
        tuple: (generated_text, num_tokens, finish_reason)
    """
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
            num_return_sequences=num_return_sequences,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Decode the first sequence
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Calculate number of generated tokens
    num_tokens = outputs.shape[1] - inputs["input_ids"].shape[1]
    
    # Extract just the new tokens (remove prompt)
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):]
    
    generated_text = generated_text.strip()
    
    # Determine finish reason
    finish_reason = "stop"
    if num_tokens >= max_new_tokens:
        finish_reason = "length"
    
    return generated_text, num_tokens, finish_reason


def extract_code_from_response(text: str) -> str:
    """Extract code block from response if present."""
    if "```python" in text:
        start = text.find("```python") + len("```python")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + len("```")
        # Skip potential language identifier
        if "\n" in text[start:]:
            start = text.find("\n", start) + 1
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    return text


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API and model.
    """
    return HealthResponse(
        status="healthy" if model is not None else "model_not_loaded",
        model_loaded=model is not None,
        model_path=MODEL_PATH,
        device=DEVICE,
        cuda_available=torch.cuda.is_available(),
    )


@app.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Get information about the loaded model.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    dtype = str(next(model.parameters()).dtype)
    
    return ModelInfoResponse(
        model_path=MODEL_PATH,
        device=str(next(model.parameters()).device),
        dtype=dtype,
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate code completion for a prompt.
    
    Takes a prompt and generates code completion based on the model.
    Supports various generation parameters for controlling output.
    """
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check /health for status."
        )
    
    try:
        generated_text, num_tokens, finish_reason = generate_response(
            prompt=request.prompt,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=request.do_sample,
            repetition_penalty=request.repetition_penalty,
            num_return_sequences=request.num_return_sequences,
        )
        
        return GenerateResponse(
            generated_text=generated_text,
            prompt=request.prompt,
            model=MODEL_PATH,
            num_tokens=num_tokens,
            finish_reason=finish_reason,
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate/raw", response_model=GenerateResponse)
async def generate_raw(request: GenerateRequest):
    """
    Generate without extracting code from markdown blocks.
    
    Returns the raw model output without any post-processing.
    """
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check /health for status."
        )
    
    try:
        # Get raw response
        inputs = tokenizer(
            request.prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.do_sample,
                repetition_penalty=request.repetition_penalty,
                num_return_sequences=request.num_return_sequences,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        num_tokens = outputs.shape[1] - inputs["input_ids"].shape[1]
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if generated_text.startswith(request.prompt):
            generated_text = generated_text[len(request.prompt):]
        
        finish_reason = "stop" if num_tokens < request.max_tokens else "length"
        
        return GenerateResponse(
            generated_text=generated_text.strip(),
            prompt=request.prompt,
            model=MODEL_PATH,
            num_tokens=num_tokens,
            finish_reason=finish_reason,
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for conversation-style interactions.
    
    Takes a conversation history and generates the next assistant response.
    """
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check /health for status."
        )
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")
    
    # Check that last message is from user
    if request.messages[-1].role != "user":
        raise HTTPException(
            status_code=400,
            detail="Last message must be from user"
        )
    
    try:
        # Format conversation as prompt
        prompt = format_chat_to_prompt(request.messages)
        
        generated_text, num_tokens, finish_reason = generate_response(
            prompt=prompt,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=request.do_sample,
            repetition_penalty=request.repetition_penalty,
            num_return_sequences=1,
        )
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=generated_text),
            model=MODEL_PATH,
            num_tokens=num_tokens,
            finish_reason=finish_reason,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


@app.post("/extract-code")
async def extract_code(request: GenerateRequest):
    """
    Extract code from a generated response.
    
    Useful when you have raw output with markdown code blocks and want to
    extract just the code portion.
    """
    code = extract_code_from_response(request.prompt)
    return {"code": code}


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "inference_api:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        workers=1,  # Multi-worker can cause GPU memory issues
    )
