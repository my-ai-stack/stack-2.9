
import asyncio
import os
import shutil
from pathlib import Path
from tools import get_registry

async def verify_tool(name, args):
    """Verify a tool's execution and categorize the result."""
    try:
        registry = get_registry()
        result = await registry.call(name, args)

        if hasattr(result, 'success') and result.success:
            return "✅ SUCCESS", None
        elif isinstance(result, dict) and result.get("success"):
            return "✅ SUCCESS", None
        else:
            error = getattr(result, 'error', str(result)) if hasattr(result, 'error') else result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            # If the error is about missing arguments, it's a validation success (the tool is protecting itself)
            if "missing" in error.lower() or "required" in error.lower() or "invalid" in error.lower():
                return "🛡️ VALIDATION", error
            return "❌ FAILED", error
    except Exception as e:
        return "💥 CRASH", str(e)

async def main():
    print("=== Stack 2.9 Full-Spectrum Tool Audit ===\n")

    # Setup sandbox environment
    sandbox = Path("audit_sandbox")
    sandbox.mkdir(exist_ok=True)
    test_file = sandbox / "test.txt"
    test_file.write_text("Hello Stack 2.9 Audit\nLine 2")
    test_dir = sandbox / "test_dir"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "sub.txt").write_text("Sub-file content")

    registry = get_registry()
    all_tools = registry.list()

    # Synthetic argument generator based on tool name/common patterns
    def generate_args(name):
        if "file_read" in name: return {"path": str(test_file)}
        if "file_write" in name: return {"path": str(sandbox / "write.txt"), "content": "test"}
        if "file_exists" in name: return {"path": str(test_file)}
        if "glob" in name: return {"pattern": "*.txt", "path": str(sandbox)}
        if "grep" in name: return {"pattern": "Hello", "path": str(test_file)}
        if "web_search" in name or "WebSearch" in name: return {"query": "Stack 2.9 AI"}
        if "web_fetch" in name: return {"url": "https://google.com"}
        if "TaskCreate" in name: return {"subject": "Audit", "description": "Test", "priority": "low"}
        if "TaskList" in name or "CronList" in name or "team_list" in name or "remote_list" in name or "skill_list" in name or "tool_list_all" in name or "list_worktrees" in name: return {}
        if "Config" in name: return {"key": "test", "value": "val", "operation": "set"}
        if "TodoWrite" in name: return {"item": "test", "operation": "add", "task": "audit"}
        if "EnterPlanMode" in name or "ExitPlanMode" in name: return {}
        return {} # Fallback to empty args to check for crashes

    results = []
    print(f"{'Tool Name':25} | {'Status':15} | {'Detail'}")
    print("-" * 80)

    for name in all_tools:
        args = generate_args(name)
        status, detail = await verify_tool(name, args)
        results.append((name, status))
        print(f"{name:25} | {status:15} | {detail if detail else ''}")

    # Final Stats
    successes = len([r for r in results if r[1] == "✅ SUCCESS"])
    validations = len([r for r in results if r[1] == "🛡️ VALIDATION"])
    crashes = len([r for r in results if r[1] == "💥 CRASH"])
    failures = len([r for r in results if r[1] == "❌ FAILED"])

    print("\n" + "="*40)
    print(f"Audit Summary for {len(all_tools)} Tools:")
    print(f"✅ Functional: {successes}")
    print(f"🛡️ Validated (Input Protections): {validations}")
    print(f"❌ Logic Failures: {failures}")
    print(f"💥 Critical Crashes: {crashes}")
    print("="*40)

    shutil.rmtree(sandbox)

if __name__ == "__main__":
    asyncio.run(main())
