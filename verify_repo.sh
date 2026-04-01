#!/usr/bin/env bash
# Stack 2.9 - Repository Integrity Check
# Verifies all components are present before pushing to GitHub

set -e

echo "🔍 Stack 2.9 Repository Check"
echo "============================"
echo ""

ERRORS=0
WARNINGS=0

check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $2"
    else
        echo "❌ Missing: $2 ($1)"
        ((ERRORS++))
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo "✅ $2"
    else
        echo "❌ Missing: $2 ($1)"
        ((ERRORS++))
    fi
}

check_file_optional() {
    if [ -f "$1" ]; then
        echo "✅ $2"
    else
        echo "⚠️  Optional: $2 ($1)"
        ((WARNINGS++))
    fi
}

echo "Checking top-level files..."
check_file "README.md" "Main README"
check_file "LICENSE" "Apache 2.0 License"
check_file "CONTRIBUTING.md" "Contributing Guide"
check_file "CODE_OF_CONDUCT.md" "Code of Conduct"
check_file "Makefile" "Makefile"
check_file "requirements.txt" "Python requirements"
check_file "pyproject.toml" "Python package config"
check_file ".gitignore" "Git ignore rules"
check_file ".env.example" "Environment example"
check_file "setup.sh" "Setup script"
check_file "PUSH_GUIDE.md" "Push guide"

echo ""
echo "Checking component directories..."
check_dir "training-data" "Training data"
check_dir "stack-2.9-training" "Training pipeline"
check_dir "stack-2.9-deploy" "Deployment configs"
check_dir "stack-2.9-voice" "Voice integration"
check_dir "stack-2.9-docs" "Documentation"
check_dir "stack-2.9-eval" "Evaluation tools"
check_dir ".github/workflows" "CI/CD workflows"

echo ""
echo "Checking critical training data files..."
check_file "training-data/tools/catalog.json" "Tool schemas"
check_file "training-data/synthetic/examples.jsonl" "Synthetic examples"
check_file "training-data/manifest.json" "Dataset manifest"
check_file_optional "training-data/code-pairs/pairs.json" "Code-comment pairs"
check_file_optional "training-data/advanced-patterns/examples.jsonl" "Advanced patterns"

echo ""
echo "Checking training pipeline files..."
check_file "stack-2.9-training/requirements.txt" "Training requirements"
check_file "stack-2.9-training/prepare_dataset.py" "Dataset preparation"
check_file "stack-2.9-training/train_lora.py" "LoRA training script"
check_file "stack-2.9-training/merge_lora.py" "Merge script"
check_file "stack-2.9-training/quantize_awq.py" "AWQ quantization"
check_file "stack-2.9-training/run_training.sh" "Training runner"

echo ""
echo "Checking deployment files..."
check_file "stack-2.9-deploy/vllm_server.py" "vLLM server"
check_file "stack-2.9-deploy/docker-compose.yml" "Docker Compose"
check_file "stack-2.9-deploy/Dockerfile" "Docker image"
check_file "stack-2.9-deploy/local_deploy.sh" "Local deployment script"
check_file_optional "stack-2.9-deploy/runpod_deploy.sh" "RunPod script"
check_file_optional "stack-2.9-deploy/vastai_deploy.sh" "Vast.ai script"

echo ""
echo "Checking voice integration..."
check_file "stack-2.9-voice/voice_server.py" "Voice API server"
check_file "stack-2.9-voice/voice_client.py" "Voice client"
check_file "stack-2.9-voice/stack_voice_integration.py" "Integration layer"
check_file "stack-2.9-voice/docker-compose.yml" "Voice Docker Compose"
check_file "stack-2.9-voice/README.md" "Voice docs"

echo ""
echo "Checking documentation..."
check_file "stack-2.9-docs/README.md" "Main docs"
check_file "stack-2.9-docs/API.md" "API reference"
check_file "stack-2.9-docs/OPENROUTER_SUBMISSION.md" "OpenRouter app"
check_file "stack-2.9-docs/TRAINING_DATA.md" "Training guide"
check_file_optional "stack-2.9-docs/VOICE_INTEGRATION.md" "Voice integration"
check_file_optional "stack-2.9-docs/BENCHMARKS.md" "Benchmarks"

echo ""
echo "Checking evaluation..."
check_file "stack-2.9-eval/eval_pipeline.py" "Evaluation pipeline"
check_file "stack-2.9-eval/tool_use_eval.py" "Tool use eval"
check_file "stack-2.9-eval/code_quality_eval.py" "Code quality eval"
check_file "stack-2.9-eval/conversation_eval.py" "Conversation eval"
check_file "stack-2.9-eval/results_aggregator.py" "Results aggregator"
check_dir "stack-2.9-eval/benchmarks" "Benchmark datasets"
check_dir "stack-2.9-eval/results" "Results directory"

echo ""
echo "============================"
echo "📊 Repository Check Summary"
echo "============================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical files present!"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠️  $WARNINGS optional files missing (not critical)"
    fi
    echo ""
    echo "Ready to push to GitHub!"
    echo ""
    echo "Next:"
    echo "  1. Create repo: https://github.com/organizations/my-ai-stack/repositories/new"
    echo "  2. Run: git init && git add . && git commit -m 'Initial commit'"
    echo "  3. Add remote: git remote add origin https://github.com/my-ai-stack/stack-2.9.git"
    echo "  4. Push: git push -u origin main"
    exit 0
else
    echo "❌ $ERRORS critical errors found!"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "Please fix missing files before pushing."
    exit 1
fi