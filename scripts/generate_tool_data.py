#!/usr/bin/env python3
"""
Synthetic Tool-Calling Training Data Generator for Stack 2.9
Generates training examples in Qwen2.5-Coder format with tool_calls.
"""

import json
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# ============================================================================
# Tool Definitions (Qwen2.5-Coder format)
# ============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute bash commands in the terminal. Use for running shell commands, scripts, git operations, package managers, and system commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "FileRead",
            "description": "Read the contents of a file from the filesystem. Use for viewing source code, configuration files, documentation, or any text-based files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (1-indexed)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "FileWrite",
            "description": "Create or overwrite a file with content. Use for creating new files, updating existing files, or writing code, configuration, or documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where the file should be created or written"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Append to existing file instead of overwriting (default: false)"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "WebSearch",
            "description": "Search the web for information. Use for finding documentation, looking up error messages, researching libraries, or getting up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Grep",
            "description": "Search for patterns in files. Use for finding specific code, function definitions, imports, TODO comments, error patterns, or any text across the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The search pattern or regex to match"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file path to search in (default: current directory)"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search recursively in subdirectories (default: true)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to filter results (e.g., '*.py', '*.js')"
                    }
                },
                "required": ["pattern"]
            }
        }
    }
]

# ============================================================================
# Template Data for Generation
# ============================================================================

FILE_PATHS = [
    "src/main.py", "src/utils.py", "src/config.py", "src/models.py",
    "src/api.py", "src/handlers.py", "src/middleware.py",
    "tests/test_main.py", "tests/test_utils.py", "tests/conftest.py",
    "README.md", "LICENSE", "package.json", "requirements.txt",
    "config.yaml", "config.json", ".env.example",
    "src/components/Button.tsx", "src/components/Header.jsx",
    "src/styles.css", "src/index.js", "src/app.js",
    "docs/API.md", "docs/ARCHITECTURE.md", "docs/CONTRIBUTING.md",
    "scripts/setup.sh", "scripts/deploy.py", "Makefile"
]

CODE_SNIPPETS = {
    "python": [
        "def hello():\n    print('Hello, World!')",
        "class MyClass:\n    def __init__(self):\n        self.value = 42",
        "import os\nos.path.join('a', 'b')",
        "async def fetch_data():\n    async with aiohttp.ClientSession() as session:\n        return await session.get(url)",
    ],
    "javascript": [
        "const fetch = require('node-fetch');\nconst data = await fetch(url);",
        "function handleClick() {\n  setCount(count + 1);\n}",
        "export default function App() {\n  return <div>Hello</div>;\n}",
        "const [state, setState] = useState(null);",
    ],
    "bash": [
        "npm install",
        "git status",
        "pytest -v",
        "python -m pytest tests/",
        "make build",
        "docker build -t myapp .",
        "ls -la",
        "curl -X GET https://api.example.com",
    ]
}

WEB_SEARCH_QUERIES = [
    "python async await best practices",
    "javascript array methods map filter reduce",
    "TypeScript generics tutorial",
    "React hooks useEffect dependency array",
    "Node.js error handling best practices",
    "Docker vs Kubernetes differences",
    "Git rebase vs merge",
    "SQL join types explained",
    "REST API design principles",
    "Python list comprehension examples",
    "JavaScript promise async await",
    "CSS flexbox vs grid",
    "MongoDB vs PostgreSQL",
    "AWS Lambda cold start optimization",
    "Docker compose tutorial",
]

GREP_PATTERNS = [
    ("TODO", "*.py", "Find TODO comments in Python files"),
    ("function ", "*.js", "Find function definitions in JS"),
    ("import ", "*.py", "Find imports in Python"),
    ("class ", "*.ts", "Find class definitions in TypeScript"),
    ("def ", "*.py", "Find function definitions in Python"),
    ("const ", "*.js", "Find const declarations in JS"),
    ("interface ", "*.ts", "Find interface definitions"),
    ("#pragma", "*.c", "Find pragma directives in C"),
    ("SELECT ", "*.sql", "Find SQL queries"),
    ("TODO", "*.md", "Find TODOs in documentation"),
]

