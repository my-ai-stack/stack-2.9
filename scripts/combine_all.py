#!/usr/bin/env python3
"""
Final dataset combiner - loads all sources, deduplicates, splits.
"""

import json
import hashlib
import random
from pathlib import Path
from datetime import datetime
import glob

def hash_messages(messages: list) -> str:
    """Create hash for deduplication."""
    return hashlib.md5(json.dumps(messages, sort_keys=True).encode()).hexdigest()

def main():
    output_dir = Path("training-data/final")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Glob all potential source files
    source_files = []

    # Synthetic sources
    source_files.extend(glob.glob("training-data/synthetic/*.jsonl"))
    source_files.extend(glob.glob("training-data/advanced-patterns/*.jsonl"))
    source_files.extend(glob.glob("training-data/scaled/*.jsonl"))

    # Code pairs (JSON format)
    source_files.extend(glob.glob("training-data/code-pairs/*.json"))

    print(f"🔍 Found {len(source_files)} source files")

    all_examples = []
    seen_hashes = set()
    source_counts = {}

    for file_path in source_files:
        path = Path(file_path)
        source_name = path.stem
        count = 0

        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        ex = json.loads(line)

                        # Convert code-pair format to message format
                        if "code" in ex and "comment" in ex and "messages" not in ex:
                            ex = {
                                "messages": [
                                    {"role": "user", "content": f"Show me code for: {ex['comment'][:100]}"},
                                    {"role": "assistant", "content": f"Here's a {ex.get('type', 'function')}:\n{ex['code']}"}
                                ],
                                "source_original": source_name,
                                "type": "code_pair"
                            }

                        # Deduplication
                        if "messages" in ex:
                            msg_hash = hash_messages(ex["messages"])
                            if msg_hash in seen_hashes:
                                continue
                            seen_hashes.add(msg_hash)

                            # Track source
                            ex["source_original"] = ex.get("source_original", source_name)
                            all_examples.append(ex)
                            count += 1
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"   ⚠️  Error reading {path}: {e}")
            continue

        source_counts[source_name] = count
        if count > 0:
            print(f"   ✅ {source_name}: {count} examples")

    print(f"\n✨ Total unique examples: {len(all_examples)}")
    print(f"   Deduplication removed: {sum(source_counts.values()) - len(all_examples)}")

    # Shuffle
    random.seed(42)
    random.shuffle(all_examples)

    # Splits (80/10/10)
    n = len(all_examples)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)

    splits = {
        "train": all_examples[:n_train],
        "val": all_examples[n_train:n_train+n_val],
        "test": all_examples[n_train+n_val:]
    }

    for split_name, data in splits.items():
        out_path = output_dir / f"{split_name}.jsonl"
        with open(out_path, 'w') as f:
            for ex in data:
                f.write(json.dumps(ex) + "\n")
        print(f"   📁 {split_name}: {len(data)} -> {out_path}")

    # Manifest
    manifest = {
        "dataset": "Stack 2.9 Training Data",
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "splits": {name: len(data) for name, data in splits.items()},
        "source_breakdown": source_counts,
        "note": "Combined from multiple synthetic and code-pair sources"
    }

    with open(output_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Final dataset ready!")
    print(f"   Total: {len(all_examples)} examples")
    print(f"   Manifest: {output_dir / 'manifest.json'}")

    if len(all_examples) >= 50000:
        print("\n🎉 TARGET ACHIEVED: 50,000+ examples!")
    else:
        print(f"\n⚠️  Still need {50000 - len(all_examples)} more to reach 50K target")

if __name__ == "__main__":
    main()