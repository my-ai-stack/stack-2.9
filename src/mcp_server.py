"""MCP Server for Stack 2.9 - Exposes Stack tools via Model Context Protocol"""

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

# Import all Stack 2.9 tools (triggers auto-registration)
from src.tools import (
    BaseTool,
    ToolResult,
    get_registry,
    file_read,
    grep_tool,
    task_management,
    team_tool,
    agent_tool,
)


def _tool_to_mcp(tool: BaseTool) -> dict[str, Any]:
    """Convert a Stack 2.9 tool to MCP tool schema."""
    schema = tool.input_schema
    if callable(schema):
        schema = schema()
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": schema,
    }


def _call_tool_sync(tool: BaseTool, arguments: dict[str, Any]) -> Any:
    """Call a tool and extract result data, handling sync/async execute."""
    import inspect

    execute = tool.execute

    # Determine if execute is async or sync
    if inspect.iscoroutinefunction(execute):
        # Run in event loop
        loop = asyncio.get_event_loop()
        if inspect.iscoroutinefunction(execute):
            result = loop.run_until_complete(execute(**arguments))
        else:
            result = execute(**arguments)
    else:
        # Sync execute (uses input_data dict style)
        if hasattr(tool, 'input_schema') and not callable(tool.input_schema):
            result = execute(arguments)
        else:
            result = execute(**arguments)

    if isinstance(result, ToolResult):
        if result.success:
            return {"success": True, "data": result.data}
        else:
            return {"success": False, "error": result.error}
    return result


def _register_tool(mcp: FastMCP, tool: BaseTool) -> None:
    """Register a single Stack tool as an MCP tool."""
    tool_name = tool.name
    schema = tool.input_schema
    if callable(schema):
        schema = schema()

    async def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        return _call_tool_sync(tool, arguments)

    mcp.add_tool(handler, name=tool_name, description=tool.description)


def _register_all_tools(mcp: FastMCP) -> int:
    """Register all tools from the Stack 2.9 registry."""
    registry = get_registry()
    count = 0
    for tool in registry._tools.values():
        try:
            _register_tool(mcp, tool)
            count += 1
        except Exception as e:
            print(f"Failed to register tool {getattr(tool, 'name', 'unknown')}: {e}")
    return count


# Create the FastMCP server
mcp = FastMCP("Stack2.9")


def main():
    """Main entry point - register tools and run the server."""
    # Import all tools to ensure registration
    from src.tools import (
        agent_tool,
        ask_question,
        brief_tool,
        config_tool,
        file_edit,
        file_read,
        file_write,
        glob_tool,
        grep_tool,
        messaging,
        plan_mode,
        remote_trigger,
        scheduling,
        skill_tool,
        sleep_tool,
        synthetic_output,
        task_get,
        task_management,
        team_delete,
        team_tool,
        todo_tool,
        tool_discovery,
        web_fetch,
        web_search,
        worktree_tool,
    )

    # Register all tools from registry
    count = _register_all_tools(mcp)
    print(f"Registered {count} Stack 2.9 tools as MCP tools")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()