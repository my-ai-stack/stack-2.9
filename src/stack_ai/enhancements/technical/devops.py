"""
DevOps Tools Module

Provides cloud and DevOps operation capabilities.
"""

from typing import Dict, List, Optional, Any
import re


class DevOpsTools:
    """Cloud and DevOps operation tools."""

    # Cloud provider templates
    CLOUD_TEMPLATES = {
        "aws": {
            "ec2": {
                "description": "AWS EC2 instance",
                "template": """# AWS EC2 Instance
resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "Stack2.9-App"
  }
}"""
            },
            "s3": {
                "description": "AWS S3 bucket",
                "template": """# AWS S3 Bucket
resource "aws_s3_bucket" "data_store" {
  bucket = "stack29-data-store"

  tags = {
    Name        = "Stack2.9 Data"
    Environment = "production"
  }
}"""
            },
            "lambda": {
                "description": "AWS Lambda function",
                "template": """# AWS Lambda Function
resource "aws_lambda_function" "handler" {
  filename         = "handler.zip"
  function_name    = "stack29_handler"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  source_code_hash = filebase64sha256("handler.zip")

  runtime = "python3.9"
}"""
            },
        },
        "gcp": {
            "compute": {
                "description": "GCP Compute Engine",
                "template": """# GCP Compute Engine
resource "google_compute_instance" "vm_instance" {
  name         = "stack29-vm"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
  }
}"""
            },
            "storage": {
                "description": "GCP Cloud Storage",
                "template": """# GCP Cloud Storage
resource "google_storage_bucket" "bucket" {
  name          = "stack29-bucket"
  location      = "US"
  force_destroy = false

  labels = {
    environment = "production"
  }
}"""
            },
        },
        "docker": {
            "container": {
                "description": "Docker container configuration",
                "template": """# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["python", "main.py"]"""
            },
            "compose": {
                "description": "Docker Compose configuration",
                "template": """# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=app
      - POSTGRES_PASSWORD=secret

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
"""
            },
        },
        "kubernetes": {
            "deployment": {
                "description": "Kubernetes Deployment",
                "template": """# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stack29-app
  labels:
    app: stack29
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stack29
  template:
    metadata:
      labels:
        app: stack29
    spec:
      containers:
      - name: app
        image: stack29:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "500m"
            memory: "256Mi"
"""
            },
            "service": {
                "description": "Kubernetes Service",
                "template": """# k8s-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: stack29-service
spec:
  selector:
    app: stack29
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
"""
            },
        },
    }

    # CI/CD templates
    CICD_TEMPLATES = {
        "github_actions": {
            "description": "GitHub Actions workflow",
            "template": """# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest tests/

    - name: Lint
      run: |
        ruff check .
"""
        },
        "gitlab_ci": {
            "description": "GitLab CI pipeline",
            "template": """# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

build:
  stage: build
  script:
    - docker build -t stack29:$CI_COMMIT_SHA .
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:
  stage: deploy
  script:
    - kubectl apply -f k8s/
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
"""
        },
    }

    # Infrastructure as Code templates
    TERRAFORM_VARIABLES = {
        "description": "Terraform variables",
        "template": """# variables.tf
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
"""
    }

    def __init__(self):
        """Initialize DevOps tools."""
        pass

    def get_cloud_template(
        self,
        provider: str,
        service: str,
    ) -> Optional[str]:
        """Get a cloud infrastructure template."""
        return self.CLOUD_TEMPLATES.get(provider, {}).get(service, {}).get("template")

    def get_cicd_template(self, platform: str) -> Optional[str]:
        """Get a CI/CD pipeline template."""
        return self.CICD_TEMPLATES.get(platform, {}).get("template")

    def list_available_templates(self) -> Dict[str, List[str]]:
        """List all available templates."""
        return {
            "cloud_providers": list(self.CLOUD_TEMPLATES.keys()),
            "cicd": list(self.CICD_TEMPLATES.keys()),
        }

    def generate_kubernetes_manifest(
        self,
        app_name: str,
        image: str,
        replicas: int = 3,
        port: int = 8000,
    ) -> str:
        """Generate a Kubernetes deployment manifest."""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: {port}
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
---

apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
spec:
  selector:
    app: {app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: {port}
  type: LoadBalancer
"""

    def generate_dockerfile(
        self,
        language: str = "python",
        version: str = "3.11",
        port: int = 8000,
    ) -> str:
        """Generate a Dockerfile."""
        base_images = {
            "python": f"python:{version}-slim",
            "node": f"node:{version}-slim",
            "go": f"golang:{version}",
            "rust": f"rust:{version}-slim",
        }
        base = base_images.get(language, f"python:{version}-slim")

        return f"""FROM {base}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE {port}

# Run application
CMD ["python", "main.py"]
"""

    def parse_docker_compose(self, compose_content: str) -> Dict[str, Any]:
        """Parse docker-compose content to extract services."""
        services = re.findall(r'^  (\w+):$', compose_content, re.MULTILINE)
        return {"services": services, "count": len(services)}

    def __repr__(self) -> str:
        templates = self.list_available_templates()
        return f"DevOpsTools(cloud={templates['cloud_providers']}, cicd={templates['cicd']})"