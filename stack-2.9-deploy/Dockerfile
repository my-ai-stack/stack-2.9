# Stack 2.9 HuggingFace Spaces Dockerfile
# Optimized for 16GB GPU with 4-bit quantization

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/workspace/.cache/huggingface
ENV HF_HOME=/workspace/.cache/huggingface

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
WORKDIR /workspace

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Gradio port
EXPOSE 7860

# Create startup script
RUN echo '#!/bin/bash\necho "🚀 Starting Stack 2.9..."\npython app.py --port 7860 --share' > /start.sh
RUN chmod +x /start.sh

# Launch command
CMD ["/start.sh"]