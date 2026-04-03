# Stack 2.9 - Tool Reference

**38 Built-in Tools** for file operations, git, code execution, web, memory, and task planning.

---

## 📁 File Operations

### read
**Description:** Read file contents with optional offset and limit.
**Input:**
```json
{
  "path": "string (required) - file path to read",
  "offset": "integer (optional, default 0) - starting line number",
  "limit": "integer (optional, default -1) - max lines to read (-1 = all)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "content": "string - file contents",
  "total_lines": "integer",
  "path": "string",
  "error": "string (if success=false)"
}
```
**Example:**
```python
read(path: '/home/user/file.py', offset: 0, limit: 100)
```

### write
**Description:** Write content to file (create or overwrite).
**Input:**
```json
{
  "path": "string (required) - destination file path",
  "content": "string (required) - content to write",
  "append": "boolean (optional, default false) - append instead of overwrite"
}
```
**Output:**
```json
{
  "success": "boolean",
  "path": "string",
  "lines_written": "integer"
}
```
**Example:**
```python
write(path: 'output.txt', content: 'Hello World', append: false)
```

### edit
**Description:** Edit file using exact text replacement (first occurrence only).
**Input:**
```json
{
  "path": "string (required) - file to edit",
  "old_text": "string (required) - text to find and replace",
  "new_text": "string (required) - replacement text"
}
```
**Output:**
```json
{
  "success": "boolean",
  "path": "string",
  "edits_made": "integer (usually 1)",
  "error": "string (if old_text not found or file missing)"
}
```
**Example:**
```python
edit(path: 'config.py', old_text: 'DEBUG = True', new_text: 'DEBUG = False')
```

### search
**Description:** Recursively search for files matching a glob pattern.
**Input:**
```json
{
  "path": "string (required) - base directory to search",
  "pattern": "string (required) - glob pattern (e.g., '*.py', '**/*.md')",
  "exclude": "array of strings (optional) - exclusion patterns"
}
```
**Output:**
```json
{
  "success": "boolean",
  "matches": "array of file paths (strings)",
  "count": "integer",
  "error": "string"
}
```
**Example:**
```python
search(path: '/project', pattern: '**/*.py', exclude: ['node_modules', '.git'])
```

### grep
**Description:** Search for regex pattern in file(s), optionally with context lines.
**Input:**
```json
{
  "path": "string (required) - file or directory to search",
  "pattern": "string (required) - regex pattern",
  "context": "integer (optional, default 0) - number of lines before/after"
}
```
**Output:**
```json
{
  "success": "boolean",
  "matches": "array of objects with: file, line, content, [context]",
  "count": "integer"
}
```
**Example:**
```python
grep(path: '/src', pattern: 'def\\s+\\w+', context: 2)
```

### copy
**Description:** Copy file or directory.
**Input:**
```json
{
  "source": "string (required) - source path",
  "destination": "string (required) - destination path"
}
```
**Output:**
```json
{
  "success": "boolean",
  "source": "string",
  "destination": "string",
  "error": "string"
}
```
**Example:**
```python
copy(source: 'backup/config.yaml', destination: 'config.yaml')
```

### move
**Description:** Move or rename file/directory.
**Input:**
```json
{
  "source": "string (required) - current path",
  "destination": "string (required) - new path"
}
```
**Output:**
```json
{
  "success": "boolean",
  "source": "string",
  "destination": "string"
}
```
**Example:**
```python
move(source: 'old_name.py', destination: 'new_name.py')
```

### delete
**Description:** Delete file or directory. Requires `force=True` for actual deletion (safety).
**Input:**
```json
{
  "path": "string (required) - path to delete",
  "force": "boolean (optional, default false) - must be true to actually delete"
}
```
**Output:**
```json
{
  "success": "boolean",
  "deleted": "string (if force=true)",
  "warning": "string (if force=false)",
  "error": "string"
}
```
**Example:**
```python
delete(path: 'temp_file.log', force: true)
```

---

## 🔀 Git Operations

### git_status
**Description:** Get git status (modified, untracked files).
**Input:**
```json
{
  "repo_path": "string (optional, default '.') - git repository path"
}
```
**Output:**
```json
{
  "success": "boolean",
  "files": "array of file paths (strings)",
  "count": "integer",
  "repo": "string",
  "error": "string"
}
```
**Example:**
```python
git_status(repo_path: '/my/project')
```

