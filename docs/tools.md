# Stack 2.9 Tools Reference

Stack 2.9 provides **37 built-in tools** for file operations, system commands, git, web search, and more. Tools are selected automatically based on user intent, or can be called explicitly via the agent API.

## Tool Calling Format

Tools use a **function schema** format similar to OpenAI's function calling:

```python
{
    "name": "tool_name",
    "description": "What the tool does",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter description"},
            "param2": {"type": "integer", "description": "Another parameter"}
        },
        "required": ["param1"]
    }
}
```

The agent determines which tools to call and with what arguments based on the user query.

---

## Complete Tool List

### File Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `read` | Read file contents | `path` (string, required) |
| `write` | Write content to file | `path` (string, required), `content` (string, required) |
| `edit` | Edit file with sed-like replacements | `path` (string, required), `old_text` (string, required), `new_text` (string, required) |
| `create_directory` | Create a new directory | `path` (string, required) |
| `list_directory` | List contents of a directory | `path` (string, default: ".") |
| `search` | Search for files matching a pattern | `pattern` (string, required), `path` (string, default: ".") |
| `get_file_info` | Get file metadata (size, timestamps, permissions) | `path` (string, required) |
| `move_file` | Move or rename a file/directory | `source` (string, required), `destination` (string, required) |
| `copy_file` | Copy a file (implementation pending) | `source` (string, required), `destination` (string, required) |
| `delete_file` | Delete a file | `path` (string, required) |

### Git Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `git_status` | Get git repository status | (no parameters) |
| `git_log` | View commit history | `max_count` (integer, default: 10), `path` (string, optional) |
| `git_diff` | Show changes between commits or working tree | `commit` (string, optional), `path` (string, optional) |
| `git_commit` | Commit staged changes | `message` (string, required), `all` (boolean, default: false) |
| `git_add` | Stage files for commit | `paths` (array of strings, required) |
| `git_push` | Push commits to remote | `remote` (string, default: "origin"), `branch` (string, optional) |
| `git_pull` | Pull from remote | `remote` (string, default: "origin"), `branch` (string, optional) |
| `git_branch` | List or create branches | `create` (string, optional), `delete` (string, optional), `checkout` (string, optional) |
| `git_clone` | Clone a repository | `url` (string, required), `path` (string, optional) |
| `git_remote` | Manage remotes | `action` (string, required: "add|remove|list"), `name` (string), `url` (string) |

### Shell & Execution

| Tool | Description | Parameters |
|------|-------------|------------|
| `run` | Execute shell command | `command` (string, required), `timeout` (integer, default: 30), `cwd` (string, optional) |
| `run_background` | Run command in background | `command` (string, required), `yield_ms` (integer, default: 10000) |
| `test` | Run tests (pytest, unittest) | `path` (string, default: "."), `pattern` (string, default: "test_*.py") |
| `lint` | Lint code (flake8, pylint, eslint) | `path` (string, default: "."), `tool` (string, default: "auto") |
| `format` | Format code (black, prettier, gofmt) | `path` (string, default: "."), `tool` (string, default: "auto") |

### Web & Search

| Tool | Description | Parameters |
|------|-------------|------------|
| `web_search` | Search the web via Brave | `query` (string, required), `count` (integer, default: 10) |
| `fetch` | Fetch and extract content from URL | `url` (string, required), `max_chars` (integer, default: 5000) |
| `download` | Download a file | `url` (string, required), `output_path` (string, required) |

### Memory & Knowledge

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_recall` | Search memory for relevant entries | `query` (string, required), `limit` (integer, default: 10) |
| `memory_save` | Store observation in memory | `content` (string, required), `entity` (string, optional) |
| `memory_list` | List all memory entities | (no parameters) |
| `context_load` | Load conversation context | `session_id` (string, optional) |
| `context_save` | Save conversation context | `session_id` (string, optional) |

### Project Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_task` | Create a new task | `title` (string, required), `description` (string, optional), `priority` (string: low/medium/high) |
| `list_tasks` | List tasks | `status` (string: pending|done|all, default: "pending") |
| `update_task` | Update task status or details | `task_id` (string, required), `status` (string, optional), `title` (string, optional), `description` (string, optional) |
| `project_scan` | Scan project structure and dependencies | (no parameters) |

### System & Utilities

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_system_info` | Get OS, CPU, memory, disk info | (no parameters) |
| `list_processes` | List running processes | `filter` (string, optional) |
| `kill_process` | Terminate a process | `pid` (integer, required) |
| `environment` | Get environment variables | `names` (array of strings, optional) |
| `set_environment` | Set environment variable (current session) | `name` (string, required), `value` (string, required) |
| `whoami` | Get current user | (no parameters) |
| `pwd` | Print working directory | (no parameters) |

### Data & Serialization

| Tool | Description | Parameters |
|------|-------------|------------|
| `json_parse` | Parse JSON string to dict | `json_string` (string, required) |
| `json_format` | Format dict/object to pretty JSON | `data` (object, required), `indent` (integer, default: 2) |
| `yaml_parse` | Parse YAML to dict | `yaml_string` (string, required) |
| `yaml_format` | Format dict to YAML | `data` (object, required) |
| `csv_parse` | Parse CSV to list of dicts | `csv_string` (string, required), `delimiter` (string, default: ",") |
| `csv_format` | Format list of dicts to CSV | `data` (array, required), `columns` (array, optional) |

### Time & Scheduling

| Tool | Description | Parameters |
|------|-------------|------------|
| `current_time` | Get current date/time | `timezone` (string, optional) |
| `sleep` | Sleep for N seconds | `seconds` (integer, required) |
| `schedule` | Schedule a future task (requires background runner) | `delay_seconds` (integer, required), `action` (string, required), `params` (object, optional) |

### Image & Media

| Tool | Description | Parameters |
|------|-------------|------------|
| `image_info` | Get image metadata (dimensions, format, size) | `path` (string, required) |
| `image_resize` | Resize an image | `path` (string, required), `width` (integer), `height` (integer), `output_path` (string, required) |
| `image_convert` | Convert image format | `path` (string, required), `format` (string: png|jpg|webp|gif), `output_path` (string, required) |
| `generate_image` | Generate image from text (requires image generation model) | `prompt` (string, required), `size` (string: 1024x1024), `output_path` (string) |

---

## Return Format

All tools return a JSON-serializable dict with at least:

```json
{
    "success": true|false,
    "result": <tool-specific result data>,
    "error": <error message if failed>
}
```

Example success:
```json
{
  "success": true,
  "result": "File content here...",
  "error": null
}
```

Example error:
```json
{
  "success": false,
  "result": null,
  "error": "File not found: /path/to/file"
}
```

---

## Schema Access

Tools can be introspected programmatically:

```python
from stack_cli.tools import get_tool_schemas, get_tool

# Get all tool schemas for LLM function calling
schemas = get_tool_schemas()

# Get a specific tool
read_tool = get_tool("read")
result = read_tool(path="/path/to/file")
```

---

## Extending

To add a new tool, define a function and register it in `stack_cli/tools.py`:

```python
def my_tool(param1: str, param2: int = 5) -> dict:
    """Tool description for LLM."""
    try:
        # Do work
        result = do_something(param1, param2)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Register
register_tool("my_tool", my_tool, "Description for LLM")
```

The system automatically generates JSON schemas from type hints and docstrings.
