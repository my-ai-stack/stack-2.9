#!/usr/bin/env python3
"""
Extract training data from RTMP tools for Stack 2.9
Creates synthetic tool-use examples from the RTMP codebase
"""

import os
import json
from pathlib import Path

RTMP_DIR = "/Users/walidsobhi/.openclaw/workspace/RTMP"
OUTPUT_DIR = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/data/rtmp-tools"

def get_tool_description(tool_name: str) -> str:
    """Get tool descriptions from tool names"""
    descriptions = {
        "BashTool": "Execute shell commands in a sandboxed environment",
        "FileReadTool": "Read file contents from the filesystem",
        "FileWriteTool": "Write content to files",
        "FileEditTool": "Edit files using sed-style replacements",
        "GlobTool": "Find files matching glob patterns",
        "GrepTool": "Search for patterns in files",
        "TaskCreateTool": "Create tasks in the task list",
        "TaskListTool": "List all tasks in the task list",
        "TaskUpdateTool": "Update task status and details",
        "TaskGetTool": "Get details of a specific task",
        "WebSearchTool": "Search the web for information",
        "WebFetchTool": "Fetch and analyze web pages",
        "SkillTool": "Execute user-invocable skills",
        "McpTool": "Call MCP (Model Context Protocol) tools",
        "AgentTool": "Delegate tasks to sub-agents",
    }
    return descriptions.get(tool_name.replace("Tool", ""), f"Tool: {tool_name}")

def extract_tool_examples():
    """Extract tool patterns and create training examples"""
    examples = []

    tools_dir = Path(RTMP_DIR) / "tools"
    if not tools_dir.exists():
        print(f"❌ Tools directory not found: {tools_dir}")
        return examples

    # Process each tool
    tool_dirs = [d for d in tools_dir.iterdir() if d.is_dir() and d.name.endswith("Tool")]

    for tool_dir in tool_dirs:
        tool_name = tool_dir.name

        # Get main tool file
        main_files = list(tool_dir.glob("*.tsx")) + list(tool_dir.glob("*.ts"))

        # Create example for this tool
        desc = get_tool_description(tool_name)

        # Generate prompt-response pairs for tool usage
        example = {
            "messages": [
                {
                    "role": "user",
                    "content": f"How do I use the {tool_name}? What does it do?"
                },
                {
                    "role": "assistant",
                    "content": f"The {tool_name} allows you to {desc.lower()}.\n\n" +
                              f"This is one of the core tools in RTMP (Real-Time AI Assistant).\n\n" +
                              f"Tools like {tool_name} enable the assistant to interact with the filesystem, " +
                              f"execute commands, manage tasks, and more."
                }
            ]
        }
        examples.append(example)

        # Add more specific examples for common tools
        if "Bash" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "List all files in the current directory"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "Bash", "arguments": {"command": "ls -la"}}
                    ]}
                ]
            }
            examples.append(example)

        elif "FileRead" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "Read the contents of config.json"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "FileRead", "arguments": {"file_path": "config.json"}}
                    ]}
                ]
            }
            examples.append(example)

        elif "Glob" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "Find all TypeScript files in the project"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "Glob", "arguments": {"pattern": "**/*.ts"}}
                    ]}
                ]
            }
            examples.append(example)

        elif "Grep" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "Find all occurrences of 'TODO' in the code"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "Grep", "arguments": {"pattern": "TODO", "path": "."}}
                    ]}
                ]
            }
            examples.append(example)

        elif "TaskCreate" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "Create a task to fix the login bug"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "TaskCreate", "arguments": {
                            "subject": "Fix login bug",
                            "description": "Investigate and fix the login issue"
                        }}
                    ]}
                ]
            }
            examples.append(example)

        elif "WebSearch" in tool_name:
            example = {
                "messages": [
                    {"role": "user", "content": "Search for latest Python 3.14 features"},
                    {"role": "assistant", "tool_calls": [
                        {"name": "WebSearch", "arguments": {"query": "Python 3.14 new features"}}
                    ]}
                ]
            }
            examples.append(example)

    return examples

def main():
    print("=" * 60)
    print("Extracting RTMP Tool Patterns for Training")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extract examples
    examples = extract_tool_examples()

    print(f"\n✅ Extracted {len(examples)} tool usage examples")

    # Save to JSONL
    output_file = os.path.join(OUTPUT_DIR, "tool_patterns.jsonl")
    with open(output_file, 'w') as f:
        for ex in examples:
            f.write(json.dumps(ex) + '\n')

    print(f"✅ Saved to: {output_file}")

    # Also show some examples
    print("\n📋 Sample examples:")
    for i, ex in enumerate(examples[:3]):
        user_msg = ex["messages"][0]["content"]
        print(f"  {i+1}. User: {user_msg[:60]}...")

if __name__ == "__main__":
    main()