# ============================================================================
# Scenario Templates
# ============================================================================

SCENARIOS = {
    "FileRead": [
        {
            "user": "Read the file at src/main.py and show me what's in it",
            "tool_call": {"name": "FileRead", "arguments": {"path": "src/main.py"}},
            "result": "Successfully read file: src/main.py\n```python\ndef main():\n    print('Hello from Stack 2.9!')\n\nif __name__ == '__main__':\n    main()\n```",
            "response": "Here's the contents of `src/main.py`:\n\n```python\ndef main():\n    print('Hello from Stack 2.9!')\n\nif __name__ == '__main__':\n    main()\n```\n\nThis is a simple Python script that prints a greeting when executed directly."
        },
        {
            "user": "Can you show me the README.md file?",
            "tool_call": {"name": "FileRead", "arguments": {"path": "README.md"}},
            "result": "Successfully read file: README.md\n```markdown\n# My Project\n\nA sample project for Stack 2.9.\n\n## Installation\n\npip install -r requirements.txt\n```",
            "response": "Here's the README.md:\n\n```markdown\n# My Project\n\nA sample project for Stack 2.9.\n\n## Installation\n\npip install -r requirements.txt\n```"
        },
        {
            "user": "What's in the config.yaml file?",
            "tool_call": {"name": "FileRead", "arguments": {"path": "config.yaml"}},
            "result": "Successfully read file: config.yaml\n```yaml\ndatabase:\n  host: localhost\n  port: 5432\n  name: myapp\n\napp:\n  port: 3000\n  debug: true\n```",
            "response": "The config.yaml contains:\n\n```yaml\ndatabase:\n  host: localhost\n  port: 5432\n  name: myapp\n\napp:\n  port: 3000\n  debug: true\n```\n\nIt has database connection settings and app configuration."
        },
        {
            "user": "Check the package.json to see the dependencies",
            "tool_call": {"name": "FileRead", "arguments": {"path": "package.json"}},
            "result": "Successfully read file: package.json\n```json\n{\n  \"name\": \"my-app\",\n  \"version\": \"1.0.0\",\n  \"dependencies\": {\n    \"express\": \"^4.18.0\",\n    \"react\": \"^18.2.0\"\n  }\n}\n```",
            "response": "The package.json shows these dependencies:\n\n```json\n{\n  \"name\": \"my-app\",\n  \"version\": \"1.0.0\",\n  \"dependencies\": {\n    \"express\": \"^4.18.0\",\n    \"react\": \"^18.2.0\"\n  }\n}\n```"
        },
    ],
    "FileWrite": [
        {
            "user": "Create a new file called hello.py with a hello world function",
            "tool_call": {"name": "FileWrite", "arguments": {"path": "hello.py", "content": "def hello():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello()\n"}},
            "result": "Successfully wrote file: hello.py",
            "response": "Created `hello.py` with a hello world function:\n\n```python\ndef hello():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello()\n```\n\nYou can run it with `python hello.py`."
        },
        {
            "user": "Write a simple React component to src/components/Button.jsx",
            "tool_call": {"name": "FileWrite", "arguments": {"path": "src/components/Button.jsx", "content": "import React from 'react';\n\nexport default function Button({ onClick, children }) {\n  return (\n    <button onClick={onClick} className=\"btn\">\n      {children}\n    </button>\n  );\n}\n"}},
            "result": "Successfully wrote file: src/components/Button.jsx",
            "response": "Created `src/components/Button.jsx`:\n\n```jsx\nimport React from 'react';\n\nexport default function Button({ onClick, children }) {\n  return (\n    <button onClick={onClick} className=\"btn\">\n      {children}\n    </button>\n  );\n}\n```"
        },
        {
            "user": "Create a config.json file with some settings",
            "tool_call": {"name": "FileWrite", "arguments": {"path": "config.json", "content": "{\n  \"app\": {\n    \"name\": \"MyApp\",\n    \"version\": \"1.0.0\"\n  },\n  \"server\": {\n    \"port\": 8080,\n    \"host\": \"localhost\"\n  }\n}\n"}},
            "result": "Successfully wrote file: config.json",
            "response": "Created `config.json`:\n\n```json\n{\n  \"app\": {\n    \"name\": \"MyApp\",\n    \"version\": \"1.0.0\"\n  },\n  \"server\": {\n    \"port\": 8080,\n    \"host\": \"localhost\"\n  }\n}\n```"
        },
    ],
    "Bash": [
        {
            "user": "Run npm install to install dependencies",
            "tool_call": {"name": "Bash", "arguments": {"command": "npm install"}},
            "result": "added 245 packages in 3.5s",
            "response": "Dependencies installed successfully! Added 245 packages."
        },
        {
            "user": "Check git status",
            "tool_call": {"name": "Bash", "arguments": {"command": "git status"}},
            "result": "On branch main\nYour branch is up to date with 'origin/main'.\n\nChanges not staged for commit:\n  modified:   README.md\n  modified:   src/main.py\n\nno changes added to commit (but untracked files present)",
            "response": "Git status shows:\n- Modified: README.md, src/main.py (not staged)\n- Untracked files present"
        },
        {
            "user": "Run the tests with pytest",
            "tool_call": {"name": "Bash", "arguments": {"command": "pytest -v"}},
            "result": "tests/test_main.py::test_hello PASSED\ntests/test_utils.py::test_add PASSED\n\n2 passed in 0.5s",
            "response": "All tests passed!\n- `tests/test_main.py::test_hello` ✓\n- `tests/test_utils.py::test_add` ✓"
        },
        {
            "user": "List all files in the current directory",
            "tool_call": {"name": "Bash", "arguments": {"command": "ls -la"}},
            "result": "total 64\ndrwxr-xr-x  12 user  staff   384 Apr  6 00:58 .\ndrwxr-xr-x   9 user  staff   288 Apr  6 00:50 ..\n-rw-r--r--   1 user  staff   220 Apr  6 00:50 README.md\ndrwxr-xr-x   3 user  staff   96 Apr  6 00:51 src\ndrwxr-xr-x   3 user  staff   96 Apr  6 00:51 tests\n...",
            "response": "Files in current directory:\n- README.md\n- src/\n- tests/\n- And more (permissions, dates shown)"
        },
        {
            "user": "Build the project with make",
            "tool_call": {"name": "Bash", "arguments": {"command": "make build"}},
            "result": "Building...\ngcc -o main main.c\nobuild successful!",
            "response": "Build completed successfully!"
        },
    ],
    "WebSearch": [
        {
            "user": "How do I use async/await in Python?",
            "tool_call": {"name": "WebSearch", "arguments": {"query": "python async await best practices", "count": 5}},
            "result": "Search results for 'python async await best practices':\n1. Real Python - Async IO in Python: A Complete Walkthrough\n2. Python Docs - asyncio - Asynchronous I/O\n3. Towards Data Science - Mastering Python Async/Await\n4. Stack Overflow - Common async/await mistakes\n5. Medium - Async/Await Patterns in Python",
            "response": "Here are some resources on Python async/await:\n\n1. **Real Python** - Async IO in Python: A Complete Walkthrough\n2. **Python Docs** - asyncio - Asynchronous I/O\n3. **Towards Data Science** - Mastering Python Async/Await\n\nKey points:\n- Use `async def` to define async functions\n- Use `await` to call other async functions\n- `asyncio.run()` to execute the main coroutine"
        },
        {
            "user": "What's the difference between Docker and Kubernetes?",
            "tool_call": {"name": "WebSearch", "arguments": {"query": "Docker vs Kubernetes differences", "count": 5}},
            "result": "Search results for 'Docker vs Kubernetes differences':\n1. Docker Blog - Containers 101\n2. Kubernetes.io - What is Kubernetes\n3. Red Hat - Docker vs Kubernetes explained\n4. DevOps.com - Container orchestration comparison\n5. Container Journal - When to use each",
            "response": "**Docker** is a container platform - it packages applications into containers.\n\n**Kubernetes** is a container orchestrator - it manages multiple containers across machines.\n\nThink of Docker as individual shipping containers, and Kubernetes as the port management system that coordinates all of them."
        },
        {
            "user": "How do I use React hooks properly?",
            "tool_call": {"name": "WebSearch", "arguments": {"query": "React hooks useEffect dependency array", "count": 5}},
            "result": "Search results for 'React hooks useEffect dependency array':\n1. React Docs - Synchronizing with Effects\n2. Kent C. Dodds - A Complete Guide to useEffect\n3. Robin Wieruch - React useEffect Hook Tutorial\n4. Stack Overflow - Common useEffect mistakes\n5. LogRocket - useEffect dependency array deep dive",
            "response": "**React Hooks Guide:**\n\n1. **useState** - For state management\n2. **useEffect** - For side effects, takes dependency array\n3. **useContext** - For global state\n\nThe dependency array controls when the effect runs. Empty `[]` = once on mount. Include variables to re-run when they change."
        },
    ],
    "Grep": [
        {
            "user": "Find all TODO comments in the Python files",
            "tool_call": {"name": "Grep", "arguments": {"pattern": "TODO", "path": ".", "recursive": True, "file_pattern": "*.py"}},
            "result": "Found 3 matches:\nsrc/main.py:14: # TODO: Add error handling\nsrc/utils.py:22: # TODO: Implement caching\ntests/test_main.py:8: # TODO: Add more tests",
            "response": "Found 3 TODO comments in Python files:\n- `src/main.py:14` - Add error handling\n- `src/utils.py:22` - Implement caching\n- `tests/test_main.py:8` - Add more tests"
        },
        {
            "user": "Search for function definitions in the JavaScript files",
            "tool_call": {"name": "Grep", "arguments": {"pattern": "function ", "path": "src", "recursive": True, "file_pattern": "*.js"}},
            "result": "Found 5 matches:\nsrc/index.js:3: function setup() {\nsrc/handlers.js:12: function handleClick(event) {\nsrc/handlers.js:25: function handleSubmit(form) {\nsrc/utils.js:8: function formatDate(date) {\nsrc/utils.js:15: function parseJSON(str) {",
            "response": "Found 5 function definitions in src/:\n- `src/index.js:3` - setup()\n- `src/handlers.js:12` - handleClick(event)\n- `src/handlers.js:15` - handleSubmit(form)\n- `src/utils.js:8` - formatDate(date)\n- `src/utils.js:15` - parseJSON(str)"
        },
        {
            "user": "Find all imports in the Python codebase",
            "tool_call": {"name": "Grep", "arguments": {"pattern": "import ", "path": ".", "recursive": True, "file_pattern": "*.py"}},
            "result": "Found 12 matches:\nsrc/main.py:1: import os\nsrc/main.py:2: import sys\nsrc/main.py:3: import json\nsrc/utils.py:1: from typing import Dict\nsrc/api.py:5: import requests\n...",
            "response": "Found 12 import statements across Python files. Main imports:\n- `os`, `sys`, `json` in src/main.py\n- `typing.Dict` in src/utils.py\n- `requests` in src/api.py"
        },
        {
            "user": "Look for class definitions in TypeScript files",
            "tool_call": {"name": "Grep", "arguments": {"pattern": "class ", "path": "src", "recursive": True, "file_pattern": "*.ts"}},
            "result": "Found 2 matches:\nsrc/models/User.ts:3: class User {\nsrc/models/Config.ts:8: class Config {",
            "response": "Found 2 class definitions:\n- `src/models/User.ts:3` - User class\n- `src/models/Config.ts:8` - Config class"
        },
    ],
}


