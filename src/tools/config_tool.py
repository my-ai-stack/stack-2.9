"""ConfigTool - Runtime configuration management for Stack 2.9"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseTool, ToolResult
from .registry import tool_registry

CONFIG_FILE = Path.home() / ".stack-2.9" / "config.json"


def _load_config() -> Dict[str, Any]:
    """Load config from disk."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"settings": {}}


def _save_config(data: Dict[str, Any]) -> None:
    """Save config to disk."""
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


# Default settings
DEFAULT_SETTINGS = {
    "model": "Qwen/Qwen2.5-Coder-1.5B",
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_length": 32768,
    "tools_enabled": True,
    "voice_enabled": False,
    "language": "en"
}


class ConfigGetTool(BaseTool):
    """Get a configuration value."""

    name = "config_get"
    description = "Get configuration value"

    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"}
        },
        "required": ["key"]
    }

    async def execute(self, key: str) -> ToolResult:
        """Get config value."""
        data = _load_config()
        value = data.get("settings", {}).get(key)

        if value is None:
            value = DEFAULT_SETTINGS.get(key)

        if value is None:
            return ToolResult(success=False, error=f"Config key not found: {key}")

        return ToolResult(success=True, data={
            "key": key,
            "value": value
        })


class ConfigSetTool(BaseTool):
    """Set a configuration value."""

    name = "config_set"
    description = "Set configuration value"

    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"},
            "value": {"type": "string", "description": "Config value"}
        },
        "required": ["key", "value"]
    }

    async def execute(self, key: str, value: Any) -> ToolResult:
        """Set config value."""
        data = _load_config()

        if "settings" not in data:
            data["settings"] = {}

        # Type conversion
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)

        data["settings"][key] = value
        _save_config(data)

        return ToolResult(success=True, data={
            "key": key,
            "value": value,
            "status": "set"
        })


class ConfigListTool(BaseTool):
    """List all configuration values."""

    name = "config_list"
    description = "List all configuration settings"

    input_schema = {
        "type": "object",
        "properties": {
            "include_defaults": {"type": "boolean", "default": False}
        },
        "required": []
    }

    async def execute(self, include_defaults: bool = False) -> ToolResult:
        """List config."""
        data = _load_config()
        settings = data.get("settings", {})

        if include_defaults:
            all_settings = dict(DEFAULT_SETTINGS)
            all_settings.update(settings)
            settings = all_settings

        return ToolResult(success=True, data={
            "settings": settings,
            "count": len(settings)
        })


class ConfigDeleteTool(BaseTool):
    """Delete a configuration value (reset to default)."""

    name = "config_delete"
    description = "Delete configuration value"

    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key to delete"}
        },
        "required": ["key"]
    }

    async def execute(self, key: str) -> ToolResult:
        """Delete config."""
        data = _load_config()

        if key in data.get("settings", {}):
            del data["settings"][key]
            _save_config(data)
            return ToolResult(success=True, data={
                "key": key,
                "status": "deleted"
            })

        return ToolResult(success=False, error=f"Config key not found: {key}")


# Register tools
tool_registry.register(ConfigGetTool())
tool_registry.register(ConfigSetTool())
tool_registry.register(ConfigListTool())
tool_registry.register(ConfigDeleteTool())
