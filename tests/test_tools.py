"""Unit tests for Stack 2.9 tools."""

import datetime
import json
import os
import tempfile
import pytest

# Patch data dirs before importing tools
_temp_data_dir = tempfile.mkdtemp()


def _patch_data_dir(path: str):
    import src.tools.web_search as ws
    import src.tools.task_management as tm
    import src.tools.scheduling as sc
    ws.DATA_DIR = path
    ws.TASKS_FILE = os.path.join(path, "tasks.json")
    ws.CACHE_FILE = os.path.join(path, "web_search_cache.json")
    tm.DATA_DIR = path
    tm.TASKS_FILE = os.path.join(path, "tasks.json")
    sc.DATA_DIR = path
    sc.SCHEDULES_FILE = os.path.join(path, "schedules.json")


_patch_data_dir(_temp_data_dir)

from src.tools.base import BaseTool, ToolResult
from src.tools.registry import ToolRegistry, get_registry
from src.tools import task_management as tm_mod
from src.tools import scheduling as sc_mod


# ── base tool tests ───────────────────────────────────────────────────────────


def test_tool_result_dataclass():
    r = ToolResult(success=True, data={"foo": "bar"}, duration_seconds=1.5)
    assert r.success is True
    assert r.data == {"foo": "bar"}
    assert r.duration_seconds == 1.5


def test_base_tool_validate_input_returns_tuple():
    class DummyTool(BaseTool):
        name = "Dummy"
        description = ""

        def execute(self, input_data):
            return ToolResult(success=True)

    tool = DummyTool()
    valid, err = tool.validate_input({})
    assert valid is True
    assert err is None


def test_base_tool_call_wraps_validation():
    class AlwaysFail(BaseTool):
        name = "AlwaysFail"
        description = ""

        def validate_input(self, input_data):
            return False, "nope"

        def execute(self, input_data):
            return ToolResult(success=True)

    result = AlwaysFail().call({})
    assert result.success is False
    assert "nope" in result.error


# ── registry tests ─────────────────────────────────────────────────────────────


def test_registry_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_registry_register_and_get():
    class DummyTool(BaseTool):
        name = "TestTool"
        description = ""

        def execute(self, input_data):
            return ToolResult(success=True)

    registry = ToolRegistry()
    registry.register(DummyTool())
    assert registry.get("TestTool") is not None
    assert registry.get("NonExistent") is None


def test_registry_list():
    registry = ToolRegistry()
    names = registry.list()
    assert isinstance(names, list)


def test_registry_call_unknown_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.call("NoSuchTool", {})


# ── cron parsing tests ─────────────────────────────────────────────────────────


def test_parse_cron_valid():
    from src.tools.scheduling import parse_cron, cron_to_human

    for expr in ["* * * * *", "0 9 * * *", "*/5 * * * *", "30 14 1 * *"]:
        valid, err = parse_cron(expr)
        assert valid, f"Should be valid: {expr}, got {err}"


def test_parse_cron_invalid():
    from src.tools.scheduling import parse_cron

    for expr in ["* * *", "not a cron", "60 * * * *", "* * * * * *"]:
        valid, err = parse_cron(expr)
        assert not valid, f"Should be invalid: {expr}"


def test_cron_to_human():
    from src.tools.scheduling import cron_to_human

    assert cron_to_human("*/5 * * * *") == "every 5 minutes"
    assert cron_to_human("0 * * * *") == "every hour"


def test_next_cron_run():
    from datetime import datetime as dt
    from src.tools.scheduling import next_cron_run

    # "every minute" should fire within 2 minutes
    next_min = next_cron_run("* * * * *")
    assert next_min is not None
    assert next_min > dt.now()


# ── scheduling tool tests ──────────────────────────────────────────────────────


def test_cron_create_validate_invalid_cron():
    tool = sc_mod.CronCreateTool()
    valid, err = tool.validate_input({"cron": "not valid"})
    assert not valid
    assert "Invalid cron" in err


def test_cron_create_validate_missing_prompt():
    tool = sc_mod.CronCreateTool()
    valid, err = tool.validate_input({"cron": "0 9 * * *"})
    assert not valid
    assert "prompt" in err.lower()


def test_cron_create_success():
    tool = sc_mod.CronCreateTool()
    result = tool.call({"cron": "0 9 * * *", "prompt": "Good morning", "durable": True})
    assert result.success
    assert "id" in result.data


def test_cron_list_empty():
    tool = sc_mod.CronListTool()
    result = tool.call({})
    assert result.success
    assert result.data["total"] >= 0


def test_cron_delete_unknown():
    tool = sc_mod.CronDeleteTool()
    result = tool.call({"id": "does-not-exist"})
    assert not result.success


# ── task management tool tests ──────────────────────────────────────────────────


def test_task_create_success():
    tool = tm_mod.TaskCreateTool()
    result = tool.call({
        "subject": "Test task",
        "description": "A description",
        "priority": "high",
    })
    assert result.success
    assert "id" in result.data
    assert result.data["subject"] == "Test task"


def test_task_create_missing_subject():
    tool = tm_mod.TaskCreateTool()
    result = tool.call({})
    assert not result.success
    assert "subject" in result.error.lower()


def test_task_list():
    tool = tm_mod.TaskListTool()
    result = tool.call({})
    assert result.success
    assert "tasks" in result.data


def test_task_update_not_found():
    tool = tm_mod.TaskUpdateTool()
    result = tool.call({"id": "no-such-id"})
    assert not result.success


def test_task_delete_unknown():
    tool = tm_mod.TaskDeleteTool()
    result = tool.call({"id": "no-such-id"})
    assert not result.success


# ── web search tool tests ──────────────────────────────────────────────────────


def test_web_search_validate_empty_query():
    # Import inside to avoid import errors if ddgs not installed
    import importlib
    import src.tools.web_search as ws
    importlib.reload(ws)
    tool = ws.WebSearchTool()
    valid, err = tool.validate_input({"query": ""})
    assert not valid


def test_web_search_validate_too_short():
    import src.tools.web_search as ws
    tool = ws.WebSearchTool()
    valid, err = tool.validate_input({"query": "a"})
    assert not valid


def test_web_search_validate_both_domains():
    import src.tools.web_search as ws
    tool = ws.WebSearchTool()
    valid, err = tool.validate_input({
        "query": "test",
        "allowed_domains": ["example.com"],
        "blocked_domains": ["foo.com"],
    })
    assert not valid


def test_web_search_no_ddgs():
    import src.tools.web_search as ws
    # Force DDGS to None to test the import error path
    original = ws.DDGS
    ws.DDGS = None
    tool = ws.WebSearchTool()
    result = tool.execute({"query": "test"})
    ws.DDGS = original
    assert not result.success
    assert "not installed" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
