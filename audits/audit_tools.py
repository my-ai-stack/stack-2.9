#!/usr/bin/env python3
"""Comprehensive audit script for Stack 2.9 tools and skills.

This script:
1. Imports all tools and skills
2. Tests each tool with appropriate test input
3. Measures execution time
4. Reports pass/fail status
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure proper imports
sys.path.insert(0, '/Users/walidsobhi/stack-2.9/src')

# Import tools module (triggers registration)
import tools
from tools.base import BaseTool, ToolResult
from tools.registry import get_registry


# Test input definitions for each tool
TOOL_TEST_INPUTS: Dict[str, Dict[str, Any]] = {
    # File tools
    "file_read": {"path": "/Users/walidsobhi/stack-2.9/audit_tools.py"},
    "file_exists": {"path": "/Users/walidsobhi/stack-2.9/audit_tools.py"},
    "file_write": {"path": "/tmp/audit_test.txt", "content": "Test content from audit"},
    "file_edit": {
        "file_path": "/tmp/audit_test_edit.txt",
        "old_string": "old content",
        "new_string": "new content",
        "replace_all": False
    },
    "glob": {"pattern": "**/*.py", "path": "/Users/walidsobhi/stack-2.9/src"},
    "grep": {"pattern": "def ", "path": "/Users/walidsobhi/stack-2.9/src/tools"},
    # Web tools
    "WebSearch": {"query": "Python testing"},
    "WebFetch": {"url": "https://example.com", "prompt": "Extract the main heading"},
    # Task tools
    "task_create": {"subject": "Test task", "description": "Test description", "activeForm": "Testing"},
    "task_list": {},
    "task_update": {"taskId": "nonexistent", "status": "completed"},
    "task_get": {"taskId": "test"},
    # Todo tools
    "todo_list": {},
    "todo_add": {"content": "Test todo item"},
    "todo_complete": {"item_id": "test"},
    "todo_delete": {"item_id": "test"},
    # Config tools
    "config_get": {"key": "test.key"},
    "config_set": {"key": "test.key", "value": "test_value"},
    # Team tools
    "team_list": {},
    "team_create": {"team_name": "test_team", "members": ["user1"]},
    "team_delete": {"team_name": "test_team"},
    # Skill tools
    "skill_list": {},
    "skill_search": {"query": "test"},
    "skill_info": {"skill_name": "nonexistent"},
    "skill_execute": {"skill_name": "nonexistent"},
    "skill_chain": {"skills": []},
    # Scheduling
    "schedule_list": {},
    "schedule_add": {"title": "Test event", "time": "2025-01-01T10:00:00"},
    "schedule_delete": {"event_id": "test"},
    # Messaging
    "message_send": {"recipient": "test_user", "message": "Test message"},
    "message_list": {},
    # Brief tool
    "brief_generate": {"content": "This is test content for the brief tool."},
    # Ask question
    "ask_question": {"question": "What is 2+2?"},
    # Sleep tool
    "sleep": {"seconds": 0.1},
    # Plan mode
    "plan_create": {"prompt": "Create a test plan"},
    "plan_execute": {"plan_id": "test"},
    # MCP tool
    "mcp_list": {},
    "mcp_invoke": {"server": "test", "method": "test"},
    # Worktree tool
    "worktree_list": {},
    "worktree_create": {"name": "test-branch", "base": "main"},
    "worktree_remove": {"name": "test-branch"},
    # Remote trigger
    "remote_trigger_execute": {"target": "test-target", "action": "ping"},
    "remote_trigger_status": {"job_id": "test"},
    # Agent tool
    "agent_execute": {"task": "Test task", "context": {}},
    "agent_status": {"job_id": "test"},
    # Synthetic output
    "synthetic_generate": {"prompt": "Generate test data", "format": "json"},
    # Tool discovery
    "tool_discover": {"query": "file"},
    "tool_search": {"pattern": "file"},
    # Config
    "config_list": {},
    "config_delete": {"key": "test.key"},
}


def get_test_input(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get test input for a specific tool."""
    return TOOL_TEST_INPUTS.get(tool_name)


class AuditResult:
    """Result of auditing a single tool."""

    def __init__(
        self,
        tool_name: str,
        load_success: bool = False,
        execution_success: bool = False,
        response_time: float = 0.0,
        error: str = "",
        data: Any = None,
    ):
        self.tool_name = tool_name
        self.load_success = load_success
        self.execution_success = execution_success
        self.response_time = response_time
        self.error = error
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "load_success": self.load_success,
            "execution_success": self.execution_success,
            "response_time": self.response_time,
            "error": self.error,
            "data": self.data,
            "timestamp": self.timestamp,
        }


