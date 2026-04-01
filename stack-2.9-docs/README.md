# Stack 2.9 - Open-Source Voice-Enabled Coding Assistant

[![Apache 2.0 License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/openclaw/stack-2.9)](https://github.com/openclaw/stack-2.9/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/openclaw/stack-2.9)](https://github.com/openclaw/stack-2.9/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/openclaw/stack-2.9)](https://github.com/openclaw/stack-2.9/issues)

## Overview

Stack 2.9 is an open-source voice-enabled coding assistant built on the Qwen2.5-Coder-32B model, fine-tuned with OpenClaw tool patterns. It provides a powerful alternative to commercial coding assistants with the added capability of voice integration.

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- GPU with at least 24GB VRAM (recommended)
- OpenClaw runtime environment

### Installation

```bash
git clone https://github.com/openclaw/stack-2.9.git
cd stack-2.9
npm install
pip install -r requirements.txt
```

### Basic Usage

```bash
# Start the server
npm run start

# Access the API
curl http://localhost:3000/v1/chat/completions

# Voice integration (optional)
npm run voice
```

## Features

### Core Capabilities
- **Code Generation**: Write code in 50+ programming languages
- **Tool Integration**: Native OpenClaw tool patterns
- **Voice Commands**: Hands-free coding with voice cloning
- **API Compatibility**: OpenAI-compatible endpoints
- **Streaming Responses**: Real-time code suggestions

### Advanced Features
- **Context Awareness**: 32K token context window
- **Multi-file Editing**: Work across entire codebases
- **Error Detection**: Identify and fix bugs
- **Code Review**: Automated code quality analysis
- **Documentation Generation**: Auto-generate API docs

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Stack 2.9 Architecture                    │
├────────────────────────────────────────────────────────────────────┤
│  Client Apps ┌────────────────────────────────────────────────────────────────────┐  │
│            │   Web UI     │   CLI      │   Voice     │            │
│            └────────────────────────────────────────────────────────────────────┘  │
│                                                        │
│  API Gateway ┌────────────────────────────────────────────────────────────────────┐  │
│              │ OpenAI-compatible REST/Streaming │              │
│              └───────────────────────────────────────────────────────────────────┘  │
│                                                        │
│  Model Layer ┌────────────────────────────────────────────────────────────────────┐  │
│              │ Qwen2.5-Coder-32B (fine-tuned) │              │
│              └───────────────────────────────────────────────────────────────────┘  │
│                                                        │
│  Tool Engine ┌────────────────────────────────────────────────────────────────────┐  │
│              │ OpenClaw Tool Patterns │              │
│              └───────────────────────────────────────────────────────────────────┘  │
│                                                        │
│  Voice System ┌────────────────────────────────────────────────────────────────────┐  │
│              │ Voice Cloning Integration │              │
│              └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Comparison with Commercial Alternatives

| Feature | Stack 2.9 | Claude Code | GitHub Copilot | Tabnine |
|---------|-----------|-------------|----------------|---------|
| **Voice Integration** | ✅ Native | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ Apache 2.0 | ❌ Closed | ❌ Closed | ✅ LGPL |
| **Tool Patterns** | ✅ OpenClaw | ✅ Yes | ❌ No | ❌ No |
| **Context Window** | 32K tokens | 200K tokens | 32K tokens | 100K tokens |
| **Price** | Free | $20/month | $10/month | $12/month |
| **Self-Hosting** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Model Size** | 32B parameters | 200K+ parameters | 15B parameters | 100M parameters |

## Getting Help

- **Documentation**: [API.md](./API.md)
- **Voice Integration**: [VOICE_INTEGRATION.md](./VOICE_INTEGRATION.md)
- **Benchmarks**: [BENCHMARKS.md](./BENCHMARKS.md)
- **Contributing**: [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

Stack 2.9 is licensed under the [Apache 2.0 License](LICENSE). Open source and forever free.

---

**Stack 2.9** - Your voice-enabled coding companion. Built by the community, for the community.