"""Tool registry for Stack 2.9 tools."""

from __future__ import annotations

from typing import Any

from .base import BaseTool


class ToolRegistry:
    """Singleton registry mapping tool names to tool instances."""

    _instance: ToolRegistry | None = None
    _tools: dict[str, BaseTool] = {}

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tools = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance by name."""
        if not tool.name:
            raise ValueError("Tool must have a non-empty name")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a registered tool by name."""
        return self._tools.get(name)

    def list(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_tools(self) -> dict[str, dict[str, Any]]:
        """List all registered tools with their info.
        
        Returns a dict mapping tool name to info dict with keys:
        - name: str
        - description: str
        - input_schema: dict
        """
        result = {}
        for name, tool in self._tools.items():
            schema = tool.input_schema
            if callable(schema):
                schema = schema()
            result[name] = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": schema,
            }
        return result

    def call(self, name: str, input_data: dict[str, Any]) -> Any:
        """Convenience: get tool and call it in one step."""
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool not found: {name}")
        return tool.call(input_data)

    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry. Returns True if it existed."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False


def get_registry() -> ToolRegistry:
    """Get the global ToolRegistry instance."""
    return ToolRegistry()

# Global registry instance
tool_registry = ToolRegistry()