async def test_tool_async(tool: BaseTool, test_input: Dict[str, Any]) -> AuditResult:
    """Test a tool with async execution."""
    result = AuditResult(tool_name=tool.name, load_success=True)

    try:
        start_time = time.perf_counter()

        # Check if tool has async execute method
        if asyncio.iscoroutinefunction(tool.execute):
            result_data = await tool.execute(**test_input)
        else:
            result_data = tool.execute(**test_input)

        result.response_time = time.perf_counter() - start_time

        # Check if result is a ToolResult
        if isinstance(result_data, ToolResult):
            result.execution_success = result_data.success
            result.error = result_data.error or ""
            result.data = result_data.data
        else:
            # Handle non-ToolResult returns
            result.execution_success = True
            result.data = result_data

    except Exception as e:
        result.response_time = time.perf_counter() - start_time
        result.execution_success = False
        result.error = f"{type(e).__name__}: {str(e)}"
        result.data = traceback.format_exc()

    return result


def test_tool_sync(tool: BaseTool, test_input: Dict[str, Any]) -> AuditResult:
    """Test a tool with sync execution."""
    result = AuditResult(tool_name=tool.name, load_success=True)

    try:
        start_time = time.perf_counter()
        result_data = tool.execute(**test_input)
        result.response_time = time.perf_counter() - start_time

        # Check if result is a ToolResult
        if isinstance(result_data, ToolResult):
            result.execution_success = result_data.success
            result.error = result_data.error or ""
            result.data = result_data.data
        else:
            result.execution_success = True
            result.data = result_data

    except Exception as e:
        result.response_time = time.perf_counter() - start_time
        result.execution_success = False
        result.error = f"{type(e).__name__}: {str(e)}"
        result.data = traceback.format_exc()

    return result


def test_tool_call_method(tool: BaseTool, test_input: Dict[str, Any]) -> AuditResult:
    """Test a tool using the call method."""
    result = AuditResult(tool_name=tool.name, load_success=True)

    try:
        start_time = time.perf_counter()
        result_data = tool.call(test_input)
        result.response_time = time.perf_counter() - start_time

        if isinstance(result_data, ToolResult):
            result.execution_success = result_data.success
            result.error = result_data.error or ""
            result.data = result_data.data
        else:
            result.execution_success = True
            result.data = result_data

    except Exception as e:
        result.response_time = time.perf_counter() - start_time
        result.execution_success = False
        result.error = f"{type(e).__name__}: {str(e)}"
        result.data = traceback.format_exc()

    return result


async def audit_tool(tool: BaseTool) -> AuditResult:
    """Audit a single tool."""
    tool_name = tool.name

    # Get test input for this tool
    test_input = get_test_input(tool_name)
    if not test_input:
        # Use empty dict as default
        test_input = {}

    # Try different execution methods
    try:
        # First try the call method which handles timing and validation
        return test_tool_call_method(tool, test_input)
    except Exception as e:
        # If call method fails, try async execute
        if asyncio.iscoroutinefunction(tool.execute):
            try:
                return await test_tool_async(tool, test_input)
            except Exception as e2:
                return AuditResult(
                    tool_name=tool_name,
                    load_success=True,
                    execution_success=False,
                    error=f"Async execute failed: {type(e2).__name__}: {str(e2)}"
                )
        else:
            # Try sync execute
            try:
                return test_tool_sync(tool, test_input)
            except Exception as e2:
                return AuditResult(
                    tool_name=tool_name,
                    load_success=True,
                    execution_success=False,
                    error=f"Sync execute failed: {type(e2).__name__}: {str(e2)}"
                )


async def audit_tools() -> List[AuditResult]:
    """Audit all registered tools."""
    registry = get_registry()
    tool_names = registry.list()

    print(f"\n{'='*60}")
    print(f"STACK 2.9 TOOLS AUDIT")
    print(f"{'='*60}")
    print(f"Found {len(tool_names)} registered tools:")
    for name in sorted(tool_names):
        print(f"  - {name}")

    results = []

    for tool_name in tool_names:
        tool = registry.get(tool_name)
        if tool is None:
            print(f"\n[ERROR] Tool '{tool_name}' not found in registry")
            continue

        print(f"\n[TESTING] {tool_name}...", end=" ", flush=True)

        result = await audit_tool(tool)
        results.append(result)

        if result.execution_success:
            print(f"PASS ({result.response_time:.4f}s)")
        else:
            print(f"FAIL ({result.response_time:.4f}s)")
            if result.error:
                error_preview = result.error[:100] if len(result.error) > 100 else result.error
                print(f"       Error: {error_preview}")

    return results


