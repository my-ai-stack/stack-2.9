#!/usr/bin/env python3
"""
Production-ready vLLM server for Stack 2.9
"""

import os
import sys
import json
import signal
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
import torch
import redis
import prometheus_client
from flask import Flask, request, jsonify, Response, abort
from vllm import LLM
from vllm.sampling_params import SamplingParams

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/vllm.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = prometheus_client.Counter(
    'vllm_requests_total', 'Total vLLM requests', ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = prometheus_client.Histogram(
    'vllm_request_latency_seconds', 'vLLM request latency', ['endpoint']
)
GPU_MEMORY = prometheus_client.Gauge(
    'vllm_gpu_memory_usage_bytes', 'GPU memory usage'
)
MODEL_LOADED = prometheus_client.Gauge(
    'vllm_model_loaded', 'Model loaded status (1=yes, 0=no)'
)

class Stack29LLM:
    """Wrapper for vLLM with Redis caching and error handling"""

    def __init__(self):
        self.model: Optional[LLM] = None
        self.redis_client: Optional[redis.Redis] = None
        self.config: Dict[str, Any] = {}
        self.start_time = time.time()
        self.load_config()
        self.setup_redis()
        self.setup_signal_handlers()
        self.setup_model()

    def load_config(self):
        """Load configuration from environment variables with validation"""
        self.model_path = os.getenv('MODEL_PATH', '/models')
        self.model_name = os.getenv('MODEL_NAME', 'meta-llama/Llama-3.1-8B-Instruct')
        self.model_format = os.getenv('MODEL_FORMAT', 'hf').lower()
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.gpu_memory_utilization = float(os.getenv('GPU_MEMORY_UTILIZATION', '0.9'))
        self.max_model_len = int(os.getenv('MAX_MODEL_LEN', '131072'))
        self.block_size = int(os.getenv('BLOCK_SIZE', '64'))
        self.quantization = os.getenv('QUANTIZATION', '').lower()
        self.max_batch_size = int(os.getenv('MAX_BATCH_SIZE', '16'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # Validate configuration
        if not 0.0 <= self.gpu_memory_utilization <= 1.0:
            raise ValueError(f"GPU_MEMORY_UTILIZATION must be between 0.0 and 1.0, got {self.gpu_memory_utilization}")

        if self.max_model_len < 512:
            raise ValueError(f"MAX_MODEL_LEN must be at least 512, got {self.max_model_len}")

        logger.setLevel(getattr(logging, self.log_level))
        logger.info(f"Configuration loaded: model={self.model_name}, max_len={self.max_model_len}")

    def setup_redis(self):
        """Setup Redis client for response caching"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Continuing without caching.")
            self.redis_client = None

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, cleaning up...")
        if self.model:
            logger.info("Emptying cache before shutdown...")
            self.model.empty_cache()
        sys.exit(0)

    def setup_model(self):
        """Load or initialize the model with comprehensive error handling"""
        try:
            logger.info(f"Loading model from {self.model_path}")

            # Determine model source
            model_dir = Path(self.model_path)
            if model_dir.exists() and any(model_dir.iterdir()):
                model_source = str(model_dir)
                model_format = 'local'
                logger.info(f"Found local model at {model_source}")
            else:
                model_source = self.model_name
                model_format = self.model_format
                logger.info(f"Will download model from HuggingFace: {model_source}")

            # Check CUDA availability
            if torch.cuda.is_available():
                num_gpus = torch.cuda.device_count()
                logger.info(f"Found {num_gpus} GPU(s)")

                # Get GPU memory for logging
                for i in range(num_gpus):
                    props = torch.cuda.get_device_properties(i)
                    total_mem = props.total_memory / (1024**3)
                    logger.info(f"  GPU {i}: {props.name} with {total_mem:.2f} GB")

                tensor_parallel_size = min(num_gpus, 8)
                logger.info(f"Setting tensor_parallel_size to {tensor_parallel_size}")
            else:
                logger.warning("No GPU detected. Model will run on CPU (very slow)")
                num_gpus = 0
                tensor_parallel_size = 0

            # Build vLLM configuration
            vllm_config = {
                'model': model_source,
                'model_format': model_format,
                'trust_remote_code': True,
                'max_model_len': self.max_model_len,
                'block_size': self.block_size,
                'tensor_parallel_size': tensor_parallel_size,
                'gpu_memory_utilization': self.gpu_memory_utilization,
                'scheduler_config': {
                    'policy': 'fcfs',
                    'max_batch_size': self.max_batch_size,
                }
            }

            # Add quantization if requested and available
            if self.quantization == 'awq':
                try:
                    import awq
                    vllm_config['quantization'] = 'awq'
                    logger.info("Enabled AWQ quantization")
                except ImportError:
                    logger.warning("AWQ requested but not available, running without quantization")

            logger.info(f"Initializing vLLM with config: {json.dumps(vllm_config, indent=2)}")

            # Initialize model
            self.model = LLM(**vllm_config)

            # Set model loaded metric
            MODEL_LOADED.set(1)

            # Log success
            logger.info("✅ Model loaded successfully")
            if hasattr(self.model, 'llm') and hasattr(self.model.llm, 'config'):
                config = self.model.llm.config
                logger.info(f"Model config: name={getattr(config, 'name', 'unknown')}, "
                          f"type={getattr(config, 'model_type', 'unknown')}, "
                          f"quant={getattr(config, 'quantization', 'none')}")

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"❌ GPU Out of Memory: {e}")
            logger.error("Consider reducing MAX_MODEL_LEN, BLOCK_SIZE, or GPU_MEMORY_UTILIZATION")
            MODEL_LOADED.set(0)
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            MODEL_LOADED.set(0)
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information for health checks"""
        if self.model and hasattr(self.model, 'llm'):
            config = self.model.llm.config
            return {
                'model_name': getattr(config, 'name', 'unknown'),
                'model_type': getattr(config, 'model_type', 'unknown'),
                'quantization': getattr(config, 'quantization', 'none'),
                'max_model_len': self.max_model_len,
                'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'uptime_seconds': time.time() - self.start_time,
                'is_loaded': True
            }
        return {
            'is_loaded': False,
            'uptime_seconds': time.time() - self.start_time
        }

    def check_health(self) -> tuple[bool, Optional[str]]:
        """Comprehensive health check"""
        try:
            if not self.model:
                return False, "Model not initialized"

            if not hasattr(self.model, 'llm'):
                return False, "Model not properly loaded"

            # Check if model can generate (basic sanity check)
            # Use a tiny test generation to verify model is functional
            test_prompt = "Hello"
            sampling_params = SamplingParams(max_tokens=1, temperature=0.1)
            _ = self.model.generate(test_prompt, sampling_params)

            return True, None
        except torch.cuda.OutOfMemoryError as e:
            return False, f"GPU OOM: {str(e)}"
        except Exception as e:
            return False, str(e)

# Global instance
stack29_llm: Optional[Stack29LLM] = None

def create_app():
    """Create and configure the Flask application"""
    global stack29_llm
    app = Flask(__name__)

    # Prometheus metrics endpoint
    @app.route('/metrics', methods=['GET'])
    def metrics():
        return prometheus_client.generate_latest()

    @app.route('/health', methods=['GET'])
    def health_check():
        """Comprehensive health check endpoint"""
        start_time = time.time()
        try:
            if not stack29_llm:
                return jsonify({
                    'status': 'error',
                    'reason': 'Server not initialized',
                    'timestamp': time.time()
                }), 500

            healthy, reason = stack29_llm.check_health()
            latency = time.time() - start_time

            if healthy:
                return jsonify({
                    'status': 'healthy',
                    'model': stack29_llm.get_model_info(),
                    'latency_ms': latency * 1000,
                    'timestamp': time.time()
                }), 200
            else:
                REQUEST_COUNT.labels('GET', '/health', 'unhealthy').inc()
                return jsonify({
                    'status': 'unhealthy',
                    'reason': reason,
                    'model': stack29_llm.get_model_info(),
                    'latency_ms': latency * 1000,
                    'timestamp': time.time()
                }), 503
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'error',
                'reason': str(e),
                'timestamp': time.time()
            }), 500

    @app.route('/ready', methods=['GET'])
    def ready_check():
        """Kubernetes-style readiness probe"""
        if not stack29_llm or not stack29_llm.model:
            return jsonify({'status': 'not_ready', 'reason': 'Model not loaded'}), 503
        return jsonify({'status': 'ready'}), 200

    @app.route('/v1/models', methods=['GET'])
    def list_models():
        """List available models (OpenAI compatible)"""
        start_time = time.time()
        try:
            if not stack29_llm or not stack29_llm.model:
                REQUEST_COUNT.labels('GET', '/v1/models', 'error').inc()
                return jsonify({'error': 'Model not loaded'}), 503

            model_info = stack29_llm.get_model_info()
            return jsonify({
                'object': 'list',
                'data': [{
                    'id': model_info.get('model_name', 'unknown'),
                    'object': 'model',
                    'owned_by': 'stack29',
                    'permission': ['read'],
                    'status': {'code': 'available'}
                }]
            })
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            REQUEST_COUNT.labels('GET', '/v1/models', 'error').inc()
            return jsonify({'error': str(e)}), 500
        finally:
            latency = time.time() - start_time
            REQUEST_LATENCY.labels('/v1/models').observe(latency)

    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """Chat completions endpoint (OpenAI compatible)"""
        start_time = time.time()
        endpoint = '/v1/chat/completions'

        try:
            if not stack29_llm or not stack29_llm.model:
                REQUEST_COUNT.labels('POST', endpoint, 'error').inc()
                return jsonify({'error': 'Model not loaded'}), 503

            data = request.get_json()
            if not data:
                REQUEST_COUNT.labels('POST', endpoint, 'error').inc()
                return jsonify({'error': 'Invalid request: no JSON body'}), 400

            # Extract parameters
            messages = data.get('messages')
            if not messages or not isinstance(messages, list):
                return jsonify({'error': 'Invalid request: messages is required and must be an array'}), 400

            model_name = data.get('model', stack29_llm.get_model_info().get('model_name', 'unknown'))
            max_tokens = min(int(data.get('max_tokens', 2048)), 4096)  # Cap at 4096
            temperature = max(0.0, min(float(data.get('temperature', 0.7)), 2.0))  # Clamp to [0, 2]
            top_p = max(0.0, min(float(data.get('top_p', 1.0)), 1.0))
            stream = bool(data.get('stream', False))

            # Convert messages to vLLM format
            prompts = []
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')
                if role == 'system':
                    prompts.append(f"System: {content}")
                elif role == 'user':
                    prompts.append(f"User: {content}")
                elif role == 'assistant':
                    prompts.append(f"Assistant: {content}")
                else:
                    logger.warning(f"Unknown role: {role}")

            final_prompt = "\n".join(prompts)

            # Create sampling parameters
            sampling_params = SamplingParams(
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            # Generate response
            logger.info(f"Generating response for prompt length {len(final_prompt)}")
            outputs = stack29_llm.model.generate([final_prompt], sampling_params)

            if not outputs:
                raise ValueError("No output generated")

            generated_text = outputs[0].outputs[0].text

            if stream:
                # Streaming response
                def generate():
                    for chunk in generated_text:
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
                    yield "data: [DONE]\n\n"

                return Response(generate(), mimetype='text/plain')
            else:
                # Non-streaming response
                response = {
                    'id': f"chatcmpl-{int(time.time())}",
                    'object': 'chat.completion',
                    'created': int(time.time()),
                    'model': model_name,
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': generated_text
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': len(final_prompt.split()),  # Rough estimate
                        'completion_tokens': len(generated_text.split()),
                        'total_tokens': len(final_prompt.split()) + len(generated_text.split())
                    }
                }
                return jsonify(response)

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU OOM during generation: {e}")
            REQUEST_COUNT.labels('POST', endpoint, 'oom').inc()
            return jsonify({
                'error': 'GPU out of memory',
                'detail': str(e),
                'suggestion': 'Reduce max_tokens or batch size, or use a smaller model'
            }), 507  # Insufficient storage
        except Exception as e:
            logger.error(f"Chat completions failed: {e}")
            REQUEST_COUNT.labels('POST', endpoint, 'error').inc()
            return jsonify({'error': str(e)}), 500
        finally:
            latency = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint).observe(latency)

    @app.route('/v1/completions', methods=['POST'])
    def completions():
        """Completions endpoint (OpenAI compatible)"""
        start_time = time.time()
        endpoint = '/v1/completions'

        try:
            if not stack29_llm or not stack29_llm.model:
                REQUEST_COUNT.labels('POST', endpoint, 'error').inc()
                return jsonify({'error': 'Model not loaded'}), 503

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request: no JSON body'}), 400

            prompt = data.get('prompt', '')
            if not prompt:
                return jsonify({'error': 'Invalid request: prompt is required'}), 400

            model_name = data.get('model', stack29_llm.get_model_info().get('model_name', 'unknown'))
            max_tokens = min(int(data.get('max_tokens', 2048)), 4096)
            temperature = max(0.0, min(float(data.get('temperature', 0.7)), 2.0))
            top_p = max(0.0, min(float(data.get('top_p', 1.0)), 1.0))
            stream = bool(data.get('stream', False))

            sampling_params = SamplingParams(
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            logger.info(f"Generating completion for prompt length {len(prompt)}")
            outputs = stack29_llm.model.generate([prompt], sampling_params)

            if not outputs:
                raise ValueError("No output generated")

            generated_text = outputs[0].outputs[0].text

            if stream:
                def generate():
                    for chunk in generated_text:
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
                    yield "data: [DONE]\n\n"

                return Response(generate(), mimetype='text/plain')
            else:
                response = {
                    'id': f"cmpl-{int(time.time())}",
                    'object': 'completion',
                    'created': int(time.time()),
                    'model': model_name,
                    'choices': [{
                        'text': generated_text,
                        'index': 0,
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': len(prompt.split()),
                        'completion_tokens': len(generated_text.split()),
                        'total_tokens': len(prompt.split()) + len(generated_text.split())
                    }
                }
                return jsonify(response)

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU OOM during completion: {e}")
            REQUEST_COUNT.labels('POST', endpoint, 'oom').inc()
            return jsonify({
                'error': 'GPU out of memory',
                'detail': str(e),
                'suggestion': 'Reduce max_tokens or use a smaller model'
            }), 507
        except Exception as e:
            logger.error(f"Completions failed: {e}")
            REQUEST_COUNT.labels('POST', endpoint, 'error').inc()
            return jsonify({'error': str(e)}), 500
        finally:
            latency = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint).observe(latency)

    @app.route('/status', methods=['GET'])
    def status():
        """Detailed server status"""
        if not stack29_llm:
            return jsonify({'error': 'Server not initialized'}), 500

        info = stack29_llm.get_model_info()
        return jsonify({
            'status': 'running',
            'uptime': time.time() - stack29_llm.start_time,
            'model': info,
            'config': stack29_llm.config
        })

    return app

def main():
    """Main entry point"""
    global stack29_llm

    try:
        logger.info("Initializing Stack 2.9 vLLM Server...")
        stack29_llm = Stack29LLM()
        app = create_app()

        # Get port from environment or default to 8000
        port = int(os.getenv('VLLM_PORT', os.getenv('PORT', '8000')))
        host = os.getenv('VLLM_HOST', '0.0.0.0')

        logger.info(f"Starting Flask server on {host}:{port}")
        app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
