# Stack 2.9 Deployment Infrastructure

Turnkey deployment configurations for Stack 2.9 LLM inference server.

## 📋 Prerequisites

- **Linux/macOS** shell environment
- For local deployment: **Docker** + **NVIDIA GPU** (optional but recommended)
- For cloud: **runpodctl** or **vastai** CLI installed
- **chmod +x** may be required on shell scripts

## 🖥️ System Requirements

Stack 2.9 deployment requires appropriate hardware depending on model size:

| Configuration | Minimum | Recommended | Production |
|---------------|---------|-------------|------------|
| **GPU VRAM** | 8GB | 24GB | 40-80GB (A100/H100) |
| **RAM** | 16GB | 32GB | 64GB+ |
| **Disk** | 20GB free | 50GB free | 100GB+ (NVMe) |
| **CUDA** | 11.8 | 12.1 | 12.1+ |
| **Models** | 7B quantized | 32B quantized | 70B+ quantized |

**Notes:**
- CPU-only mode is possible but extremely slow (not recommended for production)
- AWQ/GPTQ quantization reduces VRAM requirements by ~50%
- Multi-GPU (tensor parallelism) supported via `TENSOR_PARALLEL_SIZE`

## 🧪 Validate Setup

## 🧪 Validate Setup

Before deploying, run the validation script to ensure everything is ready:

```bash
./validate.sh
```
This checks Docker, GPU, and all required files.

## 🚀 Quick Start

### Local Deployment (Docker Compose)

```bash
# Ensure deploy.sh is executable
chmod +x deploy.sh validate.sh

# Deploy
./deploy.sh local --model TheBloke/Llama-2-7B-Chat-AWQ
```

The server will start at `http://localhost:8000`

### Cloud Deployments

```bash
# RunPod
./deploy.sh runpod --gpu A100-40GB

# Vast.ai
./deploy.sh vastai

# Kubernetes
./deploy.sh kubernetes --namespace inference
```

---

## 📦 What's Included

```
stack-2.9-deploy/
├── Dockerfile                 # Multi-stage production image
├── docker-compose.yaml        # Local orchestration
├── deploy.sh                  # One-command deployment script
├── runpod-template.json       # RunPod.io template
├── vastai-template.json       # Vast.ai template
├── kubernetes/               # K8s manifests
│   ├── deployment.yaml       # GPU-enabled deployment
│   ├── service.yaml          # LoadBalancer service
│   ├── pvc.yaml              # Model cache volume
│   ├── hpa.yaml              # Autoscaling configuration
│   └── secrets.yaml          # Secrets template
├── app.py                     # vLLM server wrapper
└── README.md                  # This file
```

---

## 🐳 Docker Image

**Base:** `nvidia/cuda:12.1-runtime-ubuntu22.04`
**Python:** 3.10
**vLLM:** 0.6.3
**CUDA:** 12.1

### Features:
- Multi-stage build for minimal footprint
- Non-root user (`vllm`)
- Health checks
- CUDA 12.1 runtime
- Model cache persistence
- AWQ 4-bit quantization support

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_ID` | `TheBloke/Llama-2-7B-Chat-AWQ` | Hugging Face model ID |
| `HUGGING_FACE_TOKEN` | (empty) | HF token for gated models |
| `QUANTIZATION` | `awq` | Quantization method |
| `TENSOR_PARALLEL_SIZE` | `1` | Number of GPUs |
| `GPU_MEMORY_UTILIZATION` | `0.9` | GPU memory fraction |
| `MAX_MODEL_LEN` | `4096` | Max sequence length |
| `MAX_NUM_SEQS` | `64` | Max batch size |
| `PORT` | `8000` | Server port |

---

## 🌐 API Endpoints

Stack 2.9 provides OpenAI-compatible endpoints:

- `POST /v1/completions` - Text completion
- `POST /v1/chat/completions` - Chat completion
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API docs

### Example Usage

```bash
# Chat completion
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "stack-2.9",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