### git_commit
**Description:** Create a git commit with optional file staging.
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "message": "string (required) - commit message",
  "files": "array of strings (optional) - specific files to stage (default: all)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "message": "string",
  "output": "string (full git output)",
  "error": "string"
}
```
**Example:**
```python
git_commit(repo_path: '.', message: 'Fix bug in parser', files: ['src/parser.py'])
```

### git_push
**Description:** Push commits to remote repository.
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "remote": "string (optional, default 'origin')",
  "branch": "string (optional) - branch name (default: current branch)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "remote": "string",
  "branch": "string",
  "output": "string",
  "error": "string"
}
```
**Example:**
```python
git_push(repo_path: '.', remote: 'origin', branch: 'main')
```

### git_pull
**Description:** Pull changes from remote repository.
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "remote": "string (optional, default 'origin')",
  "branch": "string (optional)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "remote": "string",
  "branch": "string",
  "output": "string",
  "error": "string"
}
```
**Example:**
```python
git_pull(repo_path: '.', remote: 'origin')
```

### git_branch
**Description:** List, create, or delete branches.
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "create": "string (optional) - create new branch with this name",
  "delete": "string (optional) - delete branch with this name"
}
```
**Output:**
```json
{
  "success": "boolean",
  "branches": "array of strings (when listing)",
  "count": "integer",
  "created": "string (when creating)",
  "deleted": "string (when deleting)",
  "error": "string"
}
```
**Example:**
```python
git_branch(repo_path: '.', create: 'feature/new-ui')
```

