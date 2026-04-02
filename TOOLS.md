# Stack 2.9 - Complete Tools Reference

Stack 2.9 provides **38 built-in tools** for file operations, git, code execution, web requests, memory, and task management. This document provides the complete reference with actual parameter names, types, and usage examples.

---

## Tool Calling Format

Tools are called using a JSON-based function calling format. The agent automatically selects tools based on user intent, but you can also call them directly via the agent API.

### Example Tool Call

```json
{
  "tool": "read",
  "params": {
    "path": "/path/to/file.py"
  },
  "id": "call_123"
}
```

### Return Format

All tools return a JSON-serializable dict:

```json
{
  "success": true|false,
  "result": <tool-specific result data>,
  "error": <error message if failed>
}
```

---

## Complete Tool Catalog

### 1. File Operations

#### `read`
Read file contents with optional pagination.
- **Parameters:**
  - `path` (string, required) - Path to the file
  - `offset` (integer, optional, default: 0) - Line number to start from (0-indexed)
  - `limit` (integer, optional, default: -1) - Maximum lines to read (-1 = all)
- **Returns:** `{success, content, total_lines, path}`

**Example:**
```json
{
  "tool": "read",
  "params": {"path": "stack_cli/cli.py", "limit": 50}
}
```

#### `write`
Write content to a file (overwrites by default).
- **Parameters:**
  - `path` (string, required) - Destination file path
  - `content` (string, required) - Content to write
  - `append` (boolean, optional, default: false) - Append instead of overwrite
- **Returns:** `{success, path, lines_written}`

**Example:**
```json
{
  "tool": "write",
  "params": {
    "path": "output.txt",
    "content": "Hello, World!",
    "append": false
  }
}
```

#### `edit`
Replace exact text in a file (single occurrence).
- **Parameters:**
  - `path` (string, required) - File to edit
  - `old_text` (string, required) - Text to find and replace
  - `new_text` (string, required) - Replacement text
- **Returns:** `{success, path, edits_made}`

**Example:**
```json
{
  "tool": "edit",
  "params": {
    "path": "config.yaml",
    "old_text": "debug: false",
    "new_text": "debug: true"
  }
}
```

#### `search`
Recursively search for files matching a glob pattern.
- **Parameters:**
  - `path` (string, required) - Directory to search in
  - `pattern` (string, required) - Glob pattern (e.g., `"*.py"`, `"**/*.md"`)
  - `exclude` (array of strings, optional) - Paths to exclude
- **Returns:** `{success, matches, count}`

**Example:**
```json
{
  "tool": "search",
  "params": {
    "path": ".",
    "pattern": "**/*.py",
    "exclude": ["__pycache__", "node_modules"]
  }
}
```

#### `grep`
Search for regex pattern across files with optional context.
- **Parameters:**
  - `path` (string, required) - File or directory to search
  - `pattern` (string, required) - Regular expression pattern
  - `context` (integer, optional, default: 0) - Lines of context before/after
- **Returns:** `{success, matches, count}` where each match has `{file, line, content, context?}`

**Example:**
```json
{
  "tool": "grep",
  "params": {
    "path": "stack_cli",
    "pattern": "def tool_",
    "context": 2
  }
}
```

#### `copy`
Copy file or directory (recursive for directories).
- **Parameters:**
  - `source` (string, required) - Source path
  - `destination` (string, required) - Destination path
- **Returns:** `{success, source, destination}`

**Example:**
```json
{
  "tool": "copy",
  "params": {
    "source": "config.example.yaml",
    "destination": "config.yaml"
  }
}
```

#### `move`
Move or rename file/directory.
- **Parameters:**
  - `source` (string, required) - Current path
  - `destination` (string, required) - New path
- **Returns:** `{success, source, destination}`

**Example:**
```json
{
  "tool": "move",
  "params": {
    "source": "old_name.py",
    "destination": "new_name.py"
  }
}
```

#### `delete`
Delete file or directory (requires force=True for safety).
- **Parameters:**
  - `path` (string, required) - Path to delete
  - `force` (boolean, optional, default: false) - Actually delete when true
- **Returns:** `{success, deleted/would_delete, warning?}`

**Example:**
```json
{
  "tool": "delete",
  "params": {
    "path": "obsolete_file.txt",
    "force": true
  }
}
```

---

### 2. Git Operations

#### `git_status`
Get git repository status (porcelain format).
- **Parameters:**
  - `repo_path` (string, optional, default: ".") - Repository root
- **Returns:** `{success, files, count, repo}`

**Example:**
```json
{
  "tool": "git_status",
  "params": {"repo_path": "."}
}
```

#### `git_commit`
Stage changes and create a commit.
- **Parameters:**
  - `repo_path` (string, optional, default: ".") - Repository root
  - `message` (string, required) - Commit message
  - `files` (array of strings, optional) - Specific files to stage (stages all if omitted)
