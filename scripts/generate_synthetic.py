#!/usr/bin/env python3
"""
Generate synthetic training examples using templates.
No external APIs - pure template expansion and variation.
"""

import json
import random
import string
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Load tool catalog
def load_tools(catalog_path: str) -> List[Dict[str, Any]]:
    with open(catalog_path, 'r') as f:
        return json.load(f)

# Template definitions for each tool
def get_tool_templates(tool_name: str) -> List[Dict[str, Any]]:
    """Return list of template scenarios for a given tool."""
    templates = {
        "FileReadTool": [
            {
                "user": "Read the file {file_path}",
                "params": {"file_path": "{file_path}"},
                "result": "Contents of {file_path}:\n{file_content}"
            },
            {
                "user": "Show me what's in {file_path}",
                "params": {"file_path": "{file_path}"},
                "result": "Here's {file_path}:\n{file_content}"
            },
            {
                "user": "Can you open {file_path}?",
                "params": {"file_path": "{file_path}"},
                "result": "Opening {file_path}...\n{file_content}"
            }
        ],
        "FileWriteTool": [
            {
                "user": "Create a new file {file_path} with content: {content}",
                "params": {"file_path": "{file_path}", "content": "{content}"},
                "result": "File {file_path} created successfully"
            },
            {
                "user": "Write this to {file_path}: {content}",
                "params": {"file_path": "{file_path}", "content": "{content}"},
                "result": "Wrote to {file_path}"
            }
        ],
        "GlobTool": [
            {
                "user": "Find all {pattern} files",
                "params": {"pattern": "{pattern}"},
                "result": "Found {count} files:\n{files}"
            },
            {
                "user": "List files matching {pattern}",
                "params": {"pattern": "{pattern}"},
                "result": "Matches for {pattern}:\n{files}"
            }
        ],
        "GrepTool": [
            {
                "user": "Search for {pattern} in {directory}",
                "params": {"pattern": "{pattern}", "directory": "{directory}"},
                "result": "Found {count} matches:\n{matches}"
            },
            {
                "user": "Find all occurrences of {pattern}",
                "params": {"pattern": "{pattern}"},
                "result": "Search results:\n{matches}"
            }
        ],
        "BashTool": [
            {
                "user": "Run: {command}",
                "params": {"command": "{command}"},
                "result": "$ {command}\n{output}"
            },
            {
                "user": "Execute {command}",
                "params": {"command": "{command}"},
                "result": "Output:\n{output}"
            }
        ]
    }

    # Return templates or generate generic ones if not defined
    return templates.get(tool_name, [
        {
            "user": "Use {tool} with {params}",
            "params": {"arg": "value"},
            "result": "Operation completed"
        }
    ])

def generate_variations(template: Dict[str, str], count: int, tool_name: str) -> List[Dict[str, Any]]:
    """Generate multiple variations of a template."""
    examples = []

    for _ in range(count):
        # Create parameter values
        params = generate_params(tool_name, template.get("params", {}))

        # Fill template placeholders
        user_prompt = fill_template(template.get("user", ""), params)
        tool_params = fill_params(template.get("params", {}), params)
        result = fill_template(template.get("result", ""), params)

        # Build conversation
        messages = [
            {"role": "user", "content": user_prompt},
            {
                "role": "assistant",
                "content": "I'll help with that.",
                "tool_use": {
                    "name": tool_name,
                    "input": tool_params
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
            {"role": "assistant", "content": "Done!"}
        ]

        examples.append({
            "messages": messages,
            "source": "synthetic_template",
            "tool": tool_name
        })

    return examples

def generate_params(tool_name: str, template_params: Dict[str, str]) -> Dict[str, Any]:
    """Generate realistic parameter values based on tool and template."""
    params = {}

    for key, placeholder in template_params.items():
        if placeholder == "{file_path}":
            params[key] = random.choice([
                "src/main.py", "package.json", "README.md", "src/utils.js",
                "tests/test_api.py", "config.yaml", "Dockerfile", "requirements.txt"
            ])
        elif placeholder == "{pattern}":
            params[key] = random.choice([
                "**/*.py", "**/*.js", "**/*.ts", "*.md", "src/**/*.test.js"
            ])
        elif placeholder == "{command}":
            params[key] = random.choice([
                "ls -la", "pwd", "git status", "npm run build",
                "python -m pytest", "make test", "docker ps"
            ])
        elif placeholder == "{content}":
            params[key] = random.choice([
                "console.log('Hello, World!');",
                "def hello():\n    return 'Hello'",
                "# TODO: implement\npass",
                "import React from 'react';"
            ])
        elif placeholder == "{directory}":
            params[key] = random.choice([
                ".", "src", "tests", "lib", "app/components"
            ])
        else:
            # Generic placeholder
            params[key] = f"generated_value_{random.randint(1,1000)}"

    return params

def fill_template(template: str, params: Dict[str, Any]) -> str:
    """Replace placeholders in template."""
    result = template
    for key, value in params.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    return result

def fill_params(template_params: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """Fill parameter templates."""
    filled = {}
    for key, placeholder in template_params.items():
        if placeholder in [f"{{{k}}}" for k in params.keys()]:
            # Find matching param key
            param_key = placeholder.strip("{}")
            filled[key] = params.get(param_key, placeholder)
        else:
            filled[key] = params.get(key, placeholder)
    return filled

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=str, default="training-data/tools/catalog.json")
    parser.add_argument("--output", type=str, default="training-data/scaled/template_synthetic.jsonl")
    parser.add_argument("--examples-per-tool", type=int, default=500)
    parser.add_argument("--tools-limit", type=int, default=None, help="Limit number of tools to process")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    output_path = Path(args.output)

    if not catalog_path.exists():
        print(f"❌ Tool catalog not found: {catalog_path}")
        return

    tools = load_tools(catalog_path)
    if args.tools_limit:
        tools = tools[:args.tools_limit]

    print(f"🔧 Generating synthetic examples for {len(tools)} tools")
    print(f"   Target: {args.examples_per_tool} examples per tool")
    print(f"   Total expected: ~{len(tools) * args.examples_per_tool} examples")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_examples = 0
    with open(output_path, 'w') as f:
        for tool in tools:
            tool_name = tool.get("tool") or tool.get("name", "Unknown")
            templates = get_tool_templates(tool_name)

            if not templates:
                print(f"⚠️  No templates for {tool_name}, skipping")
                continue

            # Generate examples for each template
            examples_per_template = args.examples_per_tool // len(templates)

            for template in templates:
                examples = generate_variations(template, examples_per_template, tool_name)
                for ex in examples:
                    f.write(json.dumps(ex) + "\n")
                    total_examples += 1

            print(f"✅ {tool_name}: {examples_per_template * len(templates)} examples")

    print(f"\n✨ Generated {total_examples} synthetic examples")
    print(f"   Saved to: {output_path}")

    # Create a sample
    print("\n📝 Sample example:")
    with open(output_path, 'r') as f:
        first_line = f.readline()
        if first_line:
            sample = json.loads(first_line)
            print(f"   User: {sample['messages'][0]['content'][:80]}...")

if __name__ == "__main__":
    main()