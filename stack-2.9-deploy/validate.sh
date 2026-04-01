#!/bin/bash
#
# Stack 2.9 Deployment Validation Script
# Verifies that all required files are present and properly configured
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "Validating Stack 2.9 deployment files..."
echo ""

# Check required files
echo "Checking core files..."
REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yaml"
    "deploy.sh"
    "app.py"
    "config.yaml"
    "runpod-template.json"
    "vastai-template.json"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        ((ERRORS++))
    fi
done

echo ""
echo "Checking Kubernetes manifests..."
K8S_FILES=(
    "kubernetes/deployment.yaml"
    "kubernetes/service.yaml"
    "kubernetes/pvc.yaml"
    "kubernetes/hpa.yaml"
    "kubernetes/secrets.yaml"
)

for file in "${K8S_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${YELLOW}⚠${NC} $file (missing)"
        ((WARNINGS++))
    fi
done

echo ""
echo "Checking permissions..."
if [ -x "$SCRIPT_DIR/deploy.sh" ]; then
    echo -e "  ${GREEN}✓${NC} deploy.sh is executable"
else
    echo -e "  ${YELLOW}⚠${NC} deploy.sh is not executable (run: chmod +x deploy.sh)"
    ((WARNINGS++))
fi

echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker ($(docker --version | head -n1))"
else
    echo -e "  ${YELLOW}⚠${NC} Docker not found (required for local deployment)"
    ((WARNINGS++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker Compose ($(docker-compose --version | head -n1))"
else
    echo -e "  ${YELLOW}⚠${NC} Docker Compose not found (required for local deployment)"
    ((WARNINGS++))
fi

echo ""
echo "Checking NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader | head -1
else
    echo -e "  ${YELLOW}⚠${NC} No NVIDIA GPU detected (CPU-only mode will be slower)"
    ((WARNINGS++))
fi

echo ""
echo "Checking Kubernetes..."
if command -v kubectl &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} kubectl available"
    if kubectl cluster-info &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Connected to cluster"
    else
        echo -e "  ${YELLOW}⚠${NC} kubectl not configured"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} kubectl not found (required for K8s deployment)"
fi

echo ""
echo "════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo "You can deploy with: ./deploy.sh local"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}Validation complete with $WARNINGS warning(s)${NC}"
    echo "Fix warnings before deployment, or proceed with caution."
    exit 0
else
    echo -e "${RED}Validation failed with $ERRORS error(s)${NC}"
    exit 1
fi
