# Deployment Troubleshooting Guide

## Quick Diagnostic

Run the health check first:
```bash
curl http://localhost:8000/health
```

Or use Python:
```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

Check logs:
```bash
docker-compose logs -f vllm
# or
tail -f logs/vllm.log
```

---

## Common Issues and Solutions

### 1. Docker/Compose Issues

#### Problem: `docker: command not found`
**Error:** Docker is not installed or not in PATH.

**Solution:**
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Install Docker Compose
sudo apt-get install docker-compose-plugin
# or download binary: https://github.com/docker/compose/releases
```

#### Problem: `Cannot connect to the Docker daemon`
**Error:** Permission denied or socket not found.

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify permissions
docker info
```

#### Problem: `nvidia: driver not installed` or GPU not detected
**Error:** Docker doesn't see NVIDIA GPU.

**Solution:**
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi
```

---

### 2. vLLM Service Issues

#### Problem: `GPU Out of Memory (OOM)`
**Error in logs:** `CUDA out of memory` or `CUDA error: out of memory`

**Solution:**

1. **Reduce model memory usage** via environment variables:
```bash
export GPU_MEMORY_UTILIZATION=0.7  # Lower from 0.9
export MAX_MODEL_LEN=8192         # Reduce from 131072
export BLOCK_SIZE=16              # Smaller blocks
```

2. **Use quantized model** (recommended):
   - Convert model to AWQ or GGUF format
   - Set `QUANTIZATION=awq` in environment

3. **Use smaller model**: Switch from Llama-3.1-8B to 7B or smaller

4. **Reduce batch size**:
```bash
export MAX_BATCH_SIZE=4
```

5. **Ensure no other processes** are using GPU:
```bash
nvidia-smi  # Check for other processes
```

#### Problem: `Model not found`
**Error:** Model fails to load, `FileNotFoundError`, or stays in loading state.

**Solution:**

1. **Check model path**:
```bash
# For local model:
ls -la models/
# Should contain config.json, pytorch_model.bin, etc.

# For HuggingFace model:
# Set MODEL_NAME to HF name, e.g., meta-llama/Llama-3.1-8B-Instruct
```

2. **Download model manually** if automatic download fails:
```bash
# Install huggingface-cli
pip install huggingface-hub

# Download (requires authentication for gated models)
huggingface-cli login  # if needed
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir models
```

3. **Check disk space**:
```bash
df -h
# Need ~16GB for 8B model (32GB for original, ~8GB for quantized)
```

4. **Use pre-downloaded model**:
   - Upload model to the `models/` directory before starting
   - Mount external volume with model

#### Problem: `Health check timeout` or `503 Service Unavailable`
**Cause:** Model still loading, or failed to start.

**Diagnosis:**
```bash
docker-compose logs vllm
# Look for "Model loaded successfully" or error messages
```

**Solution:**
- Wait longer (first load can take 5-15 minutes)
- Check logs for specific errors (OOM, missing files)
- Increase healthcheck start_period:
```yaml
healthcheck:
  start_period: 300s  # Increase from 120s
```

#### Problem: `CORS or network errors` when calling API
**Symptoms:** Connection refused, network timeout.

**Solution:**
```bash
# Check if container is running
docker-compose ps

# Check port mapping
docker-compose port vllm 8000

# Test from inside container
docker-compose exec vllm curl http://localhost:8000/health

# Check firewall
sudo ufw status
sudo ufw allow 8000
```

#### Problem: `Redis connection failed`
**Error:** `Could not connect to Redis`

**Solution:**
- Redis is optional (caching). vLLM will continue without it.
- If you want Redis:
```bash
docker-compose ps redis  # Check if running
docker-compose logs redis
```

---

### 3. Docker Compose Issues

#### Problem: `Port already in use`
**Error:** ` Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8000
# or
netstat -tulpn | grep :8000

# Kill process or change port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Map host 8001 to container 8000
```

#### Problem: `Volume mount permission denied`
**Error:** Cannot mount `./models:/models`

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p models logs
sudo chown -R $(id -u):$(id -g) models logs
# Or run Docker with volume flags to ignore permissions
```

#### Problem: `docker-compose: command not found`
**Solution:**
```bash
# Docker Compose v2 (included with Docker)
sudo apt-get install docker-compose-plugin

# Or Docker Compose v1 (standalone)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