- **Returns:** `{success, message, output}`

**Example:**
```json
{
  "tool": "git_commit",
  "params": {
    "repo_path": ".",
    "message": "feat: add new tool documentation",
    "files": ["TOOLS.md", "docs/tools.md"]
  }
}
```

#### `git_push`
Push commits to remote repository.
- **Parameters:**
  - `repo_path` (string, optional, default: ".") - Repository root
  - `remote` (string, optional, default: "origin") - Remote name
  - `branch` (string, optional) - Branch name (pushes current branch if omitted)
- **Returns:** `{success, remote, branch, output}`

**Example:**
```json
{
  "tool": "git_push",
  "params": {
    "repo_path": ".",
    "remote": "origin",
    "branch": "main"
  }
}
```

#### `git_pull`
Pull changes from remote.
- **Parameters:**
  - `repo_path` (string, optional, default: ".") - Repository root
  - `remote` (string, optional, default: "origin") - Remote name
  - `branch` (string, optional) - Branch name (pulls current branch if omitted)
- **Returns:** `{success, remote, branch, output}`

**Example:**
```json
{
  "tool": "git_pull",
  "params": {
    "repo_path": ".",
    "remote": "origin"
  }
}
```

#### `git_branch`
List, create, or delete branches.
- **Parameters (mutually exclusive):**
  - `repo_path` (string, optional, default: ".")
  - `create` (string, optional) - Create and checkout new branch
  - `delete` (string, optional) - Delete branch
- **Returns:** `{success, branches?, count?, created?, deleted?}`

**Examples:**
```json
// List branches
{"tool": "git_branch", "params": {"repo_path": "."}}

// Create branch
{"tool": "git_branch", "params": {"create": "feature/new-docs"}}

// Delete branch
{"tool": "git_branch", "params": {"delete": "old-branch"}}
```

#### `git_log`
View commit history.
- **Parameters:**
  - `repo_path` (string, optional, default: ".")
  - `limit` (integer, optional, default: 10) - Maximum commits
- **Returns:** `{success, commits, count}`

**Example:**
```json
{
  "tool": "git_log",
  "params": {"repo_path": ".", "limit": 20}
}
```

#### `git_diff`
Show changes between commits or working tree.
- **Parameters:**
  - `repo_path` (string, optional, default: ".")
  - `file` (string, optional) - Specific file to diff
  - `staged` (boolean, optional, default: false) - Show staged changes
- **Returns:** `{success, diff, has_changes}`

**Example:**
```json
{
  "tool": "git_diff",
  "params": {
    "repo_path": ".",
    "staged": true
  }
}
```

---

### 3. Code Execution

#### `run`
Execute shell command with timeout.
- **Parameters:**
  - `command` (string, required) - Shell command to run
  - `timeout` (integer, optional, default: 60) - Seconds before timeout
  - `cwd` (string, optional) - Working directory
  - `env` (object, optional) - Environment variables to merge
- **Returns:** `{success, returncode, stdout, stderr, command}`

**Example:**
```json
{
  "tool": "run",
  "params": {
    "command": "python -m pytest tests/ -v",
    "timeout": 300,
    "cwd": "."
  }
}
```

#### `test`
Run tests using pytest.
- **Parameters:**
  - `path` (string, optional, default: ".") - Test directory or file
  - `pattern` (string, optional, default: "test*.py") - Test file pattern
  - `verbose` (boolean, optional, default: true) - Verbose output
- **Returns:** `{success, output, errors, returncode}`

**Example:**
```json
{
  "tool": "test",
  "params": {
    "path": "tests/",
    "pattern": "test_*.py",
    "verbose": true
  }
}
```

#### `lint`
Lint code with specified linter (ruff, pylint, mypy).
- **Parameters:**
  - `path` (string, optional, default: ".")
  - `linter` (string, optional, default: "ruff") - "ruff", "pylint", or "mypy"
- **Returns:** `{success, output, errors}`

**Example:**
```json
{
  "tool": "lint",
  "params": {
    "path": "stack_cli/",
    "linter": "ruff"
  }
}
```

#### `format`
Format code with specified formatter.
- **Parameters:**
  - `path` (string, optional, default: ".")
  - `formatter` (string, optional, default: "ruff") - "ruff" or "black"
- **Returns:** `{success, output, errors}`

**Example:**
```json
{
  "tool": "format",
  "params": {
    "path": ".",
    "formatter": "black"
  }
}
```

#### `typecheck`
Run type checking with mypy.
- **Parameters:**
  - `path` (string, optional, default: ".")
- **Returns:** `{success, output, errors}`

**Example:**
```json
{
  "tool": "typecheck",
  "params": {"path": "stack_cli"}
}
```

