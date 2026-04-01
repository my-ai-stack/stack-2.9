#!/usr/bin/env python3
"""
Generate high-quality synthetic training data using tool-specific templates.
Each tool gets realistic scenarios with proper parameters.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Comprehensive templates for all tools
TOOL_TEMPLATES = {
    "AgentTool": [
        {"user": "Create an agent to help with testing", "params": {"name": "test_agent", "goal": "Write unit tests"}, "result": "Agent 'test_agent' created"},
        {"user": "Spawn a teammate to handle frontend tasks", "params": {"name": "frontend_dev", "skills": ["react", "typescript"]}, "result": "Teammate 'frontend_dev' added to team"}
    ],
    "AskUserQuestionTool": [
        {"user": "Ask the user which framework they prefer", "params": {"question": "Which framework do you want to use: React, Vue, or Angular?"}, "result": "User responded: React"},
        {"user": "I need clarification on the requirements", "params": {"question": "Should the API be REST or GraphQL?"}, "result": "User answered: REST"}
    ],
    "BashTool": [
        {"user": "Run tests", "params": {"command": "npm test"}, "result": "PASS  src/index.test.js\nTests: 12 passed, 0 failed"},
        {"user": "Check git status", "params": {"command": "git status"}, "result": "On branch main\nModified: src/index.js"},
        {"user": "Install dependencies", "params": {"command": "pip install -r requirements.txt"}, "result": "Successfully installed Flask==2.0.0"}
    ],
    "BriefTool": [
        {"user": "Give me a brief on this project", "params": {"topic": "project_overview"}, "result": "This is a voice-enabled AI coding assistant built on Qwen2.5-Coder-32B"},
        {"user": "Brief me on the architecture", "params": {"topic": "architecture"}, "result": "Stack 2.9 uses vLLM for inference with LoRA fine-tuning"}
    ],
    "ConfigTool": [
        {"user": "Show configuration", "params": {"section": "model"}, "result": "model: Qwen2.5-Coder-32B\ncontext: 32768"},
        {"user": "Get settings", "params": {"key": "max_tokens"}, "result": "max_tokens: 4000"}
    ],
    "EnterPlanModeTool": [
        {"user": "Enter plan mode", "params": {"goal": "Refactor authentication module"}, "result": "Plan mode activated for: Refactor authentication module"},
    ],
    "EnterWorktreeTool": [
        {"user": "Create a worktree for feature branch", "params": {"branch": "feature/new-ui"}, "result": "Worktree created at .worktrees/feature_new_ui"},
    ],
    "ExitWorktreeTool": [
        {"user": "Exit current worktree", "params": {}, "result": "Exited worktree, returning to main"},
    ],
    "FileEditTool": [
        {"user": "Fix syntax error in main.py line 10", "params": {"file_path": "src/main.py", "old_string": "prin('hello')", "new_string": "print('hello')"}, "result": "File edited successfully"},
        {"user": "Add import statement to app.py", "params": {"file_path": "app.py", "insert_after": "import os", "new_string": "import sys"}, "result": "Import added"},
    ],
    "FileReadTool": [
        {"user": "Read package.json", "params": {"file_path": "package.json"}, "result": "{\n  \"name\": \"myapp\",\n  \"version\": \"1.0.0\"\n}"},
        {"user": "Show me README.md", "params": {"file_path": "README.md"}, "result": "# My Project\n\nDescription here..."},
    ],
    "FileWriteTool": [
        {"user": "Create a new file utils.py", "params": {"file_path": "src/utils.py", "content": "def helper():\n    return 'help'"}, "result": "File src/utils.py created"},
    ],
    "GlobTool": [
        {"user": "Find all Python files", "params": {"pattern": "**/*.py"}, "result": "Found 15 files:\nsrc/main.py\nsrc/utils.py\ntests/test_main.py"},
        {"user": "List test files", "params": {"pattern": "**/*.test.js"}, "result": "Found 3 files:\ntests/unit.test.js\ntests/integration.test.js"},
    ],
    "GrepTool": [
        {"user": "Search for 'TODO' comments", "params": {"pattern": "TODO"}, "result": "src/main.py:15:# TODO: implement error handling\nsrc/utils.py:42:# TODO: add validation"},
        {"user": "Find all console.log statements", "params": {"pattern": "console.log"}, "result": "src/index.js:10:console.log('debug')\nsrc/app.js:25:console.log('start')"},
    ],
    "LSPTool": [
        {"user": "Get definition of function calculateTotal", "params": {"file_path": "src/math.js", "line": 10, "character": 15}, "result": "Definition at src/math.js:20-30\nfunction calculateTotal(items) {...}"},
        {"user": "Find references of MyClass", "params": {"file_path": "src/MyClass.ts", "line": 5, "character": 10}, "result": "References:\n- src/main.ts:15\n- tests/MyClass.test.ts:8"},
    ],
    "ListMcpResourcesTool": [
        {"user": "List available MCP resources", "params": {}, "result": "Resources:\n- server1.file_system\n- server2.database\n- server3.api"},
    ],
    "MCPTool": [
        {"user": "Connect to GitHub MCP server", "params": {"server_name": "github"}, "result": "Connected to GitHub MCP server"},
    ],
    "NotebookEditTool": [
        {"user": "Add markdown cell to notebook", "params": {"notebook_path": "analysis.ipynb", "cell_index": 0, "cell_type": "markdown", "content": "# Analysis"}, "result": "Cell added"},
    ],
    "ReadMcpResourceTool": [
        {"user": "Read resource file from MCP", "params": {"uri": "mcp://server1/file.txt"}, "result": "File content here..."},
    ],
    "RemoteTriggerTool": [
        {"user": "Trigger deployment on staging", "params": {"target": "staging-server", "action": "deploy"}, "result": "Deployment triggered, build ID: 12345"},
    ],
    "SendMessageTool": [
        {"user": "Message the design team about the mockups", "params": {"to": "design-team", "subject": "Mockups ready", "body": "Please review the new mockups in Figma"}, "result": "Message sent to design-team"},
    ],
    "SkillTool": [
        {"user": "Run code review skill", "params": {"skill": "code-review", "inputs": {"code": "function foo() { return 1; }"}}, "result": "Review: Use strict equality, add JSDoc"},
    ],
    "TaskCreateTool": [
        {"user": "Create task: Fix login bug", "params": {"title": "Fix login bug", "description": "Users can't log in with valid credentials"}, "result": "Task #123 created"},
    ],
    "TaskGetTool": [
        {"user": "Get details of task 123", "params": {"task_id": 123}, "result": "Task #123: Fix login bug\nStatus: in progress\nAssignee: @dev"},
    ],
    "TaskListTool": [
        {"user": "List all tasks", "params": {"status": "in_progress"}, "result": "Tasks:\n#123 Fix login bug\n#124 Update docs"},
    ],
    "TaskStopTool": [
        {"user": "Stop task 123", "params": {"task_id": 123}, "result": "Task #123 stopped"},
    ],
    "TaskUpdateTool": [
        {"user": "Mark task 123 as complete", "params": {"task_id": 123, "status": "completed"}, "result": "Task #123 marked complete"},
    ],
    "TeamCreateTool": [
        {"user": "Create a team for backend devs", "params": {"team_name": "backend", "members": ["@alice", "@bob"]}, "result": "Team 'backend' created with 2 members"},
    ],
    "TeamDeleteTool": [
        {"user": "Delete the temp team", "params": {"team_name": "temp"}, "result": "Team 'temp' deleted"},
    ],
    "TodoWriteTool": [
        {"user": "Add todo: update documentation", "params": {"text": "Update API documentation"}, "result": "Todo added"},
    ],
    "ToolSearchTool": [
        {"user": "Search for file search tools", "params": {"query": "find files"}, "result": "Found: GlobTool, GrepTool"},
    ],
    "WebFetchTool": [
        {"user": "Fetch the OpenRouter API docs", "params": {"url": "https://openrouter.ai/docs"}, "result": "Fetched 15KB from openrouter.ai/docs"},
    ],
    "WebSearchTool": [
        {"user": "Search for 'Node.js best practices 2024'", "params": {"query": "Node.js best practices 2024"}, "result": "Top results:\n1. Node.js Design Patterns\n2. 2024 Node.js Best Practices Guide"},
    ]
}

# Realistic value pools
FILE_PATHS = ["src/main.py", "src/utils.js", "README.md", "package.json", "config.yaml",
              "Dockerfile", "requirements.txt", "tests/test_api.py", "src/components/Button.tsx",
              "lib/helpers.py", "app/models.py", "src/index.js", "Makefile"]
COMMANDS = ["npm test", "pytest", "make build", "git status", "ls -la",
            "python -m pip install -r requirements.txt", "docker ps", "npm run lint"]
PATTERNS = ["**/*.py", "**/*.js", "**/*.ts", "*.md", "**/*.test.js", "**/__tests__/**/*.py"]
QUESTIONS = ["Which framework should we use?", "Is this a bug or a feature?",
             "What's the priority of this task?", "Should we refactor or rewrite?"]

def fill_placeholders(text: str, params: Dict[str, Any]) -> str:
    """Replace all {key} placeholders in text with values from params."""
    for key, value in params.items():
        placeholder = f"{{{key}}}"
        if placeholder in text:
            text = text.replace(placeholder, str(value))
    return text

def generate_variations(template: Dict[str, Any], count: int, tool_name: str) -> List[Dict[str, Any]]:
    """Generate multiple realistic variations of a template."""
    examples = []

    for i in range(count):
        params = {}
        user_text = template["user"]
        result_text = template["result"]

        # Build params by scanning template for placeholders
        template_str = user_text + json.dumps(template.get("params", {})) + result_text

        # Determine what placeholders exist
        for key, default_val in template.get("params", {}).items():
            if isinstance(default_val, str) and ("{" + key + "}") in template_str:
                # This is a placeholder - generate dynamic value
                if key == "file_path":
                    params[key] = random.choice(FILE_PATHS)
                elif key == "command":
                    params[key] = random.choice(COMMANDS)
                elif key == "pattern":
                    params[key] = random.choice(PATTERNS)
                elif key == "question":
                    params[key] = random.choice(QUESTIONS)
                elif key == "topic":
                    params[key] = random.choice(["project_overview", "architecture", "team", "timeline"])
                elif key == "branch":
                    params[key] = random.choice(["feature/new-ui", "bugfix/login", "hotfix/security"])
                elif key == "name":
                    params[key] = random.choice(["test_agent", "code_reviewer", "deployment_bot", "test_suite"])
                elif key == "goal":
                    params[key] = random.choice(["Write unit tests", "Refactor legacy code", "Add documentation"])
                elif key == "to":
                    params[key] = random.choice(["team-backend", "design-team", "product-team"])
                elif key == "subject":
                    params[key] = random.choice(["Review needed", "Update available", "Deployment status"])
                elif key == "body":
                    params[key] = "Please review the attached documents."
                elif key == "server_name":
                    params[key] = random.choice(["github", "jira", "slack", "postgres"])
                elif key == "action":
                    params[key] = random.choice(["deploy", "restart", "backup", "migrate"])
                elif key == "target":
                    params[key] = random.choice(["staging", "production", "dev"])
                elif key == "skill":
                    params[key] = random.choice(["code-review", "security-scan", "performance-test"])
                elif key == "query":
                    params[key] = random.choice(["find files", "search code", "list todos"])
                elif key == "url":
                    params[key] = random.choice(["https://api.example.com/docs", "https://github.com/repo"])
                elif key == "task_id":
                    params[key] = random.randint(100, 999)
                elif key == "title":
                    params[key] = random.choice(["Fix bug", "Add feature", "Update docs", "Refactor code"])
                elif key == "description":
                    params[key] = "Detailed description of the task..."
                elif key == "team_name":
                    params[key] = random.choice(["backend", "frontend", "devops", "qa"])
                elif key == "members":
                    params[key] = ["@user1", "@user2"]
                elif key == "status":
                    params[key] = random.choice(["in_progress", "completed", "todo"])
                elif key == "text":
                    params[key] = "Sample todo item"
                elif key == "cell_index":
                    params[key] = random.randint(0, 10)
                elif key == "cell_type":
                    params[key] = random.choice(["code", "markdown"])
                elif key == "content":
                    params[key] = random.choice(["print('hello')", "# TODO", "import React", "def main():\n    pass"])
                elif key == "uri":
                    params[key] = "mcp://server/resource"
                elif key in ["line", "character"] and "file_path" in params:
                    params[key] = random.randint(1, 100) if key == "line" else random.randint(1, 50)
                else:
                    # Generic placeholder
                    params[key] = f"value_{random.randint(1, 100)}"
            else:
                # Not a placeholder, use the static value as-is
                params[key] = default_val

        # Fill user prompt with params
        user_prompt = fill_placeholders(user_text, params)
        user_prompt = user_prompt.replace("{tool}", tool_name)

        # Build tool input from params
        tool_input = {}
        for key, template_val in template.get("params", {}).items():
            if key in params:
                tool_input[key] = params[key]
            else:
                tool_input[key] = template_val

        # Fill result
        result = fill_placeholders(result_text, params)

        # Build conversation
        messages = [
            {"role": "user", "content": user_prompt},
            {
                "role": "assistant",
                "content": random.choice([
                    "I'll help with that.",
                    "Sure, let me do that.",
                    "Processing your request..."
                ]),
                "tool_use": {
                    "name": tool_name,
                    "input": tool_input
                }
            },
            {
                "role": "user",
                "content": "",
                "tool_result": {
                    "tool_use_id": "tool_1",
                    "content": result
                }
            },
            {"role": "assistant", "content": random.choice(["Done!", "Completed.", "All set!"])}
        ]

        examples.append({
            "messages": messages,
            "source": "synthetic_template",
            "tool": tool_name
        })

    return examples

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="training-data/scaled/template_synthetic.jsonl")
    parser.add_argument("--examples-per-tool", type=int, default=500)
    parser.add_argument("--tools-limit", type=int, default=None)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tools = list(TOOL_TEMPLATES.keys())
    if args.tools_limit:
        tools = tools[:args.tools_limit]

    print(f"🔧 Generating synthetic examples for {len(tools)} tools")
    print(f"   Target: {args.examples_per_tool} per tool")
    print(f"   Total expected: ~{len(tools) * args.examples_per_tool}")

    total_examples = 0
    with open(output_path, 'w') as f:
        for tool_name in tools:
            templates = TOOL_TEMPLATES[tool_name]
            ex_per_template = max(1, args.examples_per_tool // len(templates))

            for template in templates:
                examples = generate_variations(template, ex_per_template, tool_name)
                for ex in examples:
                    f.write(json.dumps(ex) + "\n")
                    total_examples += 1

            print(f"✅ {tool_name}: {ex_per_template * len(templates)} examples")

    print(f"\n✨ Generated {total_examples} synthetic examples")
    print(f"   Saved to: {output_path}")

    # Show sample
    print("\n📝 Sample example:")
    with open(output_path, 'r') as f:
        sample = json.loads(f.readline())
        print(f"   Tool: {sample['tool']}")
        print(f"   User: {sample['messages'][0]['content'][:60]}...")
        print(f"   Assistant uses: {sample['messages'][1]['tool_use']['name']}")

if __name__ == "__main__":
    main()