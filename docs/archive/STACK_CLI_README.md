# Stack 2.9 CLI & Agent Interface

A powerful command-line interface and agent that showcases Stack 2.9 capabilities. Features interactive chat, command execution, voice input, and comprehensive tool support.

## Features

- **Interactive Chat Mode**: Conversational interface with the agent
- **Command Execution**: Run single commands and get results
- **Voice Input Support** (requires setup): Speech-to-text interaction
- **37 Built-in Tools**: File ops, git, code execution, web search, memory, planning
- **Context Awareness**: Project scanning and memory integration
- **Self-Reflection**: Agent evaluates and improves its own responses
- **Multi-mode Operation**: Chat, command-line, or voice interfaces

## Quick Start

### Installation

```bash
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9
pip install -e .
```

### Basic Usage

**Interactive Chat:**
```bash
stack
```

**Single Command:**
```bash
stack -c "read README.md"
```

**Execute Specific Tools:**
```bash
stack -t git_status project_scan
```

**Voice Mode (requires setup):**
```bash
stack -v
```

## Modes

### 1. Interactive Chat Mode
Start a conversation with the agent:
```bash
stack
```

Commands in chat mode:
- `/tools` - List tools used in current session
- `/schema` - Show tool schemas
- `/context` - Show current workspace context
- `/history` - Show conversation history
- `/clear` - Clear history
- `/voice` - Toggle voice input
- `/exit` - Exit

### 2. Command Mode
Execute a single query:
```bash
stack -c "list my tasks"
stack -c "search for *.py files"
stack -c "git status"
```

### 3. Tool Mode
Execute specific tools directly:
```bash
stack -t read project_scan memory_list
```

### 4. Voice Mode
Use voice input/output (requires `SpeechRecognition` and `pyttsx3`):
```bash
pip install SpeechRecognition pyttsx3 pyaudio
stack -v
```

## Tool Categories

### File Operations
- `read` - Read file contents
- `write` - Write to file
- `edit` - Edit file with text replacement
- `search` - Search for files
- `grep` - Search patterns in files
- `copy` - Copy files/directories
- `move` - Move/rename files
- `delete` - Delete files

### Git Operations
- `git_status` - Get git status
- `git_commit` - Create commit
- `git_push` - Push to remote
- `git_pull` - Pull from remote
- `git_branch` - Manage branches
- `git_log` - View commit history
- `git_diff` - Show changes

### Code Execution
- `run` - Run shell commands
- `test` - Run tests (pytest)
- `lint` - Lint code (ruff/pylint/mypy)
- `format` - Format code (ruff/black)
- `typecheck` - Type checking (mypy)
- `server` - Start development server
- `install` - Install dependencies

### Web Tools
- `web_search` - Search the web
- `fetch` - Fetch URL content
- `download` - Download files
- `check_url` - Check URL accessibility
- `screenshot` - Take webpage screenshot

### Memory & Context
- `memory_recall` - Search memory
- `memory_save` - Save to memory
- `memory_list` - List memory entries
- `context_load` - Load project context
- `project_scan` - Scan project structure

### Task Planning
- `create_task` - Create a task
- `list_tasks` - List tasks
- `update_task` - Update task status
- `delete_task` - Delete task
- `create_plan` - Create execution plan
- `execute_plan` - Execute plan

## Query Examples

**File operations:**
- "read main.py"
- "show me the contents of README.md"
- "create a file called notes.txt with 'Hello World'"

**Git operations:**
- "git status"
- "commit with message 'update'"
- "push to origin main"

**Code execution:**
- "run pytest"
- "lint the code"
- "format all files"

**Web search:**
- "search the web for Python async best practices"
- "look up how to use FastAPI"
- "fetch https://example.com"

**Memory:**
- "remember that the API key is in .env"
- "what do you remember about this project?"
- "list all memories"

**Tasks:**
- "create task: implement login"
- "list my tasks"
- "complete task abc123"

## Architecture

```
stack-2.9/
├── stack_cli/
│   ├── __init__.py      # Package init
│   ├── cli.py           # CLI entry point
│   ├── agent.py         # Core agent logic
│   ├── tools.py         # 37 built-in tools
│   └── context.py       # Context management
├── stack.py             # Main entry script
├── pyproject.toml       # Package config
└── requirements.txt     # Dependencies
```

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. (Optional) Install voice dependencies:
```bash
pip install SpeechRecognition pyttsx3 pyaudio
```

3. Run the CLI:
```bash
stack
```

## Customization

- Configure workspace context in `AGENTS.md`, `SOUL.md`, `TOOLS.md`
- Long-term memory stored in `MEMORY.md` and `memory/` folder
- Session files in `.tasks.json` and `.plans.json`

## License

MIT
