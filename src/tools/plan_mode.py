"""PlanModeTool - Agent reasoning mode for Stack 2.9"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTool, ToolResult
from .registry import tool_registry

PLAN_FILE = Path.home() / ".stack-2.9" / "plan.json"


def _load_plan() -> Dict[str, Any]:
    """Load current plan state."""
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PLAN_FILE.exists():
        return json.loads(PLAN_FILE.read_text())
    return {"active": False, "steps": [], "context": ""}


def _save_plan(data: Dict[str, Any]) -> None:
    """Save plan state."""
    PLAN_FILE.write_text(json.dumps(data, indent=2))


def _clear_plan() -> None:
    """Clear plan state."""
    if PLAN_FILE.exists():
        PLAN_FILE.unlink()


class EnterPlanModeTool(BaseTool):
    """Enter plan mode for structured reasoning."""

    name = "enter_plan_mode"
    description = "Enter plan mode for structured reasoning"

    input_schema = {
        "type": "object",
        "properties": {
            "context": {"type": "string", "description": "Initial context or goal"},
            "steps": {"type": "array", "items": {"type": "string"}, "description": "Initial reasoning steps"}
        },
        "required": ["context"]
    }

    async def execute(self, context: str, steps: Optional[List[str]] = None) -> ToolResult:
        """Enter plan mode."""
        data = {
            "active": True,
            "context": context,
            "steps": steps or [],
            "entered_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

        _save_plan(data)

        return ToolResult(success=True, data={
            "status": "entered",
            "context": context,
            "step_count": len(steps or [])
        })


class ExitPlanModeTool(BaseTool):
    """Exit plan mode."""

    name = "exit_plan_mode"
    description = "Exit plan mode and get summary"

    input_schema = {
        "type": "object",
        "properties": {
            "confirm": {"type": "boolean", "default": False, "description": "Confirm exit"},
            "summary": {"type": "string", "description": "Optional summary of reasoning"}
        },
        "required": ["confirm"]
    }

    async def execute(self, confirm: bool, summary: Optional[str] = None) -> ToolResult:
        """Exit plan mode."""
        if not confirm:
            return ToolResult(success=False, error="Must confirm exit to leave plan mode")

        data = _load_plan()

        if not data.get("active"):
            return ToolResult(success=False, error="Plan mode not active")

        result = {
            "status": "exited",
            "context": data.get("context"),
            "step_count": len(data.get("steps", [])),
            "summary": summary or data.get("context", ""),
            "duration": datetime.now().isoformat()
        }

        _clear_plan()

        return ToolResult(success=True, data=result)


class PlanAddStepTool(BaseTool):
    """Add a reasoning step to the plan."""

    name = "plan_add_step"
    description = "Add a reasoning step to active plan"

    input_schema = {
        "type": "object",
        "properties": {
            "step": {"type": "string", "description": "Reasoning step text"},
            "confidence": {"type": "number", "description": "Confidence level 0-1"}
        },
        "required": ["step"]
    }

    async def execute(self, step: str, confidence: Optional[float] = None) -> ToolResult:
        """Add step to plan."""
        data = _load_plan()

        if not data.get("active"):
            return ToolResult(success=False, error="Plan mode not active")

        step_entry = {
            "text": step,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence
        }

        data["steps"].append(step_entry)
        data["last_updated"] = datetime.now().isoformat()
        _save_plan(data)

        return ToolResult(success=True, data={
            "step_number": len(data["steps"]),
            "total_steps": len(data["steps"])
        })


class PlanStatusTool(BaseTool):
    """Get current plan status."""

    name = "plan_status"
    description = "Get status of current plan"

    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self) -> ToolResult:
        """Get plan status."""
        data = _load_plan()

        return ToolResult(success=True, data={
            "active": data.get("active", False),
            "context": data.get("context"),
            "steps": data.get("steps", []),
            "step_count": len(data.get("steps", []))
        })


# Register tools
tool_registry.register(EnterPlanModeTool())
tool_registry.register(ExitPlanModeTool())
tool_registry.register(PlanAddStepTool())
tool_registry.register(PlanStatusTool())
