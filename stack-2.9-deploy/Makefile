.PHONY: help build test push deploy-local clean k8s-install k8s-uninstall

# Default target
help:
	@echo "Stack 2.9 Deployment Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build            Build Docker image"
	@echo "  test             Test local deployment"
	@echo "  push             Push image to registry (set REGISTRY)"
	@echo "  deploy-local     Deploy with docker-compose"
	@echo "  clean            Clean up containers and images"
	@echo "  k8s-install      Install to Kubernetes"
	@echo "  k8s-uninstall    Remove from Kubernetes"
	@echo "  k8s-logs         Show Kubernetes pod logs"
	@echo "  k8s-status       Show Kubernetes resources status"

# Build Docker image
build:
	docker build \
		--build-arg PYTHON_VERSION=3.10 \
		--build-arg VLLM_VERSION=0.6.3 \
		--build-arg CUDA_VERSION=12.1.0 \
		-t stack-2.9:latest .

# Test with docker-compose
test:
	docker-compose up -d
	@echo "Waiting for health check..."
	@sleep 60
	@curl -f http://localhost:8000/health && echo "✓ Server healthy" || echo "✗ Health check failed"
	docker-compose logs stack-2.9

# Push to registry
push:
ifndef REGISTRY
	$(error REGISTRY is not set. Usage: make push REGISTRY=your-registry)
endif
	docker tag stack-2.9:latest $(REGISTRY)/stack-2.9:latest
	docker tag stack-2.9:latest $(REGISTRY)/stack-2.9:2.9.0
	docker push $(REGISTRY)/stack-2.9:latest
	docker push $(REGISTRY)/stack-2.9:2.9.0

# Deploy locally
deploy-local: build
	@echo "Modifying docker-compose.yaml for local deployment..."
	@docker-compose up -d
	@echo ""
	@echo "✓ Stack 2.9 is starting..."
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo ""
	@echo "View logs: docker-compose logs -f"
	@echo "Stop: docker-compose down"

# Clean up
clean:
	docker-compose down -v
	docker rmi stack-2.9:latest 2>/dev/null || true
	docker system prune -f --volumes

# Kubernetes - Install
k8s-install:
	@echo "Creating namespace..."
	-kubectl create namespace stack-2-9
	@echo "Creating secrets..."
	@if [ -f secrets.yaml ]; then \
		kubectl apply -f secrets.yaml; \
	else \
		echo "Warning: secrets.yaml not found. Create it with your Hugging Face token."; \
	fi
	@echo "Applying manifests..."
	kubectl apply -f kubernetes/
	@echo "Waiting for deployment..."
	@sleep 10
	kubectl wait --for=condition=available --timeout=300s deployment/stack-2.9 -n stack-2-9
	@echo ""
	@echo "✓ Stack 2.9 deployed to Kubernetes"
	@echo "Status: kubectl get all -n stack-2-9"

# Kubernetes - Uninstall
k8s-uninstall:
	-kubectl delete -f kubernetes/
	-kubectl delete namespace stack-2-9
	@echo "✓ Stack 2.9 removed from Kubernetes"

# Kubernetes - Status
k8s-status:
	kubectl get all,pvc,hpa -n stack-2-9

# Kubernetes - Logs
k8s-logs:
	kubectl logs -f deployment/stack-2.9 -n stack-2-9

# Quick start
quick-start: build deploy-local
	@./deploy.sh local
