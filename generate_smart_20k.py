#!/usr/bin/env python3
"""Generate high-quality, complex tool-calling examples for Stack 2.9."""

import json
import random
import sys
from pathlib import Path

TOOLS = [
    {"name": "Bash", "params": {"command": "string"}, "required": ["command"]},
    {"name": "FileRead", "params": {"path": "string"}, "required": ["path"]},
    {"name": "FileWrite", "params": {"path": "string", "content": "string"}, "required": ["path", "content"]},
    {"name": "FileEdit", "params": {"path": "string", "oldText": "string", "newText": "string"}, "required": ["path", "oldText", "newText"]},
    {"name": "Grep", "params": {"path": "string", "pattern": "string", "recursive": "boolean"}, "required": ["path", "pattern"]},
    {"name": "Glob", "params": {"pattern": "string", "path": "string"}, "required": ["pattern"]},
    {"name": "WebSearch", "params": {"query": "string"}, "required": ["query"]},
    {"name": "WebFetch", "params": {"url": "string"}, "required": ["url"]},
    {"name": "FileExists", "params": {"path": "string"}, "required": ["path"]},
    {"name": "FileDelete", "params": {"path": "string"}, "required": ["path"]},
    {"name": "TodoWrite", "params": {"content": "string", "priority": "string"}, "required": ["content"]},
    {"name": "AgentSpawn", "params": {"task": "string", "agent_id": "string"}, "required": ["task"]},
    {"name": "AgentList", "params": {}, "required": []},
    {"name": "AgentStatus", "params": {"agent_id": "string"}, "required": ["agent_id"]},
    {"name": "Config", "params": {"key": "string", "value": "string"}, "required": ["key"]},
    {"name": "AskQuestion", "params": {"question": "string", "options": "array"}, "required": ["question"]},
    {"name": "Brief", "params": {"content": "string"}, "required": ["content"]},
    {"name": "PlanMode", "params": {"goal": "string"}, "required": ["goal"]},
    {"name": "SkillTool", "params": {"name": "string", "args": "object"}, "required": ["name"]},
    {"name": "SleepTool", "params": {"seconds": "number"}, "required": ["seconds"]},
    {"name": "RemoteTrigger", "params": {"endpoint": "string", "action": "string"}, "required": ["endpoint", "action"]},
    {"name": "Scheduling", "params": {"task": "string", "at": "string"}, "required": ["task"]},
    {"name": "SyntheticOutput", "params": {"template": "string", "count": "number"}, "required": ["template"]},
    {"name": "TaskGet", "params": {}, "required": []},
    {"name": "TaskManagement", "params": {"action": "string", "task_id": "string"}, "required": ["action"]},
    {"name": "BriefSummary", "params": {"content": "string"}, "required": ["content"]},
]

TOOL_DEFS = [
    {"type": "function", "function": {"name": t["name"], "description": f"Tool: {t['name']}", "parameters": {"type": "object", "properties": {p: {"type": pt} for p, pt in t["params"].items()}, "required": t["required"]}}}
    for t in TOOLS
]

