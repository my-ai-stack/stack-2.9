# Build stage
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir \
    vllm>=0.4.0 \
    torch>=2.0.0 \
    torchvision>=0.15.0 \
    torchaudio>=2.0.0 \
    transformers>=4.30.0 \
    accelerate>=0.20.0 \
    bitsandbytes>=0.40.0 \
    redis>=4.5.0 \
    prometheus-client>=0.16.0 \
    flask>=2.3.0 \
    gunicorn>=20.1.0 \
    requests>=2.31.0 \
    aiohttp>=3.8.0 \
    python-dotenv>=1.0.0 \
    && rm -rf /root/.cache/pip

# Copy application code
WORKDIR /app
COPY vllm_server.py /app/
COPY requirements.txt /app/requirements.txt

# Runtime stage
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir \
    vllm>=0.4.0 \
    torch>=2.0.0 \
    torchvision>=0.15.0 \
    torchaudio>=2.0.0 \
    transformers>=4.30.0 \
    accelerate>=0.20.0 \
    bitsandbytes>=0.40.0 \
    redis>=4.5.0 \
    prometheus-client>=0.16.0 \
    flask>=2.3.0 \
    gunicorn>=20.1.0 \
    requests>=2.31.0 \
    aiohttp>=3.8.0 \
    python-dotenv>=1.0.0 \
    && rm -rf /root/.cache/pip

# Create app directory
WORKDIR /app

# Copy application code from builder stage
COPY --from=builder /app/vllm_server.py /app/

# Create necessary directories
RUN mkdir -p /models /logs

# Set environment variables
ENV PYTHONPATH=/app
ENV MODEL_PATH=/models
ENV MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
ENV MODEL_FORMAT=hf
ENV REDIS_URL=redis://localhost:6379
ENV GPU_MEMORY_UTILIZATION=0.9
ENV LOG_LEVEL=INFO
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "vllm_server:app"]