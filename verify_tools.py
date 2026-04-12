
import asyncio
import os
from pathlib import Path
from tools import get_registry

async def verify_tool(name, args):
    print(f"Testing tool: {name} with args: {args}...", end=" ")
    try:
        registry = get_registry()
        # BaseTool.call() is now async
        result = await registry.call(name, args)
        if result.success:
            print("✅ SUCCESS")
            return True
        else:
            print(f"❌ FAILED: {result.error}")
            return False
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return False

async def main():
    print("=== Stack 2.9 Tool Integration Verification ===\n")

    # Setup temp file for testing
    test_file = Path("tool_verify_test.txt")
    test_file.write_text("Verification content")

    results = []

    # 1. Test File Operations
    results.append(await verify_tool("file_read", {"path": str(test_file)}))
    results.append(await verify_tool("file_write", {"path": str(test_file), "content": "Updated content"}))

    # 2. Test Task Management
    results.append(await verify_tool("TaskCreate", {"title": "Verify Tools", "description": "Test task", "priority": "high"}))
    results.append(await verify_tool("TaskList", {}))

    # 3. Test Registry
    registry = get_registry()
    tools = registry.list()
    print(f"Registry Check: Found {len(tools)} tools. Expected 69. {'✅' if len(tools) == 69 else '❌'}")

    # Cleanup
    if test_file.exists():
        test_file.unlink()

    success_rate = (sum(results) / len(results)) * 100 if results else 0
    print(f"\n--- Final Result: {success_rate:.1f}% tools verified successfully ---")

if __name__ == "__main__":
    asyncio.run(main())
