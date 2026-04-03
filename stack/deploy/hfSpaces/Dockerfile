# HuggingFace Spaces Dockerfile for Stack 2.9
# Use this for free inference hosting on HF Spaces
# https://huggingface.co/docs/hub/spaces-sdks-docker

FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pydantic \
    requests \
    huggingface_hub

# Copy app
COPY app.py .

# Expose port
EXPOSE 7860

# Run app
CMD ["python", "app.py"]