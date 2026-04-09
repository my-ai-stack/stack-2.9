# Stack 2.9 Tools

Python-native tool implementations compatible with the RTMP tool system.

## Overview

Tools are implemented as Python classes extending `BaseTool`. Each tool has:
- A JSON-schema `input_schema`
- An `execute(input)` method returning `ToolResult[T]`
- Optional `validate_input()` for pre-execution checks

## Available Tools

### Web Search

**Tool:** `WebSearch`

Search the web via DuckDuckGo. Results are cached for 5 minutes.

```python
from src.tools.web_search import WebSearchTool
tool = WebSearchTool()
result = tool.call({
    "query": "latest AI news",
    "max_results": 10,
    "allowed_domains": None,
    "blocked_domains": None,
})
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query (min 2 chars) |
| `allowed_domains` | string[] | No | Restrict to domains |
| `blocked_domains` | string[] | No | Exclude domains |
| `max_results` | int | No | Max results (default 10, max 20) |

**Output:**
```json
{
  "query": "...",
  "results": [{"title": "...", "url": "...", "snippet": "..."}],
  "duration_seconds": 0.5,
  "source": "duckduckgo"
}
```

---

### Task Management

Four tools for task lifecycle management. Tasks stored in `~/.stack-2.9/tasks.json`.

#### TaskCreate

```python
result = get_registry().call("TaskCreate", {
    "subject": "Fix login bug",
    "description": "Users cannot log in with SSO",
    "status": "pending",
    "priority": "high",
    "tags": ["bug", "auth"],
})
```

#### TaskList

```python
result = get_registry().call("TaskList", {
    "status": "pending",
    "tag": "bug",
    "limit": 50,
})
```

#### TaskUpdate

```python
result = get_registry().call("TaskUpdate", {
    "id": "a1b2c3d4",
    "status": "completed",
})
```

#### TaskDelete

```python
result = get_registry().call("TaskDelete", {"id": "a1b2c3d4"})
```

**Task Status Values:** `pending`, `in_progress`, `completed`, `cancelled`

**Priority Values:** `low`, `medium`, `high`, `urgent`

---

### Scheduling / Cron

Schedule prompts for later or recurring execution. Schedules stored in `~/.stack-2.9/schedules.json`.

Uses standard 5-field cron in local time: `minute hour day-of-month month day-of-week`

#### CronCreate

```python
result = get_registry().call("CronCreate", {
    "cron": "*/5 * * * *",      # every 5 minutes
    "prompt": "Check system status",
    "recurring": True,
    "durable": True,             # persists across restarts
})
```

**Cron Examples:**
| Expression | Meaning |
|------------|---------|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 9 * * 1-5` | Weekdays at 9am |
| `30 14 * * *` | 2:30pm daily |
| `0 0 1 * *` | Midnight on 1st of month |

#### CronList

```python
result = get_registry().call("CronList", {})
```

#### CronDelete

```python
result = get_registry().call("CronDelete", {"id": "schedule-id"})
```

---

## Tool Registry

```python
from src.tools import get_registry

registry = get_registry()
registry.list()                        # list all tool names
registry.get("WebSearch")              # get a specific tool
registry.call("TaskCreate", {...})     # validate + execute in one step
```

## Adding New Tools

1. Create `src/tools/your_tool.py` extending `BaseTool`
2. Define `name`, `description`, `input_schema`, and `execute()`
3. Import and register at the bottom of the file: `get_registry().register(YourTool())`
4. Add tests in `tests/test_your_tool.py`
5. Document in this file

## Data Storage

All tools store data under `~/.stack-2.9/`:
- `tasks.json` — task list
- `schedules.json` — cron schedules
- `web_search_cache.json` — cached search results
