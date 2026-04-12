#!/usr/bin/env python3
"""Generate 15,000 synthetic tool-calling examples for Stack 2.9 training."""

import json
import random
import sys
import os
from pathlib import Path

# ── Tool definitions ─────────────────────────────────────────────────────────
TOOL_DEFS = [
    {"name": "Bash", "params": {"command": "string", "description": "string"}, "required": ["command"]},
    {"name": "FileRead", "params": {"path": "string"}, "required": ["path"]},
    {"name": "FileWrite", "params": {"path": "string", "content": "string"}, "required": ["path", "content"]},
    {"name": "Grep", "params": {"path": "string", "pattern": "string", "recursive": "boolean"}, "required": ["path", "pattern"]},
    {"name": "Glob", "params": {"pattern": "string", "path": "string"}, "required": ["pattern"]},
    {"name": "WebSearch", "params": {"query": "string"}, "required": ["query"]},
    {"name": "WebFetch", "params": {"url": "string"}, "required": ["url"]},
    {"name": "FileEdit", "params": {"path": "string", "oldText": "string", "newText": "string"}, "required": ["path", "oldText", "newText"]},
    {"name": "FileDelete", "params": {"path": "string"}, "required": ["path"]},
    {"name": "FileExists", "params": {"path": "string"}, "required": ["path"]},
    {"name": "TodoWrite", "params": {"content": "string", "priority": "string"}, "required": ["content"]},
    {"name": "TaskGet", "params": {}, "required": []},
    {"name": "AgentSpawn", "params": {"task": "string", "agent_id": "string"}, "required": ["task"]},
    {"name": "AgentList", "params": {}, "required": []},
    {"name": "Config", "params": {"key": "string", "value": "string"}, "required": ["key"]},
    {"name": "AskQuestion", "params": {"question": "string", "options": "array"}, "required": ["question"]},
    {"name": "Brief", "params": {"content": "string"}, "required": ["content"]},
    {"name": "PlanMode", "params": {"goal": "string"}, "required": ["goal"]},
    {"name": "SkillTool", "params": {"name": "string", "args": "object"}, "required": ["name"]},
    {"name": "SleepTool", "params": {"seconds": "number"}, "required": ["seconds"]},
    {"name": "RemoteTrigger", "params": {"endpoint": "string", "action": "string"}, "required": ["endpoint", "action"]},
    {"name": "Scheduling", "params": {"task": "string", "at": "string"}, "required": ["task"]},
    {"name": "SyntheticOutput", "params": {"template": "string", "count": "number"}, "required": ["template"]},
]


def make_tool_def(name, params, required):
    props = {}
    for p, t in params.items():
        prop = {"type": t}
        if p in required:
            props[p] = prop
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"Tool: {name}",
            "parameters": {
                "type": "object",
                "properties": {p: {"type": t} for p, t in params.items()},
                "required": required
            }
        }
    }


TOOL_DEFINITIONS = [make_tool_def(t["name"], t["params"], t["required"]) for t in TOOL_DEFS]

# ── Content pools ─────────────────────────────────────────────────────────────
FILE_PATHS = [
    "src/main.py", "src/utils.py", "src/config.py", "src/api.py",
    "tests/test_main.py", "tests/test_utils.py", "tests/conftest.py",
    "docs/README.md", "docs/API.md", "docs/DEPLOY.md",
    "package.json", "requirements.txt", "pyproject.toml", "Makefile",
    "scripts/build.sh", "scripts/deploy.sh", "scripts/cleanup.py",
    "src/models/user.py", "src/models/session.py", "src/routes/auth.py",
    "Dockerfile", "docker-compose.yml", ".env.example", "README.md",
]

BASH_COMMANDS = [
    "pip install -r requirements.txt", "python3 -m pytest tests/",
    "npm install && npm run build", "git status", "git log --oneline -5",
    "ls -la", "find . -name '*.py' | head -20", "docker build -t myapp .",
    "curl -s http://localhost:5000/health", "git diff --stat",
]

WEB_QUERIES = [
    "python async best practices 2025", "docker multi-stage build python",
    "react useEffect cleanup function", "git squash last N commits",
    "nginx reverse proxy websocket",
]

