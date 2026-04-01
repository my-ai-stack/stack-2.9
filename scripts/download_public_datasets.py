#!/usr/bin/env python3
"""
Download and integrate public coding datasets.
Datasets: OpenAssistant, CodeAct, CodeContests
Converts to Stack 2.9 format.
"""

import json
import os
from datasets import load_dataset
from pathlib import Path
import argparse

def download_openassistant(output_path: Path, limit: int = 10000):
    """Download OpenAssistant and filter for coding conversations."""
    print("📥 Downloading OpenAssistant dataset...")
    try:
        dataset = load_dataset("OpenAssistant/oasst1", split="train")
    except Exception as e:
        print(f"❌ Failed to load OpenAssistant: {e}")
        return []

    coding_examples = []
    count = 0

    for item in dataset:
        # Filter for coding-related conversations
        text = item.get("text", "").lower()
        if any(keyword in text for keyword in ["code", "programming", "python", "javascript", "function", "api", "development"]):
            # Convert to our format
            messages = [
                {"role": "user", "content": item.get("text", "")[:1000]},  # truncated
                {"role": "assistant", "content": "Here's a coding assistant response..."}
            ]
            coding_examples.append({
                "messages": messages,
                "source": "openassistant",
                "dataset": "oasst1"
            })
            count += 1
            if count >= limit:
                break

    print(f"   Extracted {len(coding_examples)} coding-related examples from OpenAssistant")
    return coding_examples

def download_codeact(output_path: Path, limit: int = 10000):
    """Download CodeAct dataset."""
    print("📥 Downloading CodeAct dataset...")
    try:
        dataset = load_dataset("nuprl/CodeAct", split="train")
    except Exception as e:
        print(f"❌ Failed to load CodeAct: {e}")
        return []

    examples = []
    count = 0

    for item in dataset:
        # CodeAct has actions - convert to tool calls
        action = item.get("action", {})
        if action:
            messages = [
                {"role": "user", "content": item.get("instruction", "")},
                {
                    "role": "assistant",
                    "content": "Executing action...",
                    "tool_use": {
                        "name": "CodeActTool",
                        "input": action
                    }
                },
                {
                    "role": "user",
                    "content": "",
                    "tool_result": {
                        "tool_use_id": "tool_1",
                        "content": json.dumps(item.get("observation", {}))
                    }
                },
                {"role": "assistant", "content": item.get("final_answer", "Done.")}
            ]
            examples.append({
                "messages": messages,
                "source": "codeact",
                "dataset": "CodeAct"
            })
            count += 1
            if count >= limit:
                break

    print(f"   Extracted {len(examples)} examples from CodeAct")
    return examples

def download_codecontests(output_path: Path, limit: int = 5000):
    """Download CodeContests (competition problems)."""
    print("📥 Downloading CodeContests dataset...")
    try:
        dataset = load_dataset("m-a-p/CodeContests", split="train")
    except Exception as e:
        print(f"❌ Failed to load CodeContests: {e}")
        return []

    examples = []
    count = 0

    for item in dataset:
        if item.get("problem") and item.get("solution"):
            messages = [
                {"role": "user", "content": f"Solve this problem:\n{item['problem']}"},
                {"role": "assistant", "content": f"Here's a solution:\n```python\n{item['solution']}\n```"}
            ]
            examples.append({
                "messages": messages,
                "source": "codecontests",
                "dataset": "CodeContests"
            })
            count += 1
            if count >= limit:
                break

    print(f"   Extracted {len(examples)} examples from CodeContests")
    return examples

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="training-data/scaled/public_datasets.jsonl")
    parser.add_argument("--limit-per-dataset", type=int, default=10000)
    parser.add_argument("--skip-download", action="store_true", help="Use only existing datasets")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_examples = []

    if not args.skip_download:
        # OpenAssistant
        all_examples.extend(download_openassistant(output_path, args.limit_per_dataset))

        # CodeAct
        all_examples.extend(download_codeact(output_path, args.limit_per_dataset))

        # CodeContests
        all_examples.extend(download_codecontests(output_path, min(5000, args.limit_per_dataset)))
    else:
        print("⚠️  Skipping downloads (--skip-download flag)")

    # Write all examples
    with open(output_path, 'w') as f:
        for ex in all_examples:
            f.write(json.dumps(ex) + "\n")

    print(f"\n✨ Saved {len(all_examples)} examples from public datasets")
    print(f"   to: {output_path}")

    # Show breakdown
    sources = {}
    for ex in all_examples:
        src = ex.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    print("\n📊 Breakdown:")
    for src, count in sources.items():
        print(f"   {src}: {count}")

    print("\n⚠️  Note: These are raw integrations. May need format conversion to match tool-use patterns.")

if __name__ == "__main__":
    main()