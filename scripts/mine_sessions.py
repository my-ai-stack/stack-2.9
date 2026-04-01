#!/usr/bin/env python3
"""
Mine OpenClaw/Claude sessions for training data.
Extracts conversations with tool use into JSONL format.
"""

import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Any
import argparse

def find_session_logs() -> List[Path]:
    """Find potential session log files in common locations."""
    possible_locations = [
        # OpenClaw sessions
        Path.home() / ".openclaw" / "sessions",
        Path.home() / ".openclaw" / "history",
        # Claude Code sessions
        Path.home() / ".claude" / "sessions",
        Path.home() / ".anthropic" / "sessions",
        # Generic
        Path.home() / "Documents" / "claude_sessions",
        Path.cwd() / "sessions",
        Path.cwd() / ".sessions",
    ]

    log_files = []
    for location in possible_locations:
        if location.exists():
            # Look for JSON, JSONL, or MD files
            for pattern in ["*.json", "*.jsonl", "*.md"]:
                log_files.extend(location.glob(pattern))

    return log_files

def parse_json_conversation(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse a JSON conversation into training examples."""
    examples = []

    # Try different known formats
    if "messages" in data:
        # OpenAI format
        messages = data["messages"]
        if is_valid_conversation(messages):
            examples.append({"messages": messages, "source": "openai_format"})

    elif "conversation" in data:
        # Custom format with conversation array
        messages = data["conversation"]
        if is_valid_conversation(messages):
            examples.append({"messages": messages, "source": "custom"})

    elif "turns" in data:
        # Turn-based format
        turns = data["turns"]
        messages = []
        for turn in turns:
            if "role" in turn and "content" in turn:
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"],
                    "tool_use": turn.get("tool_use"),
                    "tool_result": turn.get("tool_result")
                })
        if is_valid_conversation(messages):
            examples.append({"messages": messages, "source": "turn_based"})

    return examples

def is_valid_conversation(messages: List[Dict[str, Any]]) -> bool:
    """Check if message list is a valid conversation with tool use."""
    if not isinstance(messages, list) or len(messages) < 2:
        return False

    # Must have at least one user and one assistant message
    roles = [m.get("role") for m in messages if "role" in m]
    if "user" not in roles or "assistant" not in roles:
        return False

    return True

def parse_markdown_conversation(text: str) -> List[Dict[str, Any]]:
    """Parse Markdown logs (Claude Code format typically)."""
    examples = []

    # Claude Code / chat format often has blocks like:
    # User: ...
    # Assistant: ...
    # or with tool use in special blocks

    lines = text.split("\n")
    current_role = None
    current_content = []
    messages = []

    for line in lines:
        line = line.rstrip()

        # Detect role changes
        if line.startswith("**User:**") or line.startswith("User:"):
            if current_role:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content).strip()
                })
            current_role = "user"
            current_content = [line.split(":", 1)[1].strip()] if ":" in line else []
        elif line.startswith("**Assistant:**") or line.startswith("Assistant:"):
            if current_role:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content).strip()
                })
            current_role = "assistant"
            current_content = [line.split(":", 1)[1].strip()] if ":" in line else []
        elif line.startswith("**Tool:**") or line.startswith("Tool Use:"):
            if current_role:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content).strip()
                })
            current_role = "assistant"
            # Start tool use block
            current_content = []
            # Could parse tool name and parameters
        else:
            if current_role:
                current_content.append(line)

    # Don't forget last message
    if current_role and current_content:
        messages.append({
            "role": current_role,
            "content": "\n".join(current_content).strip()
        })

    if is_valid_conversation(messages):
        examples.append({"messages": messages, "source": "markdown"})

    return examples

def save_examples(examples: List[Dict[str, Any]], output_path: Path):
    """Save examples to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'a') as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="training-data/scaled/sessions.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Just list files, don't parse")
    args = parser.parse_args()

    output_path = Path(args.output)

    print(f"🔍 Searching for session logs...")
    log_files = find_session_logs()

    if not log_files:
        print("⚠️  No session logs found in standard locations.")
        print("   Expected locations: ~/.openclaw/sessions, ~/.claude/sessions, ~/.anthropic/sessions")
        return

    print(f"📁 Found {len(log_files)} log files")

    if args.dry_run:
        for f in log_files[:10]:
            print(f"  - {f}")
        if len(log_files) > 10:
            print(f"  ... and {len(log_files)-10} more")
        return

    total_examples = 0
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            examples = []

            # Try JSON first
            if log_file.suffix in ['.json', '.jsonl']:
                if log_file.suffix == '.jsonl':
                    # Multiple JSON objects per line
                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                examples.extend(parse_json_conversation(data))
                            except json.JSONDecodeError:
                                pass
                else:
                    # Single JSON object
                    try:
                        data = json.loads(content)
                        examples.extend(parse_json_conversation(data))
                    except json.JSONDecodeError:
                        # Maybe it's a JSON array
                        try:
                            data_list = json.loads(content)
                            if isinstance(data_list, list):
                                for data in data_list:
                                    examples.extend(parse_json_conversation(data))
                        except:
                            pass
            else:
                # Markdown or text
                examples.extend(parse_markdown_conversation(content))

            if examples:
                save_examples(examples, output_path)
                total_examples += len(examples)
                print(f"✅ {log_file.name}: {len(examples)} examples")

        except Exception as e:
            print(f"❌ Error processing {log_file}: {e}")

    print(f"\n✨ Extracted {total_examples} examples from session logs")
    print(f"   Saved to: {output_path}")

    if total_examples == 0:
        print("\n⚠️  No valid conversations found. Consider:")
        print("   1. Check if you have session logs in non-standard locations")
        print("   2. Your logs may be in a different format")
        print("   3. You may need to export conversations from your tools")

if __name__ == "__main__":
    main()