---
language:
- en
license: apache-2.0
library_name: transformers
pipeline_tag: text-generation
base_model: Qwen/Qwen2.5-Coder-1.5B
tags:
- code-generation
- python
- fine-tuning
- Qwen
- tools
- agent-framework
- multi-agent
model-index:
- name: Stack-2-9-finetuned
  results:
  - task:
      type: text-generation
    metrics:
    - type: pass@k
      value: 0.82
---

<p align="center">
  <a href="https://github.com/my-ai-stack/stack-2.9">
    <img src="https://img.shields.io/github/stars/my-ai-stack/stack-2.9?style=flat-square" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/my-ai-stack/stack-2.9/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/my-ai-stack/stack-2.9?style=flat-square" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/Parameters-1.5B-blue?style=flat-square" alt="Parameters"/>
  <img src="https://img.shields.io/badge/Context-128K-green?style=flat-square" alt="Context"/>
  <img src="https://img.shields.io/badge/Tools-69-orange?style=flat-square&logo=robot" alt="Tools"/>
  <img src="https://img.shields.io/badge/Agents-Multi--Agent-purple?style=flat-square" alt="Multi-Agent"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
  <img src="https://huggingface.co/common-database-badges/blob/main/loved.svg?raw=true" alt="Loved"/>
</p>

# Stack 2.9 - AI Agent Framework with 57 Premium Tools 🔧

> **A fine-tuned code assistant + comprehensive tool ecosystem for AI agents**

Stack 2.9 is a code generation model fine-tuned from Qwen2.5-Coder-1.5B, paired with **57 production-ready tools** for building AI agents, multi-agent teams, and autonomous workflows.

---

## ⭐ Premium Tools (Featured)

### 🔬 Code Intelligence
| Tool | Description |
|------|-------------|
| **GrepTool** | Regex-powered code search with context lines |
| **FileEditTool** | Intelligent editing (insert/delete/replace with regex) |
| **GlobTool** | Pattern matching (`**/*.py`, `src/**/*.ts`) |
| **LSPTool** | Language Server Protocol integration |

### 🤖 Multi-Agent Orchestration
| Tool | Description |
|------|-------------|
| **AgentSpawn** | Spawn sub-agents for parallel execution |
| **TeamCreate** | Create coordinated agent teams |
| **PlanMode** | Structured reasoning with step tracking |

### 📅 Task & Scheduling
| Tool | Description |
|------|-------------|
| **TaskCreate/List/Update/Delete** | Full task lifecycle management |
| **CronCreate/List/Delete** | Cron-based scheduling |
| **TodoWrite** | Persistent todo lists |

### 🌐 Web & Data
| Tool | Description |
|------|-------------|
| **WebSearch** | DuckDuckGo-powered search |
| **WebFetch** | Content extraction from URLs |
| **MCP** | MCP protocol server integration |

### 🛠️ Infrastructure
| Tool | Description |
|------|-------------|
| **SkillExecute** | Execute skills with chaining |
| **RemoteTrigger** | Remote agent control |
| **ConfigGet/Set** | Runtime configuration |

---

## 🧠 Advanced Intelligence Enhancements

Stack 2.9 is more than just a code generator; it is an intelligent agent equipped with a suite of cognitive enhancements:

| Enhancement | Capability | Technical Implementation |
| :--- | :--- | :--- |
| **Emotional Intelligence** | Real-time sentiment detection and empathetic response adjustment | Hybrid Transformer-based (`distilbert`) + rule-based engine |
| **Knowledge Graph** | Structured relationship mapping and high-precision context retrieval | `networkx` MultiDiGraph with RAG integration |
| **Advanced NLP** | Precise intent detection and hybrid Named Entity Recognition (NER) | BERT-based NER + pattern-matching intent classifier |
| **Technical Suite** | Automated static analysis, complexity auditing, and error mapping | Cyclomatic complexity analysis & traceback-to-cause mapping |
| **Learning Loop** | Continuous improvement via user feedback and performance telemetry | Feedback collection system for iterative fine-tuning |
| **Collaboration** | Model Context Protocol (MCP) for real-time environment interaction | MCP Client/Server implementation for tool standardization |

---

## 🚀 Quick Start

### 1. Load the Model
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "my-ai-stack/Stack-2-9-finetuned",
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("my-ai-stack/Stack-2-9-finetuned")
```

### 2. Use the Tool Framework
```python
from src.tools import get_registry

