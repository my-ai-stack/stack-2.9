#!/usr/bin/env python3
"""Async audit for Stack 2.9 tools - tests async tools properly."""

import asyncio
import sys
import time

sys.path.insert(0, '/Users/walidsobhi/stack-2.9/src')

from tools import tool_registry


def get_test_input(tool_name: str) -> dict:
    """Generate appropriate test input for each tool."""
    test_inputs = {
        "file_read": {"path": "/Users/walidsobhi/stack-2.9/README.md"},
        "file_write": {"path": "/tmp/test_audit.txt", "content": "test content"},
        "file_exists": {"path": "/Users/walidsobhi/stack-2.9/README.md"},
        "file_delete": {"path": "/tmp/test_audit.txt"},
        "file_edit": {"operation": "insert", "path": "/tmp/test_edit.txt", "content": "test"},
        "file_edit_insert": {"path": "/tmp/test_insert.txt", "content": "test", "offset": 0},
        "file_edit_delete": {"path": "/tmp/test_delete.txt", "start": 0, "end": 5},
        "file_edit_replace": {"path": "/tmp/test_replace.txt", "pattern": "old", "replacement": "new"},
        "glob": {"pattern": "*.py"},
        "glob_list": {"pattern": "*.md"},
        "grep": {"pattern": "def ", "path": "/Users/walidsobhi/stack-2.9"},
        "grep_count": {"pattern": "import", "path": "/Users/walidsobhi/stack-2.9/src"},
        "web_fetch": {"url": "https://example.com"},
        "web_fetch_meta": {"url": "https://example.com"},
        "WebSearch": {"query": "python async", "num_results": 3},
        "ask_question": {"question": "What is 2+2?"},
        "get_pending_questions": {},
        "answer_question": {"question_id": "1", "answer": "4"},
        "brief": {"content": "This is a test content for brief summarization."},
        "brief_summary": {"content": "Test content here."},
        "agent_spawn": {"agent_type": "general-purpose", "task": "test task"},
        "agent_status": {"agent_id": "test-123"},
        "agent_list": {},
        "sleep": {"seconds": 0.01},
        "wait_for": {"condition": "true", "timeout": 1},
        "skill_list": {},
        "skill_execute": {"skill_name": "test", "args": {}},
        "skill_info": {"skill_name": "test"},
        "skill_chain": {"skills": [], "initial_input": {}},
        "skill_search": {"query": "test"},
        "TaskCreate": {"subject": "Test Task", "description": "Test description"},
        "TaskList": {},
        "TaskUpdate": {"taskId": "1", "status": "completed"},
        "TaskDelete": {"taskId": "1"},
        "TodoWrite": {"subject": "Test", "content": "Test content"},
        "team_create": {"name": "test-team"},
        "team_delete": {"team_id": "1"},
        "team_disband": {"team_id": "1"},
        "team_list": {},
        "team_status": {"team_id": "1"},
        "team_assign": {"team_id": "1", "agent_id": "1"},
        "team_leave": {"team_id": "1"},
        "Config": {"operation": "get", "key": "test"},
        "CronCreate": {"expression": "* * * * *", "command": "echo test"},
        "CronList": {},
        "CronDelete": {"id": "1"},
        "EnterPlanMode": {},
        "ExitPlanMode": {},
        "message_send": {"channel": "test", "content": "test"},
        "message_list": {"channel": "test"},
        "message_channel": {"name": "test"},
        "message_template": {"template": "test", "vars": {}},
        "remote_add": {"name": "test", "url": "https://example.com"},
        "remote_list": {},
        "remote_remove": {"name": "test"},
        "remote_trigger": {"action": "test", "params": {}},
        "mcp_list_servers": {},
        "mcp_add_server": {"name": "test", "command": "test"},
        "mcp_call": {"server": "test", "tool_name": "test", "args": {}},
        "read_mcp_resource": {"resource_uri": "test://resource"},
        "tool_search": {"query": "file"},
        "tool_list_all": {},
        "tool_info": {"name": "file_read"},
        "tool_capabilities": {},
        "synthetic_output": {"content": "test"},
        "structure_data": {"content": "test", "format": "json"},
        "enter_worktree": {"path": "/tmp/test"},
        "exit_worktree": {},
        "list_worktrees": {},
    }
    return test_inputs.get(tool_name, {})


async def test_tool(tool_name: str) -> dict:
    """Test a single async tool."""
    tool = tool_registry.get(tool_name)
    if not tool:
        return {"tool": tool_name, "status": "FAIL", "error": "Tool not found"}

    test_input = get_test_input(tool_name)

    start_time = time.time()
    try:
        result = await tool.execute(**test_input)
        duration = time.time() - start_time
        return {
            "tool": tool_name,
            "status": "PASS",
            "duration": duration,
            "result": str(result)[:100] if result else "None"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "tool": tool_name,
            "status": "FAIL",
            "duration": duration,
            "error": str(e)[:100]
        }


async def main():
    """Run async audit on all tools."""
    print("=" * 60)
    print("STACK 2.9 ASYNC TOOLS AUDIT")
    print("=" * 60)

    tools = tool_registry.list()
    print(f"\nFound {len(tools)} registered tools\n")

    results = []
    passed = 0
    failed = 0

    for tool_name in tools:
        result = await test_tool(tool_name)
        results.append(result)

        status = result["status"]
        if status == "PASS":
            passed += 1
            print(f"✅ {tool_name}: PASS ({result['duration']:.3f}s)")
        else:
            failed += 1
            error = result.get('error', 'Unknown error')
            print(f"❌ {tool_name}: FAIL - {error[:50]}")

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tools: {len(tools)}")
    print(f"Passed: {passed} ({passed*100//len(tools)}%)")
    print(f"Failed: {failed} ({failed*100//len(tools)}%)")

    if failed > 0:
        print("\nFailed tools:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['tool']}: {r.get('error', 'Unknown')[:60]}")

    return results


if __name__ == "__main__":
    asyncio.run(main())