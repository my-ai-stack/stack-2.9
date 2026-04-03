# Stack 2.9 Directory Structure

This document describes the organized structure of the Stack 2.9 project.

## Directory Overview

```
stack-2.9/
├── src/                    # TypeScript source code (voice, LLM, MCP, indexing modules)
├── docs/                   # Project documentation
├── training-data/           # Training datasets and manifests
├── scripts/                # Build and utility scripts
├── tests/                  # Test files
├── config/                 # Configuration files (package.json, tsconfig.json, etc.)
│
├── stack-2.9-training/     # Model training code
├── stack-2.9-deploy/        # Deployment configurations
├── stack-2.9-eval/          # Evaluation and benchmarking
├── stack-2.9-voice/        # Voice API server (Python)
├── stack-2.9-docs/         # Generated documentation
│
├── examples/               # Example usage files
├── benchmarks/             # Benchmark scripts
└── .github/                # GitHub Actions workflows
```

## Directory Details

### `src/` - TypeScript Source Code

Core modules for Stack 2.9 AI assistant:

- **src/voice/** - Voice integration (recording, synthesis, cloning)
- **src/llm/** - Multi-provider LLM client (OpenAI, Anthropic, Ollama)
- **src/mcp/** - Model Context Protocol client
- **src/indexing/** - Code indexing for semantic search (RAG)
- **src/tools/** - Tool implementations
- **src/agent/** - Agent logic
- **src/providers/** - Provider integrations

### `docs/` - Documentation

- ARCHITECTURE.md - System architecture
- SETUP.md - Setup instructions
- API.md - API documentation
- TOOLS.md - Tool reference
- BENCHMARKS.md - Performance benchmarks
- guides/ - Usage guides

### `training-data/` - Training Datasets

- training-data/tools/catalog.json - Tool schemas (46 tools)
- training-data/synthetic/ - Synthetic training examples
- training-data/code-pairs/ - Code-comment pairs
- training-data/src-derived/ - RTMP-extracted examples
- training-data/final/ - Final merged datasets

### `scripts/` - Utility Scripts

- scripts/extract_rtmp_tools.ts - Extract tool schemas from RTMP
- scripts/generate_from_rtmp.ts - Generate training data from RTMP
- scripts/combine_datasets.py - Merge training datasets
- scripts/download_public_datasets.py - Download public datasets

### `stack-2.9-*` - Component Directories

- **stack-2.9-training/** - Model fine-tuning code (LoRA, quantization)
- **stack-2.9-deploy/** - Docker and deployment configs
- **stack-2.9-eval/** - Human eval and benchmarks
- **stack-2.9-voice/** - Python FastAPI voice server
- **stack-2.9-docs/** - Auto-generated docs

## Configuration Files

| File | Purpose |
|------|---------|
| package.json | npm dependencies |
| tsconfig.json | TypeScript config |
| pyproject.toml | Python project config |
| requirements.txt | Python dependencies |
| .env.example | Environment variables template |
| Makefile | Build targets |

## Root Documentation Files

- README.md - Main project readme
- CHANGELOG.md - Version history
- CONTRIBUTING.md - Contribution guidelines
- LICENSE - Apache 2.0 license
- SECURITY.md - Security policy

## Deprecated/Merged Directories

The following directories are deprecated and their contents moved to other locations:

- `stack-2.9-cli/` → merged into `src/cli/`
- `stack_cli/` → merged into `src/cli/`
- `stack_2_9_training/` → merged into `stack-2.9-training/`
- `space/` → use `stack-2.9-deploy/`
- `self_evolution/` → use `stack-2.9-training/`
- `website/` → external repository
- `benchmarks/` → use `stack-2.9-eval/`

## Getting Started

1. **Install dependencies**: `npm install && pip install -r requirements.txt`
2. **Configure environment**: Copy `.env.example` to `.env`
3. **Run voice server**: `cd stack-2.9-voice && uvicorn voice_server:app`
4. **Use TypeScript modules**: Import from `src/`

## Adding New Modules

New TypeScript modules should follow this structure:

```
src/<module-name>/
├── index.ts           # Main exports
├── <ModuleName>.ts   # Main implementation
└── <ModuleName>Tool.ts  # Tool implementation (if applicable)
```