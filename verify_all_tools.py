
import asyncio
import os
from pathlib import Path
from tools import get_registry

async def verify_tool(name, args):
    print(f"Testing tool: {name} with args: {args}...", end=" ")
    try:
        registry = get_registry()
        # Now that ToolRegistry.call is async, we await it directly.
        result = await registry.call(name, args)

        if hasattr(result, 'success') and result.success:
            print("✅ SUCCESS")
            return True
        elif isinstance(result, dict) and result.get("success"):
            print("✅ SUCCESS")
            return True
        else:
            error = getattr(result, 'error', str(result)) if hasattr(result, 'error') else result.get('error', 'Unknown error') if isinstance(result, dict) else "Unexpected result format"
            print(f"❌ FAILED: {error}")
            return False
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return False

async def main():
    print("=== Stack 2.9 Comprehensive Tool Verification ===\n")

    # Setup temp environment
    test_dir = Path("tool_test_env")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test.txt"
    test_file.write_text("Hello Stack 2.9")

    registry = get_registry()
    all_tools = registry.list()

    # Define test cases for core tools to ensure high quality
    test_cases = {
        "file_read": {"path": str(test_file)},
        "file_write": {"path": str(test_dir / "write.txt"), "content": "test content"},
        "file_exists": {"path": str(test_file)},
        "TaskList": {},
        "TaskCreate": {"subject": "Verification Task", "description": "Testing tool", "priority": "low"},
        "glob": {"pattern": "*.txt", "path": str(test_dir)},
        "grep": {"pattern": "Hello", "path": str(test_file)},
        "web_search": {"query": "what is stack 2.9"},
        "web_fetch": {"url": "https://google.com"},
        "brief": {"content": "This is a test for the brief tool."},
        "Config": {"key": "test_key", "value": "test_val"},
        "TodoWrite": {"item": "Test todo item"},
    }

    success_count = 0
    total_tested = 0

    # 1. Test specific critical tools
    print("--- Testing Critical Tools ---")
    for name, args in test_cases.items():
        if name in all_tools:
            total_tested += 1
            if await verify_tool(name, args):
                success_count += 1

    # 2. Test a sample of others with empty args to check for crashes
    print("\n--- Testing General Registry Connectivity ---")
    for name in all_tools:
        if name not in test_cases:
            total_tested += 1
            # Try empty args just to see if it triggers a clean "missing param" error rather than a crash
            if await verify_tool(name, {}):
                success_count += 1

    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

    print(f"\n--- Final Result: {success_count}/{total_tested} ({ (success_count/total_tested)*100:.1f}%) tools responded without crashing ---")

if __name__ == "__main__":
    asyncio.run(main())
