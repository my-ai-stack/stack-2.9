#!/usr/bin/env python3
"""
Generate random synthetic tool-use examples.
Uses tool catalog to create syntactically valid random conversations.
"""

import json
import random
from pathlib import Path
import argparse

def load_tool_catalog(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def random_value_for_type(param_name: str) -> Any:
    """Generate a plausible random value based on parameter name."""
    if 'file' in param_name or 'path' in param_name:
        return random.choice(['src/main.py', 'README.md', 'package.json', 'config.yaml', 'tests/test.js'])
    elif 'command' in param_name or 'cmd' in param_name:
        return random.choice(['npm test', 'pytest', 'git status', 'ls -la', 'make build'])
    elif 'pattern' in param_name or 'glob' in param_name:
        return random.choice(['**/*.py', '**/*.js', '**/*.md'])
    elif 'query' in param_name or 'search' in param_name:
        return random.choice(['TODO', 'FIXME', 'function main'])
    elif 'url' in param_name or 'uri' in param_name:
        return random.choice(['https://api.example.com', 'mcp://server/resource'])
    elif 'status' in param_name:
        return random.choice(['pending', 'in_progress', 'completed'])
    elif 'id' in param_name or 'task_id' in param_name:
        return random.randint(100, 999)
    elif 'name' in param_name:
        return random.choice(['agent1', 'myteam', 'task123'])
    elif 'content' in param_name or 'text' in param_name:
        return 'Lorem ipsum dolor sit amet...'
    elif 'directory' in param_name or 'dir' in param_name:
        return random.choice(['.', 'src', 'tests', 'lib'])
    elif 'branch' in param_name:
        return random.choice(['main', 'develop', 'feature/new'])
    else:
        return f"value_{random.randint(1,100)}"

def generate_random_example(tools: List[Dict], tool_count: int = 1) -> Dict[str, Any]:
    """Generate a random conversation with one or more tool uses."""
    tools_sample = random.sample(tools, min(tool_count, len(tools)))

    # Build messages
    messages = []

    # Random user prompt
    user_prompt = random.choice([
        "Help me with something",
        "Do a task",
        "I need assistance",
        "Can you handle this?",
        "Execute this",
        "Run this operation"
    ])
    messages.append({"role": "user", "content": user_prompt})

    # For each tool, add assistant tool-use and tool-result
    for i, tool in enumerate(tools_sample):
        tool_name = tool.get("tool") or tool.get("name", "UnknownTool")

        # Generate random parameters based on tool's expected inputs
        # We don't have strict schema, so make up plausible params
        tool_input = {}
        for j in range(random.randint(1, 3)):
            param_name = random.choice(['file_path', 'command', 'pattern', 'query', 'url', 'id', 'name', 'directory'])
            tool_input[param_name] = random_value_for_type(param_name)

        # Assistant uses tool
        messages.append({
            "role": "assistant",
            "content": f"Using {tool_name}...",
            "tool_use": {
                "name": tool_name,
                "input": tool_input
            }
        })

        # Tool result
        result_content = f"Operation completed successfully. Affected items: {random.randint(1,10)}"
        messages.append({
            "role": "user",
            "content": "",
            "tool_result": {
                "tool_use_id": f"tool_{i+1}",
                "content": result_content
            }
        })

        # Assistant acknowledges
        messages.append({
            "role": "assistant",
            "content": random.choice(["Done.", "Completed.", "All set."])
        })

    return {
        "messages": messages,
        "source": "random_synthetic",
        "tools_used": [t.get("tool") for t in tools_sample]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=str, default="training-data/tools/catalog.json")
    parser.add_argument("--output", type=str, default="training-data/scaled/random_synthetic.jsonl")
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--tools-per-example", type=int, default=1)
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    output_path = Path(args.output)

    if not catalog_path.exists():
        print(f"❌ Catalog not found: {catalog_path}")
        return

    tools = load_tool_catalog(catalog_path)
    print(f"🔧 Loaded {len(tools)} tools from catalog")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for i in range(args.count):
            example = generate_random_example(tools, args.tools_per_example)
            f.write(json.dumps(example) + "\n")
            if (i+1) % 1000 == 0:
                print(f"   Generated {i+1}/{args.count}...", end='\r')

    print(f"\n✨ Generated {args.count} random synthetic examples")
    print(f"   Saved to: {output_path}")

    # Show sample
    with open(output_path, 'r') as f:
        sample = json.loads(f.readline())
        print(f"\n📝 Sample: {len(sample['messages'])} messages, tools: {sample.get('tools_used')}")

if __name__ == "__main__":
    main()