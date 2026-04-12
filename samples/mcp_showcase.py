import asyncio
import json
import httpx
from typing import Any, Dict, List

# ==============================================================================
# MCP Showcase: Demonstrating the Model Context Protocol (MCP)
# ==============================================================================
# This script demonstrates how an agent/client interacts with an MCP server.
#
# DATA FLOW ANALYSIS:
# 1. Initialization: The client sends an 'initialize' request to the server to
#    agree on protocol versions and capabilities.
# 2. Discovery: The client calls 'tools/list'. The server returns a list of
#    available tools, their descriptions, and their JSON-Schema input schemas.
# 3. Execution: The client calls 'tools/call' with a tool name and arguments.
#    - The MCP Server receives the JSON-RPC request.
#    - The Server maps the tool name to a local Python function (in this case,
#      one of the Stack 2.9 tools).
#    - The Server executes the function and captures the result.
#    - The Server wraps the result in a JSON-RPC response and sends it back.
# 4. Consumption: The agent receives the result and uses it to update its
#    internal state or respond to the user.
# ==============================================================================

class MockMCPClient:
    """
    A lightweight Python implementation of the MCPClient logic found in
    /Users/walidsobhi/stack-2.9/src/mcp/MCPClient.ts
    """
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.request_id = 0

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        print(f"--- [Client] Sending {method} ---")
        async with httpx.AsyncClient() as client:
            response = await client.post(self.server_url, json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"MCP Error: {data['error']}")
            return data.get("result")

    async def list_tools(self) -> List[Dict[str, Any]]:
        result = await self.send_request("tools/list")
        return result.get("tools", []) if result else []

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        return await self.send_request("tools/call", {"name": name, "arguments": args})

async def main():
    # Note: This assumes an MCP server is running at this URL.
    # In a real scenario, this would be the address of the mcp_server.py instance.
    SERVER_URL = "http://localhost:8000/mcp"

    client = MockMCPClient(SERVER_URL)

    try:
        # 1. Initialize Connection
        print("Step 1: Initializing connection...")
        await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp_showcase", "version": "1.0.0"}
        })
        print("Connected successfully!\n")

        # 2. List Tools
        print("Step 2: Discovering available tools...")
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool.get('description', 'No description')}")
        print("")

        # 3. Call a tool (Example: using 'file_read' to read a known file)
        if tools:
            # We'll try to use the first available tool as a demo
            target_tool = tools[0]['name']
            print(f"Step 3: Calling tool '{target_tool}'...")

            # Mock arguments - in a real case, these would be derived from the tool's schema
            args = {"path": "/Users/walidsobhi/stack-2.9/src/mcp/MCPClient.ts"}

            result = await client.call_tool(target_tool, args)
            print(f"Result from {target_tool}:")
            print(json.dumps(result, indent=2))
        else:
            print("No tools found to demonstrate.")

    except Exception as e:
        print(f"\n[!] Note: This demo requires a running MCP server at {SERVER_URL}")
        print(f"Error encountered: {e}")

if __name__ == "__main__":
    asyncio.run(main())