PROJECTS = {
    "flask_api": {
        "files": {
            "app.py": "from flask import Flask, jsonify, request\nfrom functools import wraps\nimport os\n\napp = Flask(__name__)\napp.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')\n\ndef require_auth(f):\n    @wraps(f)\n    def decorated(*args, **kwargs):\n        token = request.headers.get('Authorization', '')\n        if not token.startswith('Bearer '):\n            return jsonify({'error': 'Unauthorized'}), 401\n        return f(*args, **kwargs)\n    return decorated\n\n@app.route('/api/users', methods=['GET'])\n@require_auth\ndef get_users():\n    return jsonify({'users': []})\n\n@app.route('/api/users', methods=['POST'])\n@require_auth\ndef create_user():\n    data = request.get_json()\n    return jsonify({'id': 1, **data}), 201",
            "requirements.txt": "flask>=2.0\nflask-cors>=3.0\npsycopg2-binary>=2.9\ngunicorn>=20.0",
            "tests/test_app.py": "import pytest\nfrom app import app\n\n@pytest.fixture\ndef client():\n    app.config['TESTING'] = True\n    with app.test_client() as c:\n        yield c\n\ndef test_get_users(client):\n    resp = client.get('/api/users', headers={'Authorization': 'Bearer token'})\n    assert resp.status_code == 200",
            ".env.example": "SECRET_KEY=change-me-in-production\nDATABASE_URL=postgresql://localhost/mydb",
            "README.md": "# Flask API\n\nA REST API built with Flask.\n\n## Setup\n\n```bash\npip install -r requirements.txt\npython app.py\n```"
        }
    },
    "react_app": {
        "files": {
            "package.json": '{\n  "name": "my-react-app",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build",\n    "test": "vitest"\n  },\n  "dependencies": {\n    "react": "^18.2.0",\n    "axios": "^1.4.0"\n  }\n}',
            "src/App.jsx": "import { useState, useEffect } from 'react'\n\nexport default function App() {\n  const [data, setData] = useState(null)\n  useEffect(() => {\n    fetch('/api/data').then(r => r.json()).then(setData)\n  }, [])\n  return <div>{data ? data.message : 'Loading...'}</div>\n}",
            "vite.config.js": 'export default {\n  plugins: [],\n  server: { port: 3000 }\n}',
            "src/App.css": ".app { padding: 20px; }"
        }
    },
    "python_cli": {
        "files": {
            "cli.py": "#!/usr/bin/env python3\nimport argparse\nimport sys\n\ndef main():\n    parser = argparse.ArgumentParser(description='CLI tool')\n    parser.add_argument('--name', default='World', help='Name to greet')\n    parser.add_argument('--verbose', action='store_true', help='Verbose output')\n    args = parser.parse_args()\n    print(f'Hello, {args.name}!')\n    if args.verbose:\n        print(f'Python: {sys.version}')\n    return 0\n\nif __name__ == '__main__':\n    sys.exit(main())",
            "setup.py": 'from setuptools import setup\nsetup(\n    name="mycli",\n    version="1.0.0",\n    py_modules=["cli"],\n    entry_points={"console_scripts": ["mycli=cli:main"]}\n)',
            "README.md": "# My CLI Tool\n\nA Python CLI for doing things."
        }
    }
}

PROJECT_NAMES = list(PROJECTS.keys())

DEBUGGING_SCENARIOS = [
    {
        "error": "ModuleNotFoundError: No module named flask",
        "investigation": [
            ("Bash", {"command": "pip list | grep -i flask"}),
            ("FileRead", {"path": "requirements.txt"}),
            ("Bash", {"command": "which python3 && python3 --version"}),
        ],
        "diagnosis": "Flask is installed in a different Python environment than the one running the script",
        "fix": "Use python3 -m pip install flask or check which python pip points to"
    },
    {
        "error": "React useEffect runs twice in development",
        "investigation": [
            ("FileRead", {"path": "src/App.jsx"}),
            ("Grep", {"path": "src", "pattern": "useEffect", "recursive": True}),
        ],
        "diagnosis": "React 18 StrictMode intentionally double-invokes effects in development to detect side effects",
        "fix": "This is expected behavior. Add cleanup function if you need to cancel subscriptions."
    },
    {
        "error": "pytest: ModuleNotFoundError for local module",
        "investigation": [
            ("Bash", {"command": "ls -la"}),
            ("FileRead", {"path": "tests/test_app.py"}),
            ("Bash", {"command": "python3 -m pytest tests/test_app.py -v"}),
        ],
        "diagnosis": "The test file imports from app but PYTHONPATH doesnt include the project root",
        "fix": "Set PYTHONPATH=. before running pytest, or add conftest.py with sys.path.insert"
    },
    {
        "error": "Vite CORS error in production",
        "investigation": [
            ("FileRead", {"path": "vite.config.js"}),
            ("Grep", {"path": ".", "pattern": "cors", "recursive": False}),
        ],
        "diagnosis": "Vite dev server has CORS enabled by default but production build does not set CORS headers",
        "fix": "Add a middleware in the backend or configure the proxy in vite.config.js"
    },
    {
        "error": "GitHub Actions: pytest not found",
        "investigation": [
            ("FileRead", {"path": ".github/workflows/ci.yml"}),
            ("Bash", {"command": "cat requirements.txt"}),
        ],
        "diagnosis": "The CI workflow installs dependencies but pytest might be in a separate dev-requirements.txt",
        "fix": "Split requirements into requirements.txt (prod) and requirements-dev.txt (dev)"
    },
]

_call_id = 10000

def next_id():
    global _call_id
    _call_id += 1
    return f"call_{_call_id}"

def make_system():
    return {"role": "system", "content": "You are a Stack 2.9, an expert AI coding assistant with tools. You help users debug, build, and understand code. Always think step by step."}

def make_user(text):
    return {"role": "user", "content": text}