def check_skills() -> Dict[str, Any]:
    """Check for available skills."""
    from tools.skill_tool import _discover_skills, SKILLS_FILE, SKILL_DIRS

    print(f"\n{'='*60}")
    print(f"SKILLS CHECK")
    print(f"{'='*60}")

    skills_info = {
        "skills_file": str(SKILLS_FILE),
        "skills_file_exists": SKILLS_FILE.exists(),
        "skill_dirs": [str(d) for d in SKILL_DIRS],
        "skill_dirs_exist": [d.exists() for d in SKILL_DIRS],
        "discovered_skills": [],
    }

    try:
        discovered = _discover_skills()
        skills_info["discovered_skills"] = discovered
        print(f"Discovered {len(discovered)} skills from directories")
        for skill in discovered:
            print(f"  - {skill['name']}: {skill.get('description', 'No description')[:50]}")
    except Exception as e:
        print(f"Error discovering skills: {e}")
        skills_info["error"] = str(e)

    return skills_info


def generate_report(results: List[AuditResult], skills_info: Dict[str, Any]) -> str:
    """Generate a comprehensive audit report."""

    # Calculate statistics
    total_tools = len(results)
    passed = sum(1 for r in results if r.execution_success)
    failed = total_tools - passed

    response_times = [r.response_time for r in results if r.response_time > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0

    report = f"""
================================================================================
                    STACK 2.9 COMPREHENSIVE AUDIT REPORT
================================================================================

Generated: {datetime.now().isoformat()}

--------------------------------------------------------------------------------
                              TOOLS SUMMARY
--------------------------------------------------------------------------------

Total Tools Tested:     {total_tools}
Passed:                {passed}
Failed:                {failed}
Pass Rate:              {passed/total_tools*100:.1f}%

--------------------------------------------------------------------------------
                           RESPONSE TIME STATISTICS
--------------------------------------------------------------------------------

Average Response Time:  {avg_response_time:.4f}s
Minimum Response Time: {min_response_time:.4f}s
Maximum Response Time: {max_response_time:.4f}s

--------------------------------------------------------------------------------
                           DETAILED RESULTS
--------------------------------------------------------------------------------
"""

    # Sort results by tool name
    sorted_results = sorted(results, key=lambda x: x.tool_name)

    for result in sorted_results:
        status = "PASS" if result.execution_success else "FAIL"
        report += f"""

Tool: {result.tool_name}
  Status:          {status}
  Load Success:    {result.load_success}
  Response Time:   {result.response_time:.4f}s
"""
        if result.error:
            error_lines = result.error.split('\n')
            report += f"  Error:          {error_lines[0]}\n"

    # Skills section
    report += f"""

--------------------------------------------------------------------------------
                             SKILLS SUMMARY
--------------------------------------------------------------------------------

Skills File:       {skills_info.get('skills_file', 'N/A')}
Skills File Exists: {skills_info.get('skills_file_exists', False)}

Skill Directories:
"""
    for i, (dir_exists, dir_path) in enumerate(zip(skills_info.get('skill_dirs_exist', []), skills_info.get('skill_dirs', []))):
        status = "EXISTS" if dir_exists else "MISSING"
        report += f"  [{status}] {dir_path}\n"

    discovered = skills_info.get('discovered_skills', [])
    report += f"""
Discovered Skills: {len(discovered)}
"""
    for skill in discovered:
        report += f"  - {skill['name']}: {skill.get('description', 'N/A')[:50]}\n"

    if skills_info.get('error'):
        report += f"""
Skills Error: {skills_info['error']}
"""

    # Final summary
    report += f"""

================================================================================
                           END OF AUDIT REPORT
================================================================================
"""

    return report


async def main():
    """Main audit function."""
    print("\nStarting Stack 2.9 Comprehensive Audit...")
    print(f"Working directory: /Users/walidsobhi/stack-2.9")

    # Audit all tools
    results = await audit_tools()

    # Check skills
    skills_info = check_skills()

    # Generate and print report
    report = generate_report(results, skills_info)
    print(report)

    # Save report to file
    report_path = "/Users/walidsobhi/stack-2.9/audit_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    # Save JSON results
    json_results = {
        "timestamp": datetime.now().isoformat(),
        "total_tools": len(results),
        "passed": sum(1 for r in results if r.execution_success),
        "failed": sum(1 for r in results if not r.execution_success),
        "tools": [r.to_dict() for r in results],
        "skills": skills_info,
    }
    json_path = "/Users/walidsobhi/stack-2.9/audit_results.json"
    with open(json_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON results saved to: {json_path}")

    # Return exit code based on failures
    failed_count = sum(1 for r in results if not r.execution_success)
    return failed_count


if __name__ == "__main__":
    failed = asyncio.run(main())
    sys.exit(0 if failed == 0 else 1)