### 4. Cloud Deployment Issues

#### RunPod Specific

**Problem: `runpodctl: command not found`**
```bash
# Install
curl -L https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64 -o runpodctl
sudo install runpodctl /usr/local/bin/
runpodctl config  # Set API key
```

**Problem: `Template not found` or `pod creation failed`**
- Ensure you have sufficient quota/balance
- Check GPU availability in your region
- Verify template name (case-sensitive)

**Problem: `SCP/SSH connection failed`**
- Pod may still be starting; wait 2-3 minutes
- Check pod status: `runpodctl get pod <id>`
- Verify pod is in `RUNNING` state

**Problem: `Insufficient disk space` on pod**
- Increase disk size in script (`DISK_SIZE=100` or higher)
- Upload model separately to `/workspace/models` before starting

#### Vast.ai Specific

**Problem: `vastai: command not found`**
```bash
pip install vastai
# or download from: https://vast.ai/docs/cli
```

**Problem: `No suitable instance found`**
- Relax search criteria (lower `VAST_GPU_RAM`)
- Increase `VAST_SEARCH_LIMIT`
- Check marketplace manually: `vastai search offers "cuda>=11.8"`

**Problem: `SSH connection refused`**
- Instance may still be provisioning
- Check `vastai show instance <id>`
- Ensure port forwarding is set up correctly

**Problem: `Instance died or unresponsive`**
- Check if balance depleted
- Instance may have been evicted (low priority)
- Use `--priority` flag or choose higher-cost instances

---

## Performance Tuning

### Reduce Latency
```bash
export MAX_BATCH_SIZE=4          # Smaller batches for lower latency
export MAX_MODEL_LEN=4096        # Shorter context window
export GPU_MEMORY_UTILIZATION=0.8
```

### Increase Throughput
```bash
export MAX_BATCH_SIZE=32        # Larger batches
export MAX_MODEL_LEN=16384      # Longer context capability
export GPU_MEMORY_UTILIZATION=0.95
```

### Multi-GPU Setup
```bash
# Automatically detected. Ensure tensor parallel size matches GPU count:
# export TENSOR_PARALLEL_SIZE=2  # For 2 GPUs (usually auto-detected)
```

---

## Monitoring

### Health Endpoint
```bash
curl http://localhost:8000/health | jq
# Returns: {"status":"healthy","model":{...},"timestamp":...}
```

### Readiness Endpoint (K8s liveness)
```bash
curl http://localhost:8000/ready
# Returns: {"status":"ready"}
```

### Prometheus Metrics
```bash
curl http://localhost:9090/metrics
# Look for: vllm_requests_total, vllm_request_latency_seconds
```

### Container Logs
```bash
# All logs
docker-compose logs -f vllm

# Last 100 lines
docker-compose logs --tail=100 vllm

# Search for errors
docker-compose logs vllm | grep -i error
```

---

## Model Compatibility

### Supported Formats
- **HuggingFace (default)**: `MODEL_FORMAT=hf`
- **Local directory**: Mount model folder to `/models`
- **AWQ quantized**: Set `QUANTIZATION=awq` and use AWQ model

### Gated Models (Llama 3.1, etc.)
1. Request access on HuggingFace
2. Get your token: https://huggingface.co/settings/tokens
3. Authenticate:
```bash
huggingface-cli login
# Paste token
```

### Unsupported Models
If vLLM doesn't support your model architecture:
- Use `trust_remote_code=True` (already set)
- Convert model to supported format
- Check vLLM supported models: https://docs.vllm.ai/

---

## Debug Mode

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
# restart services
docker-compose down && docker-compose up -d
```

---

## Getting Help

1. Check this guide for common symptoms
2. Review logs: `docker-compose logs vllm`
3. Search issues: https://github.com/vllm-project/vllm/issues
4. Community: https://discord.gg/vllm

---

## Quick Reference Commands

```bash
# Start deployment
cd stack-2.9-deploy
./local_deploy.sh

# Stop deployment
docker-compose down

# View logs
docker-compose logs -f vllm

# Restart single service
docker-compose restart vllm

# Check service status
docker-compose ps

# Access container shell
docker-compose exec vllm bash

# Clean everything (WARNING: deletes data!)
docker-compose down -v
rm -rf models logs

# Rebuild image (after Dockerfile changes)
docker-compose build --no-cache vllm
docker-compose up -d
```