# ============================================================================
# Data Augmentation Helpers
# ============================================================================

def vary_file_paths(template: Dict) -> Dict:
    """Vary file paths in a scenario to create diversity."""
    import copy
    result = copy.deepcopy(template)
    
    # Vary the file paths
    if "path" in result["tool_call"]["arguments"]:
        original_path = result["tool_call"]["arguments"]["path"]
        for old_path in FILE_PATHS:
            if old_path in result["user"]:
                result["user"] = result["user"].replace(old_path, random.choice(FILE_PATHS))
                result["tool_call"]["arguments"]["path"] = random.choice(FILE_PATHS)
                break
    
    return result


def vary_content(template: Dict) -> Dict:
    """Vary content in a scenario."""
    import copy
    result = copy.deepcopy(template)
    
    if "content" in result["tool_call"]["arguments"]:
        # Vary code snippets
        lang = random.choice(["python", "javascript"])
        result["tool_call"]["arguments"]["content"] = random.choice(CODE_SNIPPETS[lang])
    
    return result


def vary_bash_command(template: Dict) -> Dict:
    """Vary bash commands."""
    import copy
    result = copy.deepcopy(template)
    
    if "command" in result["tool_call"]["arguments"]:
        original = result["tool_call"]["arguments"]["command"].split()[0] if result["tool_call"]["arguments"]["command"] else ""
        
        if "npm" in original:
            commands = ["npm install", "npm run build", "npm test", "npm start"]
        elif "git" in original:
            commands = ["git status", "git log --oneline -5", "git diff", "git branch -a"]
        elif "pytest" in original:
            commands = ["pytest -v", "pytest tests/", "pytest -xvs", "pytest --cov"]
        elif "ls" in original:
            commands = ["ls -la", "ls -1", "ls -lah"]
        elif "make" in original:
            commands = ["make build", "make clean", "make test", "make install"]
        else:
            commands = ["echo 'hello'", "pwd", "whoami", "date"]
        
        result["tool_call"]["arguments"]["command"] = random.choice(commands)
    
    return result