USER_REQUESTS = [
    "Show me the main entry point", "Run the tests to see if everything works",
    "Find all Python files in the project", "Check if Docker is installed",
    "Read the configuration file", "Install the dependencies",
    "Search for any TODO comments", "Show me the last 5 commits",
    "List all files in the src directory", "Check the API health endpoint",
    "Build and run the Docker container", "Delete the old log files",
    "Show me the project structure", "Find files matching *.config",
    "Check disk usage", "Show me the git diff", "Deploy the latest version",
]

# ── Example generators ────────────────────────────────────────────────────────

def build_tool_call(tool_name, args):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": f"call_{random.randint(10000, 99999)}",
            "type": "function",
            "function": {"name": tool_name, "arguments": json.dumps(args)}
        }]
    }


def build_tool_result(tool_call_id, result):
    return {"role": "tool", "tool_call_id": tool_call_id, "content": result}


def make_system():
    return {"role": "system", "content": "You are a helpful AI assistant that can use tools to help users solve problems. When you need to perform actions like reading files, running commands, searching the web, or searching code, use the appropriate tool."}


def gen_single_tool():
    tool = random.choice(TOOL_DEFS)
    tool_name = tool["name"]
    
    # Build args
    args = {}
    for p, t in tool["params"].items():
        if p in tool["required"]:
            if t == "string":
                if tool_name == "Bash": args[p] = random.choice(BASH_COMMANDS)
                elif tool_name == "FileRead" or tool_name == "FileExists": args[p] = random.choice(FILE_PATHS)
                elif tool_name == "Grep": args[p] = random.choice(["src/", "tests/"]) if p == "path" else random.choice(["TODO", "FIXME", "import"])
                elif tool_name == "Glob": args[p] = random.choice(["*.py", "*.json", "*.md"])
                elif tool_name == "WebSearch": args[p] = random.choice(WEB_QUERIES)
                elif tool_name == "WebFetch": args[p] = "https://example.com"
                elif tool_name == "FileEdit": args[p] = random.choice(["old text", "function main", "# TODO"]) if p in ["oldText", "newText"] else random.choice(FILE_PATHS)
                elif tool_name == "FileWrite": args[p] = "# new file content" if p == "content" else random.choice(FILE_PATHS)
                elif tool_name == "FileDelete": args[p] = random.choice(FILE_PATHS)
                elif tool_name == "TodoWrite": args[p] = random.choice(["Review PR", "Update docs", "Fix bug"]) if p == "content" else random.choice(["low", "medium", "high"])
                elif tool_name == "AgentSpawn": args[p] = random.choice(["Research task", "Write code"]) if p == "task" else random.choice(["claude", "coder"])
                elif tool_name == "Config": args[p] = random.choice(["debug", "log_level"]) if p == "key" else "true"
                elif tool_name == "AskQuestion": args[p] = random.choice(["Continue?", "Which option?"]) if p == "question" else ["A", "B", "C"]
                elif tool_name == "Brief": args[p] = "Longer content that should be summarized briefly."
                elif tool_name == "PlanMode": args[p] = random.choice(["Deploy app", "Fix bug"])
                elif tool_name == "SkillTool": args[p] = random.choice(["code_review", "doc_gen"]) if p == "name" else {}
                elif tool_name == "SleepTool": args[p] = random.randint(1, 5)
                elif tool_name == "RemoteTrigger": args[p] = "https://api.example.com/trigger" if p == "endpoint" else "deploy"
                elif tool_name == "Scheduling": args[p] = "Run backup" if p == "task" else "2026-04-12T00:00:00Z"
                elif tool_name == "SyntheticOutput": args[p] = "output_{{i}}" if p == "template" else 5
                else: args[p] = f"value for {p}"
            elif t == "boolean": args[p] = random.choice([True, False])
            elif t == "number": args[p] = random.randint(1, 10)
            elif t == "array": args[p] = ["opt1", "opt2"]
            elif t == "object": args[p] = {}
    
    messages = [make_system(), {"role": "user", "content": random.choice(USER_REQUESTS)}]
    tc = build_tool_call(tool_name, args)
    messages.append(tc)
    result = f"Tool {tool_name} executed successfully."
    messages.append(build_tool_result(tc["tool_calls"][0]["id"], result))
    messages.append({"role": "assistant", "content": f"Done! Here's the result:\n\n{result}"})
    
    return {"messages": messages, "tools": TOOL_DEFINITIONS}