#### `server`
Start a development server (optionally in background).
- **Parameters:**
  - `command` (string, required) - Command to start server
  - `port` (integer, required) - Port number (for reference)
  - `cwd` (string, optional) - Working directory
  - `background` (boolean, optional, default: false) - Run in background
- **Returns:** `{success, pid?, port, message}` or `{success, output}`

**Example:**
```json
{
  "tool": "server",
  "params": {
    "command": "python -m http.server 8000",
    "port": 8000,
    "background": true
  }
}
```

#### `install`
Install dependencies from requirements file.
- **Parameters:**
  - `path` (string, optional, default: ".") - Project directory
  - `package_manager` (string, optional, default: "pip") - "pip", "poetry", or "npm"
- **Returns:** `{success, output, errors}`

**Example:**
```json
{
  "tool": "install",
  "params": {
    "path": ".",
    "package_manager": "pip"
  }
}
```

---

### 4. Web & Search

#### `web_search`
Search the web using Brave Search.
- **Parameters:**
  - `query` (string, required) - Search query
  - `count` (integer, optional, default: 5) - Number of results (1-10)
  - `freshness` (string, optional) - Filter by time: "day", "week", "month", "year"
  - `language` (string, optional) - ISO 639-1 language code (e.g., "en", "fr")
- **Returns:** `{success, query, results, count}`

**Example:**
```json
{
  "tool": "web_search",
  "params": {
    "query": "Stack 2.9 AI coding assistant",
    "count": 10,
    "freshness": "month"
  }
}
```

#### `fetch`
Download and extract content from a URL.
- **Parameters:**
  - `url` (string, required) - URL to fetch
  - `max_chars` (integer, optional, default: 10000) - Maximum content length
- **Returns:** `{success, url, content, length}`

**Example:**
```json
{
  "tool": "fetch",
  "params": {
    "url": "https://example.com/README.md",
    "max_chars": 5000
  }
}
```

#### `download`
Download file from URL to local path.
- **Parameters:**
  - `url` (string, required) - Source URL
  - `destination` (string, required) - Local file path
- **Returns:** `{success, url, destination, size}`

**Example:**
```json
{
  "tool": "download",
  "params": {
    "url": "https://example.com/dataset.csv",
    "destination": "data/dataset.csv"
  }
}
```

#### `check_url`
Check if URL is accessible (HTTP HEAD request).
- **Parameters:**
  - `url` (string, required) - URL to check
- **Returns:** `{success, url, status_code}`

**Example:**
```json
{
  "tool": "check_url",
  "params": {"url": "https://github.com"}
}
```

#### `screenshot`
Take screenshot of a webpage (requires puppeteer).
- **Parameters:**
  - `url` (string, required) - Webpage URL
  - `destination` (string, optional, default: "screenshot.png") - Output path
- **Returns:** `{success, url, destination}`

**Example:**
```json
{
  "tool": "screenshot",
  "params": {
    "url": "https://stack-2-9.example.com",
    "destination": "website.png"
  }
}
```

---

### 5. Memory & Knowledge

#### `memory_recall`
Search memory files for relevant entries.
- **Parameters:**
  - `query` (string, required) - Search query
  - `max_results` (integer, optional, default: 5) - Maximum matches
- **Returns:** `{success, query, matches, count}`

**Example:**
```json
{
  "tool": "memory_recall",
  "params": {
    "query": "deployment requirements",
    "max_results": 10
  }
}
```

#### `memory_save`
Store a memory entry in MEMORY.md.
- **Parameters:**
  - `key` (string, required) - Entry title/heading
  - `value` (string, required) - Content to save
- **Returns:** `{success, key, saved}`

**Example:**
```json
{
  "tool": "memory_save",
  "params": {
    "key": "GPU Requirements",
    "value": "Minimum: 8GB VRAM, Recommended: 24GB VRAM"
  }
}
```

#### `memory_list`
List all memory entries with preview.
- **Parameters:** None
- **Returns:** `{success, entries, count}` where each entry has `{title, content}`

**Example:**
```json
{
  "tool": "memory_list",
  "params": {}
}
```

#### `context_load`
Load workspace context files (AGENTS.md, SOUL.md, TOOLS.md).
- **Parameters:**
  - `projects` (array of strings, optional) - Project names to load
- **Returns:** `{success, context, loaded}`

**Example:**
```json
{
  "tool": "context_load",
  "params": {}
}
```

#### `project_scan`
Scan project structure and detect tech stack.
- **Parameters:**
  - `path` (string, optional, default: ".")
- **Returns:** `{success, project}` with `{name, files, dirs, has_git, has_pyproject, has_package_json, has_dockerfile}`

**Example:**
```json
{
  "tool": "project_scan",
  "params": {"path": "."}
}
```

---

### 6. Task & Planning