---

## ☁️ Platform-Specific Notes

### Local (Docker Compose)

```bash
# Build and start
./deploy.sh local --model <model-id>

# View logs
docker-compose logs -f stack-2.9

# Stop
docker-compose down
```

**Requirements:**
- Docker 20.10+
- Docker Compose v2
- NVIDIA GPU (recommended) with CUDA 12.x drivers

---

### RunPod

1. Authenticate: `runpodctl login`
2. Run: `./deploy.sh runpod --gpu A100-40GB`
3. Provide your Docker registry
4. Deploy from the created template on RunPod.io

**Recommended GPUs:**
- A100 40GB (default)
- A100 80GB
- H100 80GB

**Auto-sleep:** Enabled after 30 minutes of inactivity

---

### Vast.ai

1. Install vastai CLI
2. Run: `./deploy.sh vastai`
3. Provide your Docker registry
4. Launch via template or CLI

**Recommended Instances:**
- RTX 4090 (24GB) - $0.30-0.50/hr
- RTX 6000 Ada (48GB) - $0.80-1.20/hr
- A100 40GB - $0.90-1.50/hr

**SSH Access:** Available on forwarded port 2222

---

### Kubernetes

#### Prerequisites:
- kubectl configured
- GPU-enabled cluster (NVIDIA GPUs with device plugin)
- Storage class with ReadWriteMany capability

#### Deployment:

```bash
# Create namespace
kubectl apply -f kubernetes/secrets.yaml

# Set your HF token
kubectl create secret generic stack-2.9-secrets \
  --from-literal=huggingface-token='YOUR_TOKEN' \
  -n stack-2.9

# Deploy
./deploy.sh kubernetes --namespace stack-2.9

# Or manually:
kubectl apply -f kubernetes/
```

**Check status:**
```bash
kubectl get pods,svc,pvc,hpa -n stack-2.9
kubectl logs -f deployment/stack-2.9 -n stack-2-9
```

**Get service URL:**
```bash
kubectl get svc stack-2.9 -n stack-2-9 -o wide
```

---

## ⚙️ Customization

### Different Model

```bash
./deploy.sh local --model mistralai/Mistral-7B-Instruct-v0.2
```

Supported formats:
- AWQ quantized: `TheBloke/*-AWQ`
- GPTQ quantized: `TheBloke/*-GPTQ`
- Full precision: Any Hugging Face model

### GPU Configuration

Edit `docker-compose.yaml` or K8s deployment:

```yaml
resources:
  limits:
    nvidia.com/gpu: 2  # Multi-GPU
  requests:
    memory: "24Gi"
    cpu: "8"
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Test inference
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Once upon a time", "max_tokens": 50}'
```

---

## 🐛 Troubleshooting

### GPU not detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Ensure NVIDIA Container Toolkit
docker info | grep -i runtime
```

### Out of memory
Reduce `GPU_MEMORY_UTILIZATION` to `0.7` or `0.8`

### Slow first request
First request downloads/loads the model (~5-10 min for 7B). This is cached for subsequent requests.

### Model download failures
Ensure `HUGGING_FACE_TOKEN` is set for gated models or large files.

---

## 📊 Monitoring

### Metrics Endpoint
`GET /metrics` - Basic server metrics

### Docker Metrics
```bash
docker stats stack-2.9-server
```

### Kubernetes Metrics
```bash
kubectl top pod stack-2.9 -n stack-2-9
kubectl get hpa -n stack-2-9
```

---

## 🔒 Security

- Runs as non-root user (`vllm`)
- Dropped capabilities
- Read-only filesystem (except cache)
- Health checks for liveness/readiness
- Secrets via Kubernetes secrets or env file

---

## 📝 License

Same as Stack 2.9 project license.

---

## 🤝 Support

Issues: Report to Stack 2.9 repository

---

**Made with ❤️ for turnkey LLM deployment**