def vary_search_query(template: Dict) -> Dict:
    """Vary web search queries."""
    import copy
    result = copy.deepcopy(template)
    
    if "query" in result["tool_call"]["arguments"]:
        result["tool_call"]["arguments"]["query"] = random.choice(WEB_SEARCH_QUERIES)
    
    return result


def vary_grep_pattern(template: Dict) -> Dict:
    """Vary grep patterns."""
    import copy
    result = copy.deepcopy(template)
    
    pattern, file_pattern, _ = random.choice(GREP_PATTERNS)
    result["tool_call"]["arguments"]["pattern"] = pattern
    result["tool_call"]["arguments"]["file_pattern"] = file_pattern
    
    return result


# ============================================================================
# Main Generation Functions
# ============================================================================

def create_tool_call_message(tool_call: Dict, tool_call_id: str) -> Dict:
    """Create a tool_calls message in Qwen format."""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": tool_call["name"],
                    "arguments": json.dumps(tool_call["arguments"])
                }
            }
        ]
    }


def create_tool_message(role: str, tool_call_id: str, tool_name: str, result: str) -> Dict:
    """Create a tool message (result of tool execution)."""
    return {
        "role": role,  # typically "tool"
        "content": result,
        "tool_call_id": tool_call_id,
        "name": tool_name
    }