#### `create_task`
Create a new task.
- **Parameters:**
  - `title` (string, required) - Task title
  - `description` (string, optional, default: "") - Detailed description
  - `priority` (string, optional, default: "medium") - "low", "medium", or "high"
- **Returns:** `{success, task}` with `{id, title, description, priority, status, created}`

**Example:**
```json
{
  "tool": "create_task",
  "params": {
    "title": "Write comprehensive tool documentation",
    "description": "Create TOOLS.md with all 38 tools documented",
    "priority": "high"
  }
}
```

#### `list_tasks`
List tasks with optional filtering.
- **Parameters:**
  - `status` (string, optional) - Filter by "pending", "done", or "all"
  - `priority` (string, optional) - Filter by "low", "medium", "high"
- **Returns:** `{success, tasks, count}`

**Example:**
```json
{
  "tool": "list_tasks",
  "params": {
    "status": "pending",
    "priority": "high"
  }
}
```

#### `update_task`
Update task status or fields.
- **Parameters:**
  - `task_id` (string, required) - Task identifier
  - `status` (string, optional) - New status
  - Additional fields: `title`, `description`, `priority`
- **Returns:** `{success, task_id, updated}`

**Example:**
```json
{
  "tool": "update_task",
  "params": {
    "task_id": "a1b2c3d4",
    "status": "done"
  }
}
```

#### `delete_task`
Delete a task by ID.
- **Parameters:**
  - `task_id` (string, required) - Task to delete
- **Returns:** `{success, task_id, deleted}`

**Example:**
```json
{
  "tool": "delete_task",
  "params": {"task_id": "a1b2c3d4"}
}
```

#### `create_plan`
Create an execution plan with steps.
- **Parameters:**
  - `goal` (string, required) - Plan objective
  - `steps` (array of strings, required) - Ordered steps
- **Returns:** `{success, plan}` with `{id, goal, steps, status, created}`

**Example:**
```json
{
  "tool": "create_plan",
  "params": {
    "goal": "Deploy to RunPod",
    "steps": [
      "Prepare Docker image",
      "Upload to registry",
      "Launch pod with template",
      "Verify deployment"
    ]
  }
}
```

#### `execute_plan`
Mark a plan as in-progress (execution tracking).
- **Parameters:**
  - `plan_id` (string, required) - Plan identifier
- **Returns:** `{success, plan_id, status, steps}`

**Example:**
```json
{
  "tool": "execute_plan",
  "params": {"plan_id": "p123abc"}
}
```

---

## Tool Count Clarification

**Actual tool count: 38** (not 37). The following categories:
- File Operations: 8 tools
- Git Operations: 7 tools
- Code Execution: 7 tools
- Web & Search: 5 tools
- Memory & Knowledge: 5 tools
- Task & Planning: 6 tools
- **Total: 38 tools**

---

## Extension Mechanism

To add a new tool, edit `stack_cli/tools.py`:

```python
def tool_my_feature(param1: str, param2: int = 42) -> Dict[str, Any]:
    """Brief description for LLM."""
    try:
        # Implementation
        result = do_something(param1, param2)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Register in TOOLS dict
TOOLS["my_feature"] = tool_my_feature
```

The tool will be automatically available. Update this document when adding tools.

---

## Schema Generation

For programmatic access, use:

```python
from stack_cli.tools import get_tool_schemas, get_tool

# Get all tool schemas (for LLM function calling)
schemas = get_tool_schemas()

# Get a specific tool function
read_fn = get_tool("read")
result = read_fn(path="file.txt")
```

**Note:** The `get_tool_schemas()` function currently provides a limited subset. For full production use, extend it to include all 38 tools with proper JSON Schema parameters derived from function signatures.

---

## Best Practices

1. **Always check `success`** in the return value before using results
2. **Use pagination** for large files: `read(path, offset=0, limit=1000)`
3. **Handle errors gracefully** - tools return `error` field when `success=false`
4. **Be cautious with destructive operations**: `delete` requires `force=true`
5. **Set appropriate timeouts** for long-running commands (`run` tool)
6. **Use `git_status` before `git_commit`** to verify what will be committed
7. **Remember context limits** - tool results count against token limits

---

## Quick Reference Table

| Category | Tools | Count |
|----------|-------|-------|
| File Operations | read, write, edit, search, grep, copy, move, delete | 8 |
| Git | git_status, git_commit, git_push, git_pull, git_branch, git_log, git_diff | 7 |
| Execution | run, test, lint, format, typecheck, server, install | 7 |
| Web | web_search, fetch, download, check_url, screenshot | 5 |
| Memory | memory_recall, memory_save, memory_list, context_load, project_scan | 5 |
| Planning | create_task, list_tasks, update_task, delete_task, create_plan, execute_plan | 6 |
| **Total** | | **38** |

---

*Last updated: 2026-04-02*
*Stack 2.9 - Pattern Memory AI*
