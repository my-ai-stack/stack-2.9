# Multi-stage production Docker image for Stack 2.9
# Stack 2.9 LLM Inference Server with vLLM

ARG PYTHON_VERSION=3.10
ARG VLLM_VERSION=0.6.3
ARG CUDA_VERSION=12.1.0
ARG BASE_IMAGE=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu22.04

# Stage 1: Builder
FROM ${BASE_IMAGE} AS builder

ARG PYTHON_VERSION
ARG VLLM_VERSION

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies and Python
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA 12.1 support
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# Install vLLM
RUN pip3 install vllm==${VLLM_VERSION} "vllm[attention]"

# Install additional dependencies
RUN pip3 install \
    fastapi==0.111.0 \
    uvicorn[standard]==0.30.1 \
    transformers==4.41.2 \
    accelerate==0.30.1 \
    huggingface-hub==0.23.0 \
    sentencepiece==0.2.0 \
    protobuf==3.20.3

# Stage 2: Runtime
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu22.04

ARG PYTHON_VERSION
ARG VLLM_VERSION

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    VLLM_USE_MODELSCOPE=false \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1

# Install Python and minimal dependencies
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    git \
    curl \
    wget \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/dist-packages /usr/local/lib/python${PYTHON_VERSION}/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user
RUN groupadd -r vllm && useradd -r -g vllm -d /home/vllm -m vllm

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vllm:vllm app.py .
COPY --chown=vllm:vllm requirements.txt .
COPY --chown=vllm:vllm config.yaml .

# Create model cache directory
RUN mkdir -p /home/vllm/.cache/huggingface && chown -R vllm:vllm /home/vllm/.cache

# Expose port for vLLM server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER vllm

# Run vLLM server
CMD ["python3", "app.py"]