### git_log
**Description:** Get commit history (oneline format).
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "limit": "integer (optional, default 10) - max commits to return"
}
```
**Output:**
```json
{
  "success": "boolean",
  "commits": "array of strings (oneline format)",
  "count": "integer"
}
```
**Example:**
```python
git_log(repo_path: '.', limit: 20)
```

### git_diff
**Description:** Show git diff (staged or unstaged changes).
**Input:**
```json
{
  "repo_path": "string (optional, default '.')",
  "file": "string (optional) - limit diff to specific file",
  "staged": "boolean (optional, default false) - show staged changes"
}
```
**Output:**
```json
{
  "success": "boolean",
  "diff": "string - full diff output",
  "has_changes": "boolean",
  "error": "string"
}
```
**Example:**
```python
git_diff(repo_path: '.', staged: true)
```

---

## 💻 Code Execution

### run
**Description:** Execute shell command with timeout and working directory.
**Input:**
```json
{
  "command": "string (required) - shell command to execute",
  "timeout": "integer (optional, default 60) - timeout in seconds",
  "cwd": "string (optional) - working directory",
  "env": "object (optional) - environment variables to add/override"
}
```
**Output:**
```json
{
  "success": "boolean (true if returncode==0)",
  "returncode": "integer",
  "stdout": "string",
  "stderr": "string",
  "command": "string"
}
```
**Example:**
```python
run(command: 'npm test', timeout: 120, cwd: '/project')
```

### test
**Description:** Run tests using pytest.
**Input:**
```json
{
  "path": "string (optional, default '.') - test directory or file",
  "pattern": "string (optional, default 'test*.py') - test file pattern",
  "verbose": "boolean (optional, default true) - verbose output"
}
```
**Output:**
```json
{
  "success": "boolean (true if tests pass)",
  "output": "string (stdout)",
  "errors": "string (stderr)",
  "returncode": "integer"
}
```
**Example:**
```python
test(path: 'tests/', pattern: 'test_*.py', verbose: true)
```

### lint
**Description:** Lint code using ruff, pylint, or mypy.
**Input:**
```json
{
  "path": "string (optional, default '.')",
  "linter": "string (optional, default 'ruff') - one of: 'ruff', 'pylint', 'mypy'"
}
```
**Output:**
```json
{
  "success": "boolean",
  "output": "string",
  "errors": "string"
}
```
**Example:**
```python
lint(path: 'src/', linter: 'ruff')
```

### format
**Description:** Format code using ruff or black.
**Input:**
```json
{
  "path": "string (optional, default '.')",
  "formatter": "string (optional, default 'ruff') - one of: 'ruff', 'black'"
}
```
**Output:**
```json
{
  "success": "boolean",
  "output": "string",
  "errors": "string"
}
```
**Example:**
```python
format(path: '.', formatter: 'black')
```

### typecheck
**Description:** Run mypy type checking.
**Input:**
```json
{
  "path": "string (optional, default '.')"
}
```
**Output:**
```json
{
  "success": "boolean",
  "output": "string",
  "errors": "string"
}
```
**Example:**
```python
typecheck(path: 'src/')
```

### server
**Description:** Start a development server (foreground or background).
**Input:**
```json
{
  "command": "string (required) - command to start server",
  "port": "integer (required) - port number",
  "cwd": "string (optional) - working directory",
  "background": "boolean (optional, default false) - run in background"
}
```
**Output:**
```json
{
  "success": "boolean",
  "pid": "integer (if background=true)",
  "port": "integer",
  "message": "string",
  "output": "string (if background=false)"
}
```
**Example:**
```python
server(command: 'python -m http.server 8000', port: 8000, background: true)
```

### install
**Description:** Install dependencies from requirements file.
**Input:**
```json
{
  "path": "string (optional, default '.')",
  "package_manager": "string (optional, default 'pip') - 'pip', 'poetry', or 'npm'"
}
```
**Output:**
```json
{
  "success": "boolean",
  "output": "string",
  "errors": "string"
}
```
**Example:**
```python
install(path: '.', package_manager: 'pip')
```

---

## 🌐 Web

### web_search
**Description:** Search the web (uses brave-search CLI or fallback).
**Input:**
```json
{
  "query": "string (required) - search query",
  "count": "integer (optional, default 5) - number of results",
  "freshness": "string (optional) - time filter (day, week, month, year)",
  "language": "string (optional) - language code (e.g., 'en')"
}
```
**Output:**
```json
{
  "success": "boolean",
  "query": "string",
  "results": "array of {title, url, snippet} objects",
  "error": "string"
}
```
**Example:**
```python
web_search(query: 'python asyncio tutorial', count: 5)
```

### fetch
**Description:** Fetch and extract text content from URL.
**Input:**
```json
{
  "url": "string (required) - URL to fetch",
  "max_chars": "integer (optional, default 10000) - max characters to return"
}
```
**Output:**
```json
{
  "success": "boolean",
  "url": "string",
  "content": "string (truncated to max_chars)",
  "length": "integer",
  "error": "string"
}
```
**Example:**
```python
fetch(url: 'https://example.com', max_chars: 5000)
```

### download
**Description:** Download file from URL to local destination.
**Input:**
```json
{
  "url": "string (required) - URL to download",
  "destination": "string (required) - local file path"
}
```
**Output:**
```json
{
  "success": "boolean",
  "url": "string",
  "destination": "string",
  "size": "integer (bytes)",
  "error": "string"
}
```
**Example:**
```python
download(url: 'https://example.com/file.zip', destination: 'downloads/file.zip')
```

### check_url
**Description:** Check if URL is accessible (HTTP status code).
**Input:**
```json
{
  "url": "string (required) - URL to check"
}
```
**Output:**
```json
{
  "success": "boolean (true for 200, 301, 302)",
  "url": "string",
  "status_code": "string (e.g., '200')"
}
```
**Example:**
```python
check_url(url: 'https://api.example.com/health')
```

### screenshot
**Description:** Take screenshot of webpage (requires puppeteer).
**Input:**
```json
{
  "url": "string (required) - webpage URL",
  "destination": "string (optional, default 'screenshot.png') - output file path"
}
```
**Output:**
```json
{
  "success": "boolean",
  "url": "string",
  "destination": "string",
  "error": "string"
}
```
**Example:**
```python
screenshot(url: 'https://example.com', destination: 'page.png')
```

---

## 🧠 Memory

### memory_recall
**Description:** Search memory files (MEMORY.md and memory/*.md) for query.
**Input:**
```json
{
  "query": "string (required) - search term",
  "max_results": "integer (optional, default 5) - max matching files to return"
}
```
**Output:**
```json
{
  "success": "boolean",
  "query": "string",
  "matches": "array of file paths",
  "count": "integer"
}
```
**Example:**
```python
memory_recall(query: 'project Alpha', max_results: 10)
```

### memory_save
**Description:** Save a memory entry to MEMORY.md.
**Input:**
```json
{
  "key": "string (required) - entry title/heading",
  "value": "string (required) - entry content"
}
```
**Output:**
```json
{
  "success": "boolean",
  "key": "string",
  "saved": "boolean"
}
```
**Example:**
```python
memory_save(key: 'Meeting with Client', value: 'Discussed timeline and requirements')
```

### memory_list
**Description:** List all memory entries (titles only).
**Input:** `{}`
**Output:**
```json
{
  "success": "boolean",
  "entries": "array of {title, content_preview}",
  "count": "integer"
}
```
**Example:**
```python
memory_list()
```

### context_load
**Description:** Load core context files (AGENTS.md, SOUL.md, TOOLS.md).
**Input:** `{}`
**Output:**
```json
{
  "success": "boolean",
  "context": "object with keys: agents, soul, tools",
  "loaded": "array of loaded file names"
}
```
**Example:**
```python
context_load()
```

### project_scan
**Description:** Scan project structure and detect key files.
**Input:**
```json
{
  "path": "string (optional, default '.')"
}
```
**Output:**
```json
{
  "success": "boolean",
  "project": {
    "name": "string",
    "files": "array",
    "dirs": "array",
    "has_git": "boolean",
    "has_pyproject": "boolean",
    "has_package_json": "boolean",
    "has_dockerfile": "boolean"
  }
}
```
**Example:**
```python
project_scan(path: '/my/project')
```

---

## 📋 Task Planning

### create_task
**Description:** Create a new task with title, description, priority.
**Input:**
```json
{
  "title": "string (required)",
  "description": "string (optional, default '')",
  "priority": "string (optional, default 'medium') - 'low', 'medium', 'high', 'critical'"
}
```
**Output:**
```json
{
  "success": "boolean",
  "task": {
    "id": "string (8-char hash)",
    "title": "string",
    "description": "string",
    "priority": "string",
    "status": "pending",
    "created": "ISO timestamp"
  }
}
```
**Example:**
```python
create_task(title: 'Fix login bug', description: 'Users cannot logout', priority: 'high')
```

### list_tasks
**Description:** List tasks with optional filtering.
**Input:**
```json
{
  "status": "string (optional) - filter by status",
  "priority": "string (optional) - filter by priority"
}
```
**Output:**
```json
{
  "success": "boolean",
  "tasks": "array of task objects",
  "count": "integer"
}
```
**Example:**
```python
list_tasks(status: 'pending', priority: 'high')
```

### update_task
**Description:** Update task status or fields.
**Input:**
```json
{
  "task_id": "string (required) - task identifier",
  "status": "string (optional) - new status (pending, in_progress, done, blocked)",
  "**kwargs": "any other fields to update"
}
```
**Output:**
```json
{
  "success": "boolean",
  "task_id": "string",
  "updated": "boolean"
}
```
**Example:**
```python
update_task(task_id: 'a1b2c3d4', status: 'in_progress')
```

### delete_task
**Description:** Delete a task by ID.
**Input:**
```json
{
  "task_id": "string (required)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "task_id": "string",
  "deleted": "boolean"
}
```
**Example:**
```python
delete_task(task_id: 'a1b2c3d4')
```

### create_plan
**Description:** Create an execution plan with ordered steps.
**Input:**
```json
{
  "goal": "string (required)",
  "steps": "array of strings (required) - ordered list of steps"
}
```
**Output:**
```json
{
  "success": "boolean",
  "plan": {
    "id": "string (8-char hash)",
    "goal": "string",
    "steps": "array",
    "status": "pending",
    "created": "ISO timestamp"
  }
}
```
**Example:**
```python
create_plan(goal: 'Deploy to production', steps: ['Build Docker image', 'Push to registry', 'Update k8s config'])
```

### execute_plan
**Description:** Mark a plan as executing (manual step-by-step execution).
**Input:**
```json
{
  "plan_id": "string (required)"
}
```
**Output:**
```json
{
  "success": "boolean",
  "plan_id": "string",
  "status": "executing",
  "steps": "array of steps to execute"
}
```
**Example:**
```python
execute_plan(plan_id: 'p1l2a3n4')
```

---

## 📝 Notes

- All tools return a dictionary with at least a `success` boolean key.
- On failure, additional keys (`error`, `message`) provide details.
- Paths are relative to current working directory unless absolute.
- Timeouts prevent infinite hangs (default varies per tool).
- For safety, destructive operations (delete) require explicit flags.

---

**Total Tools:** 38 across 6 categories
