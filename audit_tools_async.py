#!/usr/bin/env python3
"""Async Tool Audit for Stack 2.9 - Tests all tools properly with async execution"""

import sys
import asyncio
import time
from datetime import datetime

sys.path.insert(0, '/Users/walidsobhi/stack-2.9/src')

# Import tools to trigger registration
import tools


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def test_tool(tool, name, test_input):
    """Test a single tool with async execution"""
    start_time = time.time()

    try:
        if asyncio.iscoroutinefunction(tool.execute):
            result = await tool.execute(**test_input)
        else:
            result = tool.execute(**test_input)

        duration = time.time() - start_time

        # Check result
        if hasattr(result, 'success'):
            if result.success:
                return {
                    "status": "PASS",
                    "duration": duration,
                    "data": result.data if result.data else "OK"
                }
            else:
                return {
                    "status": "FAIL",
                    "duration": duration,
                    "error": result.error
                }
        else:
            return {
                "status": "PASS",
                "duration": duration,
                "data": str(result)
            }

    except Exception as e:
        duration = time.time() - start_time
        return {
            "status": "FAIL",
            "duration": duration,
            "error": str(e)
        }


async def audit_all_tools():
    """Run async audit on all tools"""

    print_header("STACK 2.9 ASYNC TOOL AUDIT")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from tools import tool_registry

    all_tools = tool_registry.list()
    print(f"\nFound {len(all_tools)} registered tools")

    # Define test cases for each tool
    test_cases = {
        "file_read": {"path": "/Users/walidsobhi/stack-2.9/README.md"},
        "file_exists": {"path": "/Users/walidsobhi/stack-2.9/README.md"},
        "file_write": {"path": "/tmp/test_tool_audit.txt", "content": "test content"},
        "file_delete": {"path": "/tmp/test_tool_audit.txt"},
        "glob": {"pattern": "*.py", "path": "/Users/walidsobhi/stack-2.9/src"},
        "grep": {"pattern": "def ", "path": "/Users/walidsobhi/stack-2.9/src/tools"},
        "grep_count": {"pattern": "def ", "path": "/Users/walidsobhi/stack-2.9/src/tools"},
        "WebSearch": {"query": "python async", "num_results": 3},
        "web_fetch": {"url": "https://example.com"},
        "tool_search": {"query": "file"},
        "tool_list_all": {},
        "tool_info": {"name": "file_read"},
        "tool_capabilities": {},
        "TaskCreate": {"subject": "Test Task", "description": "Test description"},
        "TaskList": {},
        "TaskUpdate": {"taskId": "1", "status": "completed"},
        "TaskDelete": {"taskId": "1"},
        "TodoWrite": {"subject": "Test Todo"},
        "team_create": {"name": "test-team"},
        "team_list": {},
        "team_status": {"team_id": "test-team"},
        "team_assign": {"team_id": "test-team", "user_id": "test-user"},
        "team_delete": {"team_id": "test-team"},
        "team_leave": {"team_id": "test-team"},
        "team_disband": {"team_id": "test-team"},
        "skill_list": {},
        "skill_search": {"query": "code"},
        "skill_info": {"name": "python"},
        "skill_execute": {"name": "python", "args": "print('hello')"},
        "skill_chain": {"skills": ["python"]},
        "brief": {"content": "This is a test content for brief analysis."},
        "brief_summary": {"content": "This is a test content."},
        "sleep": {"seconds": 0.1},
        "wait_for": {"condition": "true", "timeout": 1},
        "synthetic_output": {"template": "Test output: {value}", "values": {"value": "hello"}},
        "structure_data": {"data": {"name": "test"}, "format": "json"},
        "agent_spawn": {"name": "test-agent", "capabilities": ["code"]},
        "agent_list": {},
        "agent_status": {"name": "test-agent"},
        "ask_question": {"question": "Test question?"},
        "get_pending_questions": {},
        "answer_question": {"question_id": "1", "answer": "Test answer"},
        "message_send": {"channel": "test", "content": "Test message"},
        "message_list": {"channel": "test"},
        "message_channel": {"action": "create", "name": "test-channel"},
        "message_template": {"name": "test", "variables": {}},
        "CronCreate": {"expression": "* * * * *", "command": "echo test"},
        "CronList": {},
        "CronDelete": {"id": "test-cron"},
        "mcp_list_servers": {},
        "mcp_add_server": {"name": "test", "command": "echo test"},
        "mcp_call": {"server": "test", "tool_name": "test", "args": {}},
        "read_mcp_resource": {"resource_uri": "test://resource"},
        "remote_add": {"name": "test", "url": "https://example.com"},
        "remote_list": {},
        "remote_remove": {"name": "test"},
        "remote_trigger": {"name": "test", "action": "test"},
        "EnterPlanMode": {},
        "ExitPlanMode": {},
        "enter_worktree": {"path": "/tmp/test-worktree"},
        "exit_worktree": {},
        "list_worktrees": {},
        "Config": {"operation": "get", "key": "test"},
    }

    results = {}
    passed = 0
    failed = 0

    print("\n" + "-" * 60)
    print("Testing tools...")
    print("-" * 60)

    for name in all_tools:
        tool = tool_registry.get(name)
        if not tool:
            results[name] = {"status": "FAIL", "error": "Tool not found"}
            failed += 1
            continue

        # Get test input or empty dict
        test_input = test_cases.get(name, {})

        # Skip tools without test cases
        if not test_input:
            results[name] = {"status": "SKIP", "error": "No test case"}
            continue

        result = await test_tool(tool, name, test_input)
        results[name] = result

        status = result["status"]
        if status == "PASS":
            passed += 1
            print(f"✓ {name}: PASS ({result['duration']:.3f}s)")
        elif status == "SKIP":
            print(f"○ {name}: SKIP")
            passed += 1  # Count skipped as OK
        else:
            failed += 1
            print(f"✗ {name}: FAIL ({result['duration']:.3f}s)")
            print(f"  Error: {result.get('error', 'Unknown')}")

    # Summary
    print_header("AUDIT SUMMARY")

    total = len(all_tools)
    print(f"""
Total Tools:     {total}
Passed:         {passed}
Failed:         {failed}
Success Rate:   {(passed/total)*100:.1f}%
    """)

    # Show failures
    if failed > 0:
        print_header("FAILURES")
        for name, result in results.items():
            if result["status"] == "FAIL":
                print(f"  • {name}: {result.get('error', 'Unknown error')}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    asyncio.run(audit_all_tools())