def gen_two_step():
    tools = random.sample(TOOL_DEFS, 2)
    messages = [make_system(), {"role": "user", "content": random.choice(USER_REQUESTS)}]
    
    for tool in tools:
        args = {}
        for p, t in tool["params"].items():
            if p in tool["required"]:
                if t == "string":
                    if tool["name"] == "Glob": args[p] = "*.py"
                    elif tool["name"] == "FileRead": args[p] = "src/main.py"
                    elif tool["name"] == "Grep": args[p] = "src/" if p == "path" else "TODO"
                    elif tool["name"] == "Bash": args[p] = "ls -la"
                    else: args[p] = "value"
                elif t == "boolean": args[p] = False
        tc = build_tool_call(tool["name"], args)
        messages.append(tc)
        messages.append(build_tool_result(tc["tool_calls"][0]["id"], f"Result from {tool['name']}"))
    
    messages.append({"role": "assistant", "content": "Here's what I found after checking with two tools."})
    return {"messages": messages, "tools": TOOL_DEFINITIONS}


def gen_error_recovery():
    messages = [make_system(), {"role": "user", "content": random.choice(USER_REQUESTS)}]
    
    # Wrong tool call first
    bad_tool = random.choice(TOOL_DEFS)
    bad_args = {p: "fake/path" for p in bad_tool["required"] if p == "path"}
    if not bad_args: bad_args = {"command": "rm -rf /nonexistent"}
    tc1 = build_tool_call(bad_tool["name"], bad_args)
    messages.append(tc1)
    messages.append(build_tool_result(tc1["tool_calls"][0]["id"], f"Error: operation failed for {bad_tool['name']}"))
    
    # Correct tool
    good_tool = random.choice([t for t in TOOL_DEFS if t["name"] == "Bash"])
    tc2 = build_tool_call(good_tool["name"], {"command": "ls -la"})
    messages.append(tc2)
    messages.append(build_tool_result(tc2["tool_calls"][0]["id"], "Command succeeded. Here's the output:\n.\n..\nsrc\ntests\ndocs"))
    
    messages.append({"role": "assistant", "content": "I recovered from the error by trying a different approach. The directory listing shows the project structure."})
    return {"messages": messages, "tools": TOOL_DEFINITIONS}


def gen_complex():
    tools = random.sample(TOOL_DEFS, min(4, len(TOOL_DEFS)))
    messages = [make_system(), {"role": "user", "content": "I need to understand this project: check structure, read key files, run tests, check for issues."}]
    
    sequence = [
        ("Glob", {"pattern": "**/*.py"}),
        ("FileRead", {"path": "README.md"}),
        ("Bash", {"command": "python3 -m pytest --collect-only"}),
        ("Grep", {"path": ".", "pattern": "TODO|FIXME"}),
    ]
    
    for i, (name, args) in enumerate(sequence):
        tc = build_tool_call(name, args)
        messages.append(tc)
        messages.append(build_tool_result(tc["tool_calls"][0]["id"], f"Result {i+1} from {name}"))
    
    messages.append({"role": "assistant", "content": "Complete project overview:\n\n**Structure:** Python project with Flask\n**Tests:** Ready to run\n**Issues:** 3 TODOs found\n\nLet me know if you need more details!"})
    return {"messages": messages, "tools": TOOL_DEFINITIONS}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_PATH = "training/training-data-expanded/tool_examples_15k.jsonl"
    BATCH_SIZE = 1000
    TOTAL = 15000
    
    print(f"Generating {TOTAL:,} synthetic examples...")
    
    path = Path(OUTPUT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    generators = [gen_single_tool, gen_single_tool, gen_single_tool, gen_two_step, gen_error_recovery, gen_complex]
    
    with open(OUTPUT_PATH, "w") as f:
        for batch in range(TOTAL // BATCH_SIZE):
            for _ in range(BATCH_SIZE):
                ex = random.choice(generators)()
                f.write(json.dumps(ex) + "\n")
            print(f"  Batch {batch+1}/15 done — {(batch+1)*BATCH_SIZE:,}/{TOTAL:,}")
    
    with open(OUTPUT_PATH) as f:
        count = sum(1 for _ in f)
    print(f"\n✅ Done! Wrote {count:,} examples → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
