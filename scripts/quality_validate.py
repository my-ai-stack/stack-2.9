#!/usr/bin/env python3
"""
Quality validation for Stack 2.9 training dataset.
Checks: message structure, tool format, schema compliance.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import argparse
from collections import Counter

def load_tool_catalog(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return {tool["tool"]: tool for tool in json.load(f)}

def validate_example(example: Dict[str, Any], tool_catalog: Dict[str, Any]) -> List[str]:
    """Validate a single example. Returns list of errors (empty if valid)."""
    errors = []

    if "messages" not in example:
        errors.append("Missing 'messages' field")
        return errors

    messages = example["messages"]
    if not isinstance(messages, list) or len(messages) < 2:
        errors.append("Invalid messages: must be list with at least 2 messages")
        return errors

    # Check roles sequence
    roles = [msg.get("role") for msg in messages]
    valid_roles = {"system", "user", "assistant"}
    if not all(r in valid_roles for r in roles):
        errors.append(f"Invalid roles: {roles}")

    # Tool use validation
    for msg in messages:
        if msg.get("role") == "assistant" and "tool_use" in msg:
            tool_use = msg["tool_use"]
            if "name" not in tool_use:
                errors.append("Tool use missing 'name'")
            else:
                tool_name = tool_use["name"]
                if tool_name not in tool_catalog:
                    errors.append(f"Unknown tool: {tool_name}")
            if "input" not in tool_use:
                errors.append(f"Tool use missing 'input' for {tool_name}")

        if msg.get("role") == "user" and "tool_result" in msg:
            tool_result = msg["tool_result"]
            if "tool_use_id" not in tool_result:
                errors.append("Tool result missing 'tool_use_id'")
            if "content" not in tool_result:
                errors.append("Tool result missing 'content'")

    # Check message content is non-empty (except user with tool_result can be empty)
    for i, msg in enumerate(messages):
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and "tool_result" in msg:
            continue  # Tool result user message can have empty content
        if content is not None and not isinstance(content, str):
            errors.append(f"Message content must be string, got {type(content)}")
        if content is not None and len(content.strip()) == 0:
            errors.append(f"Empty content in {role} message")

    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="training-data/final/train.jsonl")
    parser.add_argument("--catalog", type=str, default="training-data/tools/catalog.json")
    parser.add_argument("--output-report", type=str, default="training-data/final/quality_report.json")
    args = parser.parse_args()

    input_path = Path(args.input)
    catalog_path = Path(args.catalog)

    if not input_path.exists():
        print(f"❌ Input not found: {input_path}")
        return

    if not catalog_path.exists():
        print(f"⚠️  Catalog not found: {catalog_path}, skipping tool validation")
        tool_catalog = {}
    else:
        tool_catalog = load_tool_catalog(catalog_path)
        print(f"✅ Loaded tool catalog with {len(tool_catalog)} tools")

    print(f"🔍 Validating {input_path}...")

    total_examples = 0
    valid_examples = 0
    error_distribution = Counter()
    tool_usage = Counter()

    with open(input_path, 'r') as f:
        for line in f:
            total_examples += 1
            try:
                example = json.loads(line)
                errors = validate_example(example, tool_catalog)

                if errors:
                    for err in errors:
                        error_distribution[err] += 1
                else:
                    valid_examples += 1

                # Track tool usage regardless of validation
                for msg in example.get("messages", []):
                    if "tool_use" in msg:
                        tool_name = msg["tool_use"]["name"]
                        tool_usage[tool_name] += 1

            except json.JSONDecodeError:
                error_distribution["JSON decode error"] += 1

    print(f"\n📊 Validation Results:")
    print(f"   Total examples: {total_examples}")
    print(f"   Valid: {valid_examples} ({valid_examples/total_examples*100:.1f}%)")
    print(f"   Invalid: {total_examples - valid_examples}")

    if error_distribution:
        print("\n   Error breakdown:")
        for err, count in error_distribution.most_common(10):
            print(f"     - {err}: {count}")

    print("\n   Tool usage (top 10):")
    for tool, count in tool_usage.most_common(10):
        print(f"     - {tool}: {count}")

    # Write report
    report = {
        "total_examples": total_examples,
        "valid_examples": valid_examples,
        "invalid_examples": total_examples - valid_examples,
        "validity_rate": valid_examples / total_examples if total_examples > 0 else 0,
        "error_distribution": dict(error_distribution),
        "tool_usage": dict(tool_usage),
        "generated_at": datetime.datetime.now().isoformat()
    }

    output_report = Path(args.output_report)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved: {output_report}")

    if valid_examples / total_examples < 0.9:
        print("\n⚠️  Quality below 90%. Consider filtering invalid examples before training.")
    else:
        print("\n✅ Dataset quality looks good for training!")

if __name__ == "__main__":
    import json, datetime
    main()