def generate_example(scenario: Dict, system_prompt: str = None) -> Dict:
    """Generate a single training example in Qwen2.5-Coder format."""
    if system_prompt is None:
        system_prompt = "You are a helpful AI assistant that can use tools to help users solve problems. When you need to perform actions like reading files, running commands, searching the web, or searching code, use the appropriate tool."
    
    tool_call_id = f"call_${random.randint(1000, 9999)}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": scenario["user"]},
        create_tool_call_message(scenario["tool_call"], tool_call_id),
        create_tool_message("tool", tool_call_id, scenario["tool_call"]["name"], scenario["result"]),
        {"role": "assistant", "content": scenario["response"]}
    ]
    
    return {
        "messages": messages,
        "tools": TOOL_DEFINITIONS
    }


def augment_scenario(scenario: Dict, tool_name: str) -> Dict:
    """Apply random augmentations to a scenario."""
    import random
    
    augmented = scenario.copy()
    
    if tool_name == "FileRead":
        augmented = vary_file_paths(augmented)
    elif tool_name == "FileWrite":
        augmented = vary_file_paths(augmented)
        augmented = vary_content(augmented)
    elif tool_name == "Bash":
        augmented = vary_bash_command(augmented)
    elif tool_name == "WebSearch":
        augmented = vary_search_query(augmented)
    elif tool_name == "Grep":
        augmented = vary_grep_pattern(augmented)
    
    return augmented


