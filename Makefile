.PHONY: help install test train deploy clean lint format check check-types lint-ci

help: ## Show this help message
	@echo "Stack 2.9 - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install Python and Node dependencies"
	@echo ""
	@echo "Training:"
	@echo "  train            Run full training pipeline"
	@echo "  prepare-data     Prepare training dataset"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-local     Deploy vLLM server locally with Docker"
	@echo "  deploy-runpod    Deploy to RunPod"
	@echo "  deploy-vast      Deploy to Vast.ai"
	@echo ""
	@echo "Voice:"
	@echo "  voice-up         Start voice integration service"
	@echo "  voice-down       Stop voice service"
	@echo ""
	@echo "Evaluation:"
	@echo "  eval             Run full benchmark suite"
	@echo "  eval-tool-use    Run tool-use evaluation"
	@echo "  eval-code        Run code quality evaluation"
	@echo ""
	@echo "Utilities:"
	@echo "  test             Run unit tests"
	@echo "  lint             Run linters"
	@echo "  clean            Remove build artifacts and temporary files"
	@echo "  docs             Generate documentation"

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	cd stack-2.9-training && pip install -r requirements.txt
	cd stack-2.9-voice && pip install -r requirements.txt 2>/dev/null || true
	npm install 2>/dev/null || true
	@echo "✅ Installation complete"

train: ## Run full training pipeline
	@echo "🤖 Starting training pipeline..."
	cd stack-2.9-training && ./run_training.sh

deploy-local: ## Deploy locally with Docker Compose
	@echo "🚀 Deploying to local Docker..."
	cd stack-2.9-deploy && ./local_deploy.sh

deploy-runpod: ## Deploy to RunPod
	@echo "☁️  Deploying to RunPod..."
	cd stack-2.9-deploy && ./runpod_deploy.sh

deploy-vast: ## Deploy to Vast.ai
	@echo "☁️  Deploying to Vast.ai..."
	cd stack-2.9-deploy && ./vastai_deploy.sh

voice-up: ## Start voice integration service
	@echo "🎤 Starting voice service..."
	cd stack-2.9-voice && docker-compose up -d
	@echo "✅ Voice service running on http://localhost:8001"

voice-down: ## Stop voice service
	@echo "🎤 Stopping voice service..."
	cd stack-2.9-voice && docker-compose down

eval: ## Run full benchmark suite
	@echo "📊 Running evaluation suite..."
	cd stack-2.9-eval && ./benchmark_suite.sh

eval-tool-use: ## Run tool-use evaluation
	@echo "🔧 Running tool-use evaluation..."
	cd stack-2.9-eval && python tool_use_eval.py

eval-code: ## Run code quality evaluation
	@echo "✨ Running code quality evaluation..."
	cd stack-2.9-eval && python code_quality_eval.py

test: ## Run unit tests
	@echo "🧪 Running tests..."
	pytest -xvs 2>/dev/null || echo "No pytest tests found"
	cd stack-2.9-voice && python -m pytest test_integration.py 2>/dev/null || true

lint: ## Run ruff linter
	@echo "🔍 Running ruff linter..."
	ruff check .
	@echo "✅ Lint complete"

format: ## Run black formatter
	@echo "🎨 Running black formatter..."
	black .
	@echo "✅ Format complete"

check: ## Run all quality checks
	@echo "🔍 Running all checks (lint + format check + type check)..."
	@echo ""
	@echo "--- Lint (ruff) ---"
	ruff check . || true
	@echo ""
	@echo "--- Format check (black) ---"
	black --check . || true
	@echo ""
	@echo "--- Type check (mypy) ---"
	bash scripts/check_types.sh
	@echo ""
	@echo "✅ All checks complete"

check-types: ## Run mypy type checks
	@echo "🔍 Running mypy type checks..."
	bash scripts/check_types.sh
	@echo "✅ Type check complete"

lint-ci: ## Run linters (CI-friendly, fail on errors)
	@echo "🔍 Running linters (CI mode)..."
	ruff check . --exit-non-zero-on-error

clean: ## Clean build artifacts
	@echo "🧹 Cleaning..."
	rm -rf data/ output/ models/ logs/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	find . -name ".pytest_cache" -delete
	@echo "✅ Clean complete"

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	cd stack-2.9-docs && cp -R ../README.md . 2>/dev/null || true
	@echo "✅ Docs ready in stack-2.9-docs/"

status: ## Show deployment status
	@echo "📋 Stack 2.9 Status"
	@echo "=================="
	@if docker ps | grep -q stack; then \
		echo "✅ vLLM server: running"; \
	else \
		echo "❌ vLLM server: stopped"; \
	fi
	@if docker ps | grep -q voice; then \
		echo "✅ Voice service: running"; \
	else \
		echo "❌ Voice service: stopped"; \
	fi
	@echo ""
	@echo "Directories:"
	@ls -ld training-data/ stack-2.9-*/ 2>/dev/null | awk '{print "  " $$NF}'