import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Mock MCP Client to demonstrate the protocol behavior
# In a real scenario, this would use an MCP SDK to communicate via JSON-RPC
class MockMCPClient:
    def __init__(self, server_config: Dict[str, Any]):
        self.server_name = server_config.get("name", "unknown")
        self.command = server_config.get("command")
        self.args = server_config.get("args", [])
        self.connected = False

        # Mock data representing what a server would provide
        self.mock_tools = {
            "get_weather": {
                "description": "Get current weather for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            },
            "read_file": {
                "description": "Read a file from the server's filesystem",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
                }
            }
        }
        self.mock_resources = {
            "file:///logs/main.log": "System started successfully",
            "file:///config/settings.json": '{"theme": "dark"}'
        }

    async def connect(self):
        print(f"Connecting to MCP server '{self.server_name}' using command: {self.command}...")
        await asyncio.sleep(0.5)  # Simulate connection delay
        self.connected = True
        print(f"Connected to {self.server_name}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        if not self.connected:
            raise ConnectionError("Client not connected to server")
        print(f"Listing tools for {self.server_name}...")
        return [
            {"name": name, **info}
            for name, info in self.mock_tools.items()
        ]

    async def list_resources(self) -> List[Dict[str, Any]]:
        if not self.connected:
            raise ConnectionError("Client not connected to server")
        print(f"Listing resources for {self.server_name}...")
        return [
            {"uri": uri, "description": f"Resource at {uri}"}
            for uri in self.mock_resources.keys()
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self.connected:
            raise ConnectionError("Client not connected to server")

        if tool_name not in self.mock_tools:
            return {"error": f"Tool {tool_name} not found"}

        print(f"Executing tool '{tool_name}' with args: {arguments}...")
        await asyncio.sleep(0.2) # Simulate processing

        # Mock responses
        if tool_name == "get_weather":
            location = arguments.get("location", "Unknown")
            return {"temperature": "22°C", "condition": "Sunny", "location": location}
        elif tool_name == "read_file":
            path = arguments.get("path", "")
            return {"content": f"Contents of {path}: Sample data"}

        return {"status": "success", "data": "Generic result"}

async def main():
    # 1. Define a mock MCP server configuration
    server_config = {
        "name": "weather-service",
        "command": "npx -y @modelcontextprotocol/server-weather",
        "args": ["--api-key", "mock-key"]
    }

    # 2. Initialize the MCP Client
    client = MockMCPClient(server_config)

    try:
        # Connect to the server
        await client.connect()

        # 3. List available tools
        tools = await client.list_tools()
        print("\nAvailable Tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

        # 4. List available resources
        resources = await client.list_resources()
        print("\nAvailable Resources:")
        for res in resources:
            print(f"- {res['uri']}")

        # 5. Execute a tool call
        print("\n--- Calling 'get_weather' tool ---")
        result = await client.call_tool("get_weather", {"location": "San Francisco"})
        print(f"Result: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nDemo completed.")

if __name__ == "__main__":
    asyncio.run(main())
