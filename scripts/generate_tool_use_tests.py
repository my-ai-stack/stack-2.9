#!/usr/bin/env python3
"""
Tool-Use Evaluation Framework for Stack 2.9.
Generates test cases and evaluates model's tool selection accuracy.
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Any
import argparse

def load_tool_catalog(path: str) -> List[Dict]:
    with open(path, 'r') as f:
        return json.load(f)

def generate_test_case(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a single test case for a tool."""
    tool_name = tool["tool"]

    # Templates for each tool (simplified)
    user_prompts = {
        "FileReadTool": [
            "Read {file_path}",
            "Show me the contents of {file_path}",
            "What's in {file_path}?",
            "Open {file_path}"
        ],
        "FileWriteTool": [
            "Create a new file {file_path} with content: {content}",
            "Write this to {file_path}: {content}",
            "Save the following as {file_path}: {content}"
        ],
        "GlobTool": [
            "Find all {pattern} files",
            "List files matching {pattern}",
            "Show me every {pattern}",
            "Search for files like {pattern}"
        ],
        "GrepTool": [
            "Search for {pattern} in {directory}",
            "Find all {pattern}",
            "Grep for {pattern}",
            "Locate {pattern} in the codebase"
        ],
        "BashTool": [
            "Run: {command}",
            "Execute {command}",
            "Please run {command}",
            "Can you execute {command}?"
        ]
        # ... others use default fallback
    }

    prompts = user_prompts.get(tool_name, [
        "Use {tool} to do something",
        "Execute {tool}",
        "Call {tool}"
    ])

    # Choose random prompt template
    prompt_template = random.choice(prompts)

    # Extract placeholders from template
    placeholders = re.findall(r'{(.*?)}', prompt_template)

    # Generate parameter values for each placeholder
    params = {}
    for ph in placeholders:
        if ph == 'file_path':
            params[ph] = random.choice([
                "src/main.py", "README.md", "package.json",
                "config.yaml", "tests/test_api.py", "src/index.js"
            ])
        elif ph == 'pattern':
            params[ph] = random.choice([
                "**/*.py", "**/*.js", "**/*.md", "**/*.test.*",
                "src/**/*.ts", "lib/**/*.py"
            ])
        elif ph == 'command':
            params[ph] = random.choice([
                "npm test", "pytest", "git status", "ls -la",
                "make build", "python -m pip install -e ."
            ])
        elif ph == 'query':
            params[ph] = random.choice(["TODO", "FIXME", "BUG", "HACK"])
        elif ph == 'directory':
            params[ph] = random.choice([".", "src", "tests", "lib", "app"])
        elif ph == 'content':
            params[ph] = "console.log('test');"
        elif ph == 'tool':
            params[ph] = tool_name
        else:
            params[ph] = f"value_{random.randint(1,100)}"

    # Fill prompt template
    prompt = prompt_template.format(**params)

    # Build expected tool call
    expected_tool = tool_name
    # Remove 'tool' param if present (it's just for substitution)
    expected_params = {k: v for k, v in params.items() if k != 'tool'}

    return {
        "test_id": f"{tool_name}_{random.randint(1000,9999)}",
        "prompt": prompt,
        "expected_tool": expected_tool,
        "expected_params": expected_params,
        "tool_description": tool.get("description", ""),
        "difficulty": random.choice(["easy", "medium", "hard"])
    }

def generate_test_suite(catalog: List[Dict], tests_per_tool: int = 10) -> List[Dict]:
    """Generate test suite for all tools."""
    suite = []
    for tool in catalog:
        for _ in range(tests_per_tool):
            test_case = generate_test_case(tool)
            suite.append(test_case)
    return suite

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=str, default="training-data/tools/catalog.json")
    parser.add_argument("--output", type=str, default="stack-2.9-eval/tool_use/test_cases.json")
    parser.add_argument("--tests-per-tool", type=int, default=10)
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    output_path = Path(args.output)

    if not catalog_path.exists():
        print(f"❌ Catalog not found: {catalog_path}")
        return

    tools = load_tool_catalog(catalog_path)
    print(f"🔧 Generating test cases for {len(tools)} tools")

    suite = generate_test_suite(tools, args.tests_per_tool)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(suite, f, indent=2)

    print(f"\n✨ Generated {len(suite)} test cases")
    print(f"   Saved to: {output_path}")

    # Summary by tool
    by_tool = {}
    for tc in suite:
        tool = tc["expected_tool"]
        by_tool[tool] = by_tool.get(tool, 0) + 1

    print("\n📊 Test cases per tool (top 10):")
    for tool, count in sorted(by_tool.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {tool}: {count}")

    print("\n✅ Test suite ready!")
    print("   To evaluate: run tool_use_evaluator.py with a trained model")

if __name__ == "__main__":
    main()