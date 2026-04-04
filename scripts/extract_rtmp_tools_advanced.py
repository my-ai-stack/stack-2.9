#!/usr/bin/env python3
"""
Extract advanced training data from RTMP tools
Includes actual patterns, best practices, and tool definitions
"""

import os
import json
from pathlib import Path

RTMP_DIR = "/Users/walidsobhi/.openclaw/workspace/RTMP"
OUTPUT_DIR = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/data/rtmp-tools"

def get_tool_definitions():
    """Get detailed tool definitions with examples"""
    tools = []

    # BashTool
    tools.append({
        "messages": [
            {"role": "system", "content": "You are a helpful AI coding assistant with access to various tools."},
            {"role": "user", "content": "List all files in the current directory including hidden files"},
            {"role": "assistant", "tool_calls": [
                {"name": "Bash", "arguments": {"command": "ls -la"}}
            ]},
            {"role": "tool", "content": "total 128\ndrwxr-xr-x 1 user staff 4096 Apr 4 10:00 .\ndrwxr-xr-x 1 user staff 4096 Apr 4 10:00 ..\n-rw-r--r-- 1 user staff 1024 Apr 4 09:00 file.ts"}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Find all TypeScript files in the src directory"},
            {"role": "assistant", "tool_calls": [
                {"name": "Glob", "arguments": {"pattern": "src/**/*.ts"}}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Search for all TODO comments in the codebase"},
            {"role": "assistant", "tool_calls": [
                {"name": "Grep", "arguments": {"pattern": "TODO", "path": ".", "output_mode": "content"}}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Read the package.json file"},
            {"role": "assistant", "tool_calls": [
                {"name": "FileRead", "arguments": {"file_path": "package.json"}}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Create a new task to implement the login feature"},
            {"role": "assistant", "tool_calls": [
                {"name": "TaskCreate", "arguments": {
                    "subject": "Implement login feature",
                    "description": "Add user authentication with OAuth",
                    "activeForm": "Implementing login feature"
                }}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Search the web for how to use PyTorch MPS on Apple Silicon"},
            {"role": "assistant", "tool_calls": [
                {"name": "WebSearch", "arguments": {"query": "PyTorch MPS Apple Silicon tutorial"}}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Fetch the documentation from https://pytorch.org/docs"},
            {"role": "assistant", "tool_calls": [
                {"name": "WebFetch", "arguments": {"url": "https://pytorch.org/docs", "prompt": "Extract the main features of PyTorch"}}
            ]}
        ]
    })

    # Task management examples
    tools.append({
        "messages": [
            {"role": "user", "content": "Show me all open tasks"},
            {"role": "assistant", "tool_calls": [
                {"name": "TaskList", "arguments": {}}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "What's the status of the login feature task?"},
            {"role": "assistant", "tool_calls": [
                {"name": "TaskGet", "arguments": {"taskId": "1"}}
            ]}
        ]
    })

    # File operations
    tools.append({
        "messages": [
            {"role": "user", "content": "Write a simple Python script to a new file"},
            {"role": "assistant", "tool_calls": [
                {"name": "FileWrite", "arguments": {
                    "file_path": "hello.py",
                    "content": "print('Hello, World!')\n"
                }}
            ]}
        ]
    })

    tools.append({
        "messages": [
            {"role": "user", "content": "Edit the config file to enable debug mode"},
            {"role": "assistant", "tool_calls": [
                {"name": "FileEdit", "arguments": {
                    "file_path": "config.json",
                    "old_string": "\"debug\": false",
                    "new_string": "\"debug\": true"
                }}
            ]}
        ]
    })

    # Complex multi-step examples
    tools.append({
        "messages": [
            {"role": "user", "content": "First find all React component files, then read one of them"},
            {"role": "assistant", "tool_calls": [
                {"name": "Glob", "arguments": {"pattern": "**/*.{tsx,jsx}"}},
                {"name": "TaskCreate", "arguments": {
                    "subject": "Read React components",
                    "description": "Read the found component files",
                    "activeForm": "Reading React components"
                }}
            ]}
        ]
    })

    # Skill invocation
    tools.append({
        "messages": [
            {"role": "user", "content": "Commit the changes with a message"},
            {"role": "assistant", "tool_calls": [
                {"name": "Skill", "arguments": {"skill": "git-commit", "args": "-m 'Fix bug'"}}
            ]}
        ]
    })

    return tools

def main():
    print("=" * 60)
    print("Extracting Advanced RTMP Tool Patterns")
    print("=" * 60)

    # Get tool examples
    tools = get_tool_definitions()

    print(f"\n✅ Created {len(tools)} advanced tool examples")

    # Save to JSONL
    output_file = os.path.join(OUTPUT_DIR, "advanced_tool_patterns.jsonl")
    with open(output_file, 'w') as f:
        for ex in tools:
            f.write(json.dumps(ex) + '\n')

    print(f"✅ Saved to: {output_file}")

    # Combine with previous
    prev_file = os.path.join(OUTPUT_DIR, "tool_patterns.jsonl")
    combined_file = os.path.join(OUTPUT_DIR, "combined_tools.jsonl")

    with open(combined_file, 'w') as out:
        # Previous simple patterns
        if os.path.exists(prev_file):
            with open(prev_file) as f:
                for line in f:
                    out.write(line)
        # Advanced patterns
        with open(output_file) as f:
            for line in f:
                out.write(line)

    print(f"\n📦 Total combined examples:")
    with open(combined_file) as f:
        count = sum(1 for _ in f)
    print(f"   {count} tool usage examples")

if __name__ == "__main__":
    main()