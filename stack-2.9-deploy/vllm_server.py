#!/usr/bin/env python3
"""
Production-ready vLLM server for Stack 2.9
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import torch
import redis
import prometheus_client
from flask import Flask, request, jsonify, Response
from vllm import LLM
from vllm.server import app as vllm_app
from vllm.server.api import chat_completions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = prometheus_client.Counter(
    'vllm_requests_total', 'Total vLLM requests', ['method', 'endpoint']
)
REQUEST_LATENCY = prometheus_client.Histogram(
    'vllm_request_latency_seconds', 'vLLM request latency'
)

class Stack29LLM:
    def __init__(self):
        self.model = None
        self.redis_client = None
        self.load_config()
        self.setup_model()
        self.setup_redis()
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.model_path = os.getenv('MODEL_PATH', '/models')
        self.model_name = os.getenv('MODEL_NAME', 'meta-llama/Llama-3.1-8B-Instruct')
        self.model_format = os.getenv('MODEL_FORMAT', 'hf')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.gpu_memory_utilization = float(os.getenv('GPU_MEMORY_UTILIZATION', '0.9'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        logger.setLevel(getattr(logging, self.log_level))
        
    def setup_model(self):
        """Load or initialize the model"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            
            # Check if model is already loaded locally
            model_dir = Path(self.model_path)
            if model_dir.exists() and list(model_dir.iterdir()):
                model_path = str(model_dir)
                logger.info(f"Found local model at {model_path}")
                model_name = model_path
                model_format = 'local'
            else:
                model_name = self.model_name
                model_format = self.model_format
                logger.info(f"Downloading model from HuggingFace: {model_name}")
            
            # Configure GPU settings
            device_map = 'auto'
            if torch.cuda.is_available():
                num_gpus = torch.cuda.device_count()
                logger.info(f"Found {num_gpus} GPU(s)")
                
                # Set tensor parallel size
                tensor_parallel_size = min(num_gpus, 8)  # Limit to 8 for stability
                logger.info(f"Setting tensor_parallel_size to {tensor_parallel_size}")
                
                # Enable AWQ quantization if available
                quantization_config = {
                    'method': 'awq',
                    'gpu_memory_utilization': self.gpu_memory_utilization
                }
                
                self.model = LLM(
                    model_name=model_name,
                    model_format=model_format,
                    device_map=device_map,
                    tensor_parallel_size=tensor_parallel_size,
                    quantization_config=quantization_config if 'awq' in sys.modules else None,
                    trust_remote_code=True
                )
            else:
                logger.warning("No GPU detected, using CPU (this will be very slow)")
                self.model = LLM(
                    model_name=model_name,
                    model_format=model_format,
                    device_map='cpu',
                    trust_remote_code=True
                )
                
            logger.info("Model loaded successfully")
            logger.info(f"Model details: {self.model.llm.config}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            sys.exit(1)
            
    def setup_redis(self):
        """Setup Redis client for caching"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.redis_client = None
    
    def get_model_info(self):
        """Get model information for health checks"""
        if self.model:
            return {
                'model_name': getattr(self.model.llm.config, 'name', 'unknown'),
                'model_type': getattr(self.model.llm.config, 'model_type', 'unknown'),
                'quantization': getattr(self.model.llm.config, 'quantization', 'none'),
                'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'is_loaded': True
            }
        return {'is_loaded': False}

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__)
    
    # Add Prometheus metrics endpoint
    app.route('/metrics')(prometheus_client.generate_latest)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            model_info = stack29_llm.get_model_info()
            if model_info['is_loaded']:
                return jsonify({
                    'status': 'healthy',
                    'model': model_info,
                    'timestamp': prometheus_client.time()
                }), 200
            else:
                return jsonify({
                    'status': 'unhealthy',
                    'reason': 'Model not loaded',
                    'timestamp': prometheus_client.time()
                }), 503
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'error',
                'reason': str(e),
                'timestamp': prometheus_client.time()
            }), 500
    
    @app.route('/ready', methods=['GET'])
    def ready_check():
        """Readiness check endpoint"""
        try:
            model_info = stack29_llm.get_model_info()
            if model_info['is_loaded']:
                return jsonify({'status': 'ready'}), 200
            return jsonify({'status': 'not_ready'}), 503
        except Exception as e:
            logger.error(f"Ready check failed: {e}")
            return jsonify({'status': 'error', 'reason': str(e)}), 500
    
    @app.route('/v1/models', methods=['GET'])
    def list_models():
        """List available models (OpenAI compatible)"""
        REQUEST_COUNT.labels('GET', '/v1/models').inc()
        
        try:
            model_info = stack29_llm.get_model_info()
            
            if not model_info['is_loaded']:
                return jsonify({'error': 'Model not loaded'}), 503
            
            return jsonify({
                'models': [{
                    'id': model_info.get('model_name', 'unknown'),
                    'object': 'model',
                    'owned_by': 'stack29',
                    'permission': 'read',
                    'status': {
                        'code': 'available'
                    }
                }]
            })
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """Chat completions endpoint (OpenAI compatible)"""
        REQUEST_COUNT.labels('POST', '/v1/chat/completions').inc()
        
        start_time = prometheus_client.time()
        
        try:
            data = request.get_json()
            if not data or 'messages' not in data:
                return jsonify({'error': 'Invalid request format'}), 400
            
            messages = data.get('messages', [])
            model = data.get('model', 'unknown')
            max_tokens = data.get('max_tokens', 2048)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 1.0)
            stream = data.get('stream', False)
            
            # Get model info
            model_info = stack29_llm.get_model_info()
            if not model_info['is_loaded']:
                return jsonify({'error': 'Model not loaded'}), 503
            
            # Use the loaded model
            if model != model_info.get('model_name', 'unknown'):
                return jsonify({'error': 'Model not found'}), 404
            
            # Convert messages to vLLM format
            vllm_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    vllm_messages.append(('system', msg['content']))
                elif msg['role'] == 'user':
                    vllm_messages.append(('user', msg['content']))
                elif msg['role'] == 'assistant':
                    vllm_messages.append(('assistant', msg['content']))
            
            # Generate response
            response = stack29_llm.model.generate(
                messages=vllm_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream
            )
            
            if stream:
                def generate_stream():
                    for chunk in response:
                        yield f"data: {chunk.decode('utf-8')}\n\n"
                
                return Response(
                    generate_stream(),
                    mimetype='text/plain'
                )
            else:
                return jsonify({
                    'id': 'chatcmpl-123',  # Would be actual ID in production
                    'object': 'chat.completion',
                    'created': int(start_time),
                    'model': model,
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': response
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': 0,  # Would calculate actual tokens
                        'completion_tokens': 0,
                        'total_tokens': 0
                    }
                })
                
        except Exception as e:
            logger.error(f"Chat completions failed: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            latency = prometheus_client.time() - start_time
            REQUEST_LATENCY.observe(latency)
    
    @app.route('/v1/completions', methods=['POST'])
    def completions():
        """Completions endpoint (OpenAI compatible)"""
        REQUEST_COUNT.labels('POST', '/v1/completions').inc()
        
        start_time = prometheus_client.time()
        
        try:
            data = request.get_json()
            if not data or 'prompt' not in data:
                return jsonify({'error': 'Invalid request format'}), 400
            
            prompt = data.get('prompt', '')
            model = data.get('model', 'unknown')
            max_tokens = data.get('max_tokens', 2048)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 1.0)
            stream = data.get('stream', False)
            
            # Get model info
            model_info = stack29_llm.get_model_info()
            if not model_info['is_loaded']:
                return jsonify({'error': 'Model not loaded'}), 503
            
            if model != model_info.get('model_name', 'unknown'):
                return jsonify({'error': 'Model not found'}), 404
            
            # Generate response
            response = stack29_llm.model.generate(
                messages=[('user', prompt)],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream
            )
            
            if stream:
                def generate_stream():
                    for chunk in response:
                        yield f"data: {chunk.decode('utf-8')}\n\n"
                
                return Response(
                    generate_stream(),
                    mimetype='text/plain'
                )
            else:
                return jsonify({
                    'id': 'cmpl-123',
                    'object': 'completion',
                    'created': int(start_time),
                    'model': model,
                    'choices': [{
                        'text': response,
                        'index': 0,
                        'logprobs': None,
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'total_tokens': 0
                    }
                })
                
        except Exception as e:
            logger.error(f"Completions failed: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            latency = prometheus_client.time() - start_time
            REQUEST_LATENCY.observe(latency)
    
    return app

if __name__ == '__main__':
    # Initialize the Stack29LLM instance
    stack29_llm = Stack29LLM()
    
    # Create and run the app
    app = create_app()
    
    # Run the vLLM server on port 8000
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)