# Stack 2.9 Directory Structure

## Quick Overview

```
stack-2.9/
├── src/           # Core source code (voice, LLM, MCP, indexing)
├── stack/         # Components (deploy, training, eval, voice, docs)
├── data/          # Training datasets
├── scripts/       # Utility scripts
├── samples/       # Examples & tests
├── docs/          # Documentation
│
├── README.md      # Main docs
├── LICENSE        # Apache 2.0
├── package.json   # npm config
├── pyproject.toml # Python config
└── .env.example   # Environment template
```

## Structure Details

### Root Files (User-Facing)
| File | Purpose |
|------|---------|
| README.md | Main documentation |
| LICENSE | Apache 2.0 license |
| CHANGELOG.md | Version history |
| CONTRIBUTING.md | Contribution guide |
| SECURITY.md | Security policy |
| .env.example | Environment variables |
| package.json | npm dependencies |
| pyproject.toml | Python project |
| requirements.txt | Python deps |
| Dockerfile | Container config |
| Makefile | Build targets |
| colab_train_stack29.ipynb | Colab training |

### Core Modules (`src/`)
- **src/voice/** - Voice integration (recording, synthesis, cloning)
- **src/llm/** - Multi-provider LLM client
- **src/mcp/** - Model Context Protocol client
- **src/indexing/** - Code indexing (RAG)
- **src/cli/** - CLI tools
- **src/utils/** - Utilities

### Components (`stack/`)
- **stack/deploy/** - Docker & deployment configs
- **stack/training/** - Model fine-tuning code
- **stack/eval/** - Evaluation & benchmarks
- **stack/voice/** - Python voice API server
- **stack/docs/** - API documentation
- **stack/internal/** - Internal docs (archive)

### Data & Scripts
- **data/** - Training datasets
- **scripts/** - Build & utility scripts
- **samples/** - Examples & test files