def generate_dataset(num_examples: int = 1000, output_path: str = None) -> List[Dict]:
    """Generate the complete dataset."""
    examples = []
    tools = list(SCENARIOS.keys())
    
    # Track counts for balance
    examples_per_tool = num_examples // len(tools)
    remainder = num_examples % len(tools)
    
    for i, tool_name in enumerate(tools):
        # Determine how many examples for this tool
        count = examples_per_tool + (1 if i < remainder else 0)
        
        base_scenarios = SCENARIOS[tool_name]
        
        for j in range(count):
            # Use base scenario and vary
            base = base_scenarios[j % len(base_scenarios)]
            
            # Apply augmentations for variety
            if j >= len(base_scenarios):
                scenario = augment_scenario(base, tool_name)
            else:
                scenario = base
            
            example = generate_example(scenario)
            examples.append(example)
    
    # Shuffle for better training
    random.shuffle(examples)
    
    return examples


def save_jsonl(examples: List[Dict], output_path: str):
    """Save examples to JSONL format."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')


def save_json(examples: List[Dict], output_path: str):
    """Save examples to JSON format."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic tool-calling training data")
    parser.add_argument("--num-examples", type=int, default=1000, help="Number of examples to generate")
    parser.add_argument("--output-dir", type=str, default="training-data", help="Output directory")
    parser.add_argument("--output-format", choices=["jsonl", "json", "both"], default="jsonl", help="Output format")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Set seed for reproducibility
    random.seed(args.seed)
    
    print(f"🎯 Generating {args.num_examples} tool-calling training examples...")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Format: {args.output_format}")
    print()
    
    # Generate dataset
    examples = generate_dataset(args.num_examples)
    
    output_dir = Path(args.output_dir)
    
    # Save based on format
    if args.output_format in ["jsonl", "both"]:
        jsonl_path = output_dir / "tool_examples.jsonl"
        save_jsonl(examples, str(jsonl_path))
        print(f"✅ Saved JSONL: {jsonl_path}")
    
    if args.output_format in ["json", "both"]:
        json_path = output_dir / "tool_examples.json"
        save_json(examples, str(json_path))
        print(f"✅ Saved JSON: {json_path}")
    
    # Statistics
    print(f"\n📊 Statistics:")
    print(f"   Total examples: {len(examples)}")
    
    # Count by tool
    tool_counts = {}
    for ex in examples:
        for msg in ex["messages"]:
            if msg.get("tool_calls"):
                tool_name = msg["tool_calls"][0]["function"]["name"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
    
    print(f"   Examples by tool:")
    for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {tool}: {count}")
    
    # Show sample
    print(f"\n📝 Sample example (first in dataset):")
    sample = examples[0]
    print(f"   Tools defined: {len(sample['tools'])}")
    print(f"   Messages: {len(sample['messages'])}")
    print(f"   First user message: {sample['messages'][1]['content'][:60]}...")
    
    print(f"\n✨ Generation complete!")


if __name__ == "__main__":
    main()
