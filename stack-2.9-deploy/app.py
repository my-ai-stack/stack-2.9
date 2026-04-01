#!/usr/bin/env python3
"""
Stack 2.9 vLLM Server Entrypoint
Production-ready LLM inference server with health checks and metrics
"""

import os
import sys
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from huggingface_hub import login

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("stack-2.9")

# Initialize FastAPI app
app = FastAPI(
    title="Stack 2.9 Inference API",
    description="High-performance LLM inference using vLLM",
    version="2.9.0"
)

# Global LLM instance
llm_instance = None

def get_model_id():
    """Get model ID from environment or config"""
    model_id = os.getenv("MODEL_ID")
    if not model_id:
        # Default to a quantized model
        model_id = "TheBloke/Llama-2-7B-Chat-AWQ"
    return model_id

def get_hf_token():
    """Get Hugging Face token if provided"""
    token = os.getenv("HUGGING_FACE_TOKEN") or os.getenv("HF_TOKEN")
    return token

async def initialize_model():
    """Initialize the vLLM model"""
    global llm_instance

    model_id = get_model_id()
    hf_token = get_hf_token()

    logger.info(f"Initializing model: {model_id}")

    try:
        # Login to Hugging Face if token provided
        if hf_token:
            login(token=hf_token)

        # Engine arguments
        engine_args = AsyncEngineArgs(
            model=model_id,
            tokenizer=model_id,
            tensor_parallel_size=int(os.getenv("TENSOR_PARALLEL_SIZE", 1)),
            gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION", 0.9)),
            max_model_len=int(os.getenv("MAX_MODEL_LEN", 4096)),
            max_num_seqs=int(os.getenv("MAX_NUM_SEQS", 64)),
            max_num_batched_tokens=int(os.getenv("MAX_NUM_BATCHED_TOKENS", 4096)),
            disable_log_stats=os.getenv("DISABLE_LOG_STATS", "false").lower() == "true",
            enforce_eager=os.getenv("ENFORCE_EAGER", "false").lower() == "true",
            quantization=os.getenv("QUANTIZATION", "awq"),
            download_dir=os.getenv("MODEL_CACHE_DIR", "/home/vllm/.cache/huggingface"),
        )

        # Override quantization if not using AWQ
        if os.getenv("QUANTIZATION", "").lower() not in ["awq", "gptq", "squeezellm"]:
            engine_args.quantization = None

        llm_instance = LLM.from_engine_args(engine_args)
        logger.info("Model initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        return False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return {"status": "healthy", "model": get_model_id()}

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if llm_instance is None:
        return JSONResponse(status_code=503, content={"error": "Model not initialized"})

    # Basic metrics - can be extended
    metrics_data = {
        "model": get_model_id(),
        "status": "ready",
        "gpu_utilization": "N/A"  # Would need nvml for actual values
    }
    return JSONResponse(content=metrics_data)

@app.post("/v1/completions")
async def completions(request: Request):
    """OpenAI-compatible completions endpoint"""
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        max_tokens = int(body.get("max_tokens", 100))
        temperature = float(body.get("temperature", 0.7))
        top_p = float(body.get("top_p", 1.0))
        stream = body.get("stream", False)

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

        if stream:
            # Streaming response
            async def generate():
                try:
                    outputs = llm_instance.generate(prompt, sampling_params, stream=True)
                    async for output in outputs:
                        chunk = output.outputs[0].text
                        yield f"data: {json.dumps({'text': chunk, 'finished': False})}\n\n"
                    yield f"data: {json.dumps({'text': '', 'finished': True})}\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Non-streaming
            outputs = llm_instance.generate(prompt, sampling_params)
            generated_text = outputs[0].outputs[0].text

            return JSONResponse(content={
                "id": "cmpl-" + os.urandom(12).hex(),
                "object": "text_completion",
                "created": int(os.path.getmtime(__file__)),
                "model": get_model_id(),
                "choices": [{
                    "text": generated_text,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(generated_text.split()),
                    "total_tokens": len(prompt.split()) + len(generated_text.split())
                }
            })

    except Exception as e:
        logger.error(f"Completions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint"""
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        body = await request.json()
        messages = body.get("messages", [])

        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")

        # Format messages based on model type
        # Simple implementation - extend for specific model chat templates
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        prompt += "Assistant:"

        max_tokens = int(body.get("max_tokens", 100))
        temperature = float(body.get("temperature", 0.7))
        top_p = float(body.get("top_p", 1.0))
        stream = body.get("stream", False)

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

        if stream:
            async def generate():
                try:
                    outputs = llm_instance.generate(prompt, sampling_params, stream=True)
                    async for output in outputs:
                        chunk = output.outputs[0].text
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}] )}\n\n"
                    yield f"data: {json.dumps({'choices': [{'delta': {}}] })}\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            outputs = llm_instance.generate(prompt, sampling_params)
            generated_text = outputs[0].outputs[0].text

            return JSONResponse(content={
                "id": "chatcmpl-" + os.urandom(12).hex(),
                "object": "chat.completion",
                "created": int(os.path.getmtime(__file__)),
                "model": get_model_id(),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "logprobs": None,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(generated_text.split()),
                    "total_tokens": len(prompt.split()) + len(generated_text.split())
                }
            })

    except Exception as e:
        logger.error(f"Chat completions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("Starting Stack 2.9 inference server...")
    success = await initialize_model()
    if not success:
        logger.error("Failed to initialize model on startup")
        sys.exit(1)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        workers=1  # vLLM manages its own async
    )