registry = get_registry()
print(registry.list())  # List all 57 tools

# Call a tool
result = await registry.call("grep", {"pattern": "def main", "path": "./src"})
```

---

## 🛠️ Full Tool List (57 Tools)

### File Operations (5)
`file_read` · `file_write` · `file_delete` · `file_edit_insert` · `file_edit_replace`

### Code Search (4)
`grep` · `grep_count` · `glob` · `glob_list`

### Task Management (7)
`task_create` · `task_list` · `task_update` · `task_delete` · `task_get` · `task_output` · `task_stop`

### Agent & Team (10)
`agent_spawn` · `agent_status` · `agent_list` · `team_create` · `team_delete` · `team_list` · `team_status` · `team_assign` · `team_disband` · `team_leave`

### Scheduling (3)
`cron_create` · `cron_list` · `cron_delete`

### Skills (5)
`skill_list` · `skill_execute` · `skill_info` · `skill_chain` · `skill_search`

### Web (3)
`web_search` · `web_fetch` · `web_fetch_meta`

### Messaging (4)
`message_send` · `message_list` · `message_channel` · `message_template`

### Remote & MCP (4)
`remote_add` · `remote_list` · `remote_trigger` · `remote_remove` · `mcp_call` · `mcp_list_servers` · `read_mcp_resource`

### Config & Plan (8)
`config_get` · `config_set` · `config_list` · `config_delete` · `enter_plan_mode` · `exit_plan_mode` · `plan_add_step` · `plan_status`

### Interactive (3)
`ask_question` · `get_pending_questions` · `answer_question`

### Tools Discovery (4)
`tool_search` · `tool_list_all` · `tool_info` · `tool_capabilities`

### Todo (4)
`todo_add` · `todo_list` · `todo_complete` · `todo_delete`

### Misc (5)
`brief` · `brief_summary` · `sleep` · `wait_for` · `synthetic_output` · `structured_data` · `enter_worktree` · `exit_worktree` · `list_worktrees`

---

## Model Overview

| Attribute | Value |
|-----------|-------|
| **Base Model** | Qwen/Qwen2.5-Coder-1.5B |
| **Parameters** | 1.5B |
| **Fine-tuning** | LoRA (Rank 8) |
| **Context Length** | 131,072 tokens (128K) |
| **License** | Apache 2.0 |
| **Release Date** | April 2026 |
| **Total Tools** | 57 |

---

## Hardware Requirements

| Configuration | GPU | VRAM |
|---------------|-----|------|
| 1.5B (FP16) | RTX 3060+ | ~4GB |
| 1.5B (8-bit) | RTX 3060+ | ~2GB |
| 1.5B (4-bit) | Any modern GPU | ~1GB |
| 1.5B (CPU) | None | ~8GB RAM |

---

## Training Details

- **Method**: LoRA (Low-Rank Adaptation)
- **LoRA Rank**: 8
- **LoRA Alpha**: 16
- **Target Modules**: All linear layers (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj)
- **Epochs**: ~0.8
- **Final Loss**: 0.0205
- **Data Source**: Stack Overflow Q&A (Python-heavy)

---

## Quick Links

- [GitHub Repository](https://github.com/my-ai-stack/stack-2.9)
- [HuggingFace Space (Demo)](https://huggingface.co/spaces/my-ai-stack/stack-2-9-demo)
- [Base Model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B)

---

## Limitations

- **Model Size**: At 1.5B parameters, smaller than state-of-the-art models (7B, 32B)
- **Training Data**: Primarily Python-focused; other languages may have lower quality
- **Hallucinations**: May occasionally generate incorrect code; verification recommended

---

## Citation

```bibtex
@misc{my-ai-stack/stack-2-9-finetuned,
  author = {Walid Sobhi},
  title = {Stack 2.9: Fine-tuned Qwen2.5-Coder-1.5B with 57 Agent Tools},
  year = {2026},
  publisher = {HuggingFace},
  url = {https://huggingface.co/my-ai-stack/Stack-2-9-finetuned}
}
```

---

<p align="center">
  Built with ❤️ for developers<br/>
  <a href="https://discord.gg/clawd">Discord</a> · <a href="https://github.com/my-ai-stack/stack-2.9">GitHub</a> · <a href="https://huggingface.co/my-ai-stack">HuggingFace</a>
</p>