def make_tool_call(name, args):
    return {"role": "assistant", "content": None, "tool_calls": [{"id": next_id(), "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}

def make_tool_result(tool_call_id, content):
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

def make_final(content):
    return {"role": "assistant", "content": content}

def gen_debugging():
    scenario = random.choice(DEBUGGING_SCENARIOS)
    project = random.choice(PROJECT_NAMES)
    project_files = PROJECTS[project]["files"]

    messages = [make_system(), make_user(f"I am getting this error: {scenario['error']} in my {project} project")]

    results = []
    for tool_name, args in scenario["investigation"]:
        if tool_name == "Bash":
            cmd = args["command"]
            if "pip list" in cmd:
                results.append("flask==2.3.0\nflask-cors==4.0.0")
            elif "which python" in cmd:
                results.append("/usr/bin/python3\nPython 3.11.0")
            elif "pytest" in cmd:
                results.append(f"ERROR: {scenario['error']}")
            else:
                results.append("expected output")
        elif tool_name == "FileRead":
            results.append(project_files.get(args["path"], f"Contents of {args['path']}"))
        else:
            results.append("result")

    for i, (tool_name, args) in enumerate(scenario["investigation"]):
        tc = make_tool_call(tool_name, args)
        messages.append(tc)
        messages.append(make_tool_result(tc["tool_calls"][0]["id"], results[i]))

    messages.append(make_final(f"I identified the issue: {scenario['diagnosis']}\n\nFix: {scenario['fix']}\n\nLet me know if you need me to implement the fix!"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_file_navigation():
    project = random.choice(PROJECT_NAMES)
    project_files = PROJECTS[project]["files"]
    main_file = list(project_files.keys())[0]

    messages = [make_system(), make_user(f"Help me understand the {project} project structure")]
    tc1 = make_tool_call("Glob", {"pattern": "**/*", "path": "."})
    messages.append(tc1)
    messages.append(make_tool_result(tc1["tool_calls"][0]["id"], "\n".join(f"- {f}" for f in project_files.keys())))
    tc2 = make_tool_call("FileRead", {"path": main_file})
    messages.append(tc2)
    messages.append(make_tool_result(tc2["tool_calls"][0]["id"], project_files[main_file]))

    messages.append(make_final(f"I explored the {project} project. Here is the structure:\n\n**Files:** {', '.join(project_files.keys())}\n\n**Main entry:** {main_file}\n\nThe project uses a standard structure. Want me to dive deeper into any specific file?"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_error_recovery():
    project = random.choice(PROJECT_NAMES)
    errors = [
        ("rm -rf node_modules", "Permission denied"),
        ("pip install flask==99.0.0", "ERROR: No matching distribution for flask==99.0.0"),
        ("python3 app.py", "ImportError: cannot import name Flask from flask"),
        ("git push origin main", "error: src refspec main does not match any"),
    ]
    cmd, error = random.choice(errors)

    messages = [make_system(), make_user(f"I ran `{cmd}` and got: {error}")]
    tc1 = make_tool_call("Bash", {"command": cmd})
    messages.append(tc1)
    messages.append(make_tool_result(tc1["tool_calls"][0]["id"], error))
    tc2 = make_tool_call("Bash", {"command": "git status"})
    messages.append(tc2)
    messages.append(make_tool_result(tc2["tool_calls"][0]["id"], "expected output"))

    messages.append(make_final(f"That command failed because the version does not exist or there is an environment issue.\n\n1. Check what is currently installed: pip list\n2. Use a valid version or install without specifying one\n3. Make sure you are in the right virtual environment\n\nWould you like me to run the correct command?"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_multi_step_build():
    project = random.choice(PROJECT_NAMES)
    steps = [
        ("FileRead", {"path": "requirements.txt"}),
        ("Bash", {"command": "pip install -r requirements.txt"}),
        ("Bash", {"command": "python3 -m pytest tests/ -v"}),
        ("Bash", {"command": "git add . && git commit -m Update"}),
    ]
    results = [
        "flask>=2.0\nflask-cors>=3.0\npsycopg2-binary>=2.9",
        "Successfully installed flask-2.3.0",
        "tests/test_app.py::test_get_users PASSED\n1 passed",
        "[main abc1234] Update\n 1 file changed",
    ]

    messages = [make_system(), make_user(f"Can you build and deploy the {project} project?")]
    for i, (tool_name, args) in enumerate(steps):
        tc = make_tool_call(tool_name, args)
        messages.append(tc)
        messages.append(make_tool_result(tc["tool_calls"][0]["id"], results[i]))

    messages.append(make_final(f"Build complete!\n\n✅ Dependencies installed\n✅ Tests passing\n✅ Code committed\n\nThe project is ready. Let me know if you want to set up CI/CD!"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_code_review():
    project = random.choice(PROJECT_NAMES)
    project_files = PROJECTS[project]["files"]
    main_file = list(project_files.keys())[0]

    messages = [make_system(), make_user(f"Review the {project} codebase for security issues and bugs")]
    tc = make_tool_call("FileRead", {"path": main_file})
    messages.append(tc)
    messages.append(make_tool_result(tc["tool_calls"][0]["id"], project_files[main_file]))
    tc2 = make_tool_call("Grep", {"path": ".", "pattern": "TODO|FIXME|secret|password|api.key", "recursive": True})
    messages.append(tc2)
    messages.append(make_tool_result(tc2["tool_calls"][0]["id"], "Found:\n- Line with hardcoded secret key"))

    messages.append(make_final(f"Code review for {project}:\n\n**Security Issues:**\n🔴 HIGH: SECRET_KEY is hardcoded as dev-key - use environment variable\n🟡 MEDIUM: No input validation on POST endpoint\n\n**Best Practices:**\n✅ Uses decorators for auth\n✅ Proper HTTP status codes\n\n**Recommendations:**\n1. Move SECRET_KEY to os.environ.get\n2. Add input validation\n3. Add rate limiting\n\nWould you like me to implement any fixes?"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_test_debug():
    messages = [
        make_system(),
        make_user("My test is failing with AssertionError: expected 200 got 401"),
        make_tool_call("FileRead", {"path": "tests/test_app.py"}),
    ]
    tc1 = messages[-1]["tool_calls"][0]["id"]
    messages.append(make_tool_result(tc1, "def test_get_users(client):\n    resp = client.get('/api/users')\n    assert resp.status_code == 200"))
    messages.append(make_tool_call("FileRead", {"path": "app.py"}))
    tc2 = messages[-1]["tool_calls"][0]["id"]
    messages.append(make_tool_result(tc2, "@app.route('/api/users')\n@require_auth\ndef get_users():\n    return jsonify({'users': []})"))

    messages.append(make_final("Found the issue! The test does not send an Authorization header but the endpoint requires @require_auth.\n\n**Fix:**\nAdd headers={'Authorization': 'Bearer test-token'} to the test client request.\n\nThe code is correct - the test just needs to authenticate. Want me to show the fixed test?"))
    return {"messages": messages, "tools": TOOL_DEFS}

def gen_refactoring():
    project = random.choice(PROJECT_NAMES)
    messages = [
        make_system(),
        make_user(f"The app.py in {project} is getting too big. Help me refactor it into a proper structure."),
        make_tool_call("FileRead", {"path": "app.py"}),
    ]
    tc = messages[-1]["tool_calls"][0]["id"]
    messages.append(make_tool_result(tc, "# Flask app with routes, models, decorators..."))
    messages.append(make_tool_call("Bash", {"command": "ls -la"}))
    tc2 = messages[-1]["tool_calls"][0]["id"]
    messages.append(make_tool_result(tc2, "app.py requirements.txt tests/"))

    messages.append(make_final(f"Here is a clean architecture for {project}:\n\nproject/\n├── app/\n│   ├── __init__.py\n│   ├── routes/users.py\n│   ├── models/user.py\n│   └── utils/auth.py\n├── tests/\n├── requirements.txt\n└── run.py\n\n**Benefits:**\n- Separation of concerns\n- Easier to test\n- Team-friendly\n- Scalable\n\nWant me to create the new structure and move the code?"))
    return {"messages": messages, "tools": TOOL_DEFS}

GENERATORS = [
    gen_debugging,
    gen_file_navigation,
    gen_error_recovery,
    gen_multi_step_build,
    gen_code_review,
    gen_test_debug,
    gen_refactoring,
]

def main():
    OUTPUT_PATH = "training/training-data-expanded/tool_examples_smart_20k.jsonl"
    BATCH_SIZE = 500
    TOTAL = 20000

    print(f"Generating {TOTAL:,} SMART examples...")
    print("Types: debugging, code review, refactoring, multi-step build, error recovery, navigation")

    with open(OUTPUT_PATH, "w") as f:
        for batch in range(TOTAL // BATCH_SIZE):
            for _ in range(BATCH_SIZE):
                ex = random.choice(GENERATORS)()
                f.write(json.dumps(ex) + "\n")
            print(f"  Batch {batch+1}/{TOTAL//BATCH_SIZE} - {(batch+1)*BATCH_SIZE:,}/{TOTAL:,}")

    with open(OUTPUT_PATH) as f:
        count = sum(1 for _ in f)
    print(f"\nDone! Wrote {count:,} examples -> {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
