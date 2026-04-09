"""TodoWriteTool - Persistent todo lists for Stack 2.9"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTool, ToolResult
from .registry import tool_registry

TODOS_FILE = Path.home() / ".stack-2.9" / "todos.json"


def _load_todos() -> Dict[str, Any]:
    """Load todos from disk."""
    TODOS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TODOS_FILE.exists():
        return json.loads(TODOS_FILE.read_text())
    return {"todos": []}


def _save_todos(data: Dict[str, Any]) -> None:
    """Save todos to disk."""
    TODOS_FILE.write_text(json.dumps(data, indent=2))


class TodoAddTool(BaseTool):
    """Add a new todo item."""

    name = "todo_add"
    description = "Add a new todo item"

    input_schema = {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Todo task description"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
        },
        "required": ["task"]
    }

    async def execute(self, task: str, priority: str = "medium", tags: Optional[List[str]] = None) -> ToolResult:
        """Add todo."""
        data = _load_todos()

        todo_id = str(uuid.uuid4())[:8]
        todo = {
            "id": todo_id,
            "task": task,
            "priority": priority,
            "status": "pending",
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }

        data["todos"].append(todo)
        _save_todos(data)

        return ToolResult(success=True, data={
            "id": todo_id,
            "task": task,
            "status": "added"
        })


class TodoListTool(BaseTool):
    """List all todos."""

    name = "todo_list"
    description = "List all todos with optional filters"

    input_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["pending", "completed", "all"], "default": "pending"},
            "tag": {"type": "string", "description": "Filter by tag"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
        },
        "required": []
    }

    async def execute(self, status: str = "pending", tag: Optional[str] = None, priority: Optional[str] = None) -> ToolResult:
        """List todos."""
        data = _load_todos()
        todos = data.get("todos", [])

        if status != "all":
            todos = [t for t in todos if t.get("status") == status]

        if tag:
            todos = [t for t in todos if tag in t.get("tags", [])]

        if priority:
            todos = [t for t in todos if t.get("priority") == priority]

        return ToolResult(success=True, data={
            "todos": todos,
            "count": len(todos)
        })


class TodoCompleteTool(BaseTool):
    """Mark a todo as completed."""

    name = "todo_complete"
    description = "Mark a todo as completed"

    input_schema = {
        "type": "object",
        "properties": {
            "todo_id": {"type": "string", "description": "Todo ID to complete"}
        },
        "required": ["todo_id"]
    }

    async def execute(self, todo_id: str) -> ToolResult:
        """Complete todo."""
        data = _load_todos()

        for todo in data["todos"]:
            if todo["id"] == todo_id:
                todo["status"] = "completed"
                todo["completed_at"] = datetime.now().isoformat()
                _save_todos(data)
                return ToolResult(success=True, data={
                    "id": todo_id,
                    "status": "completed"
                })

        return ToolResult(success=False, error=f"Todo {todo_id} not found")


class TodoDeleteTool(BaseTool):
    """Delete a todo."""

    name = "todo_delete"
    description = "Delete a todo item"

    input_schema = {
        "type": "object",
        "properties": {
            "todo_id": {"type": "string", "description": "Todo ID to delete"}
        },
        "required": ["todo_id"]
    }

    async def execute(self, todo_id: str) -> ToolResult:
        """Delete todo."""
        data = _load_todos()
        original_count = len(data["todos"])
        data["todos"] = [t for t in data["todos"] if t["id"] != todo_id]

        if len(data["todos"]) == original_count:
            return ToolResult(success=False, error=f"Todo {todo_id} not found")

        _save_todos(data)
        return ToolResult(success=True, data={
            "id": todo_id,
            "status": "deleted"
        })


# Register tools
tool_registry.register(TodoAddTool())
tool_registry.register(TodoListTool())
tool_registry.register(TodoCompleteTool())
tool_registry.register(TodoDeleteTool())
