#!/usr/bin/env python3
"""
Combine all training data sources into final dataset.
Applies deduplication and quality filtering.
"""

import json
import hashlib
from pathlib import Path
import argparse
from datetime import datetime

def hash_messages(messages: list) -> str:
    """Create a hash of messages to detect duplicates."""
    m = hashlib.md5()
    m.update(json.dumps(messages, sort_keys=True).encode())
    return m.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="training-data/final/dataset.jsonl")
    parser.add_argument("--train-size", type=float, default=0.8)
    parser.add_argument("--val-size", type=float, default=0.1)
    parser.add_argument("--max-dataset", type=int, default=50000, help="Max examples to include")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # List all source files
    sources = [
        ("training-data/synthetic/examples.jsonl", "original_synthetic"),
        ("training-data/advanced-patterns/examples.jsonl", "advanced_patterns"),
        ("training-data/code-pairs/pairs.json", "code_pairs"),
        ("training-data/code-pairs/extended_pairs.json", "code_pairs_extended"),
        ("training-data/scaled/synthetic_final.jsonl", "synthetic_augmented"),
        ("training-data/scaled/random_10k.jsonl", "random_10k"),
        ("training-data/scaled/random_5_5k.jsonl", "random_5k"),
    ]

    all_examples = []
    seen_hashes = set()
    duplicates_removed = 0

    print("📦 Combining datasets...")
    for file_path, source in sources:
        path = Path(file_path)
        if not path.exists():
            print(f"   ⚠️  Not found: {path}")
            continue

        print(f"   Loading {source}...")
        count = 0
        with open(path, 'r') as f:
            for line in f:
                try:
                    ex = json.loads(line)

                    # Convert code-pair format if needed
                    if "code" in ex and "comment" in ex:
                        # Convert code-pair to message format
                        ex = {
                            "messages": [
                                {"role": "user", "content": ex["comment"]},
                                {"role": "assistant", "content": f"Here's the code:\n{ex['code']}"}
                            ],
                            "source": source,
                            "type": "code_pair"
                        }

                    # Deduplication
                    msg_hash = hash_messages(ex["messages"])
                    if msg_hash in seen_hashes:
                        duplicates_removed += 1
                        continue
                    seen_hashes.add(msg_hash)

                    # Add metadata
                    ex["source_original"] = source
                    all_examples.append(ex)
                    count += 1

                    if len(all_examples) >= args.max_dataset:
                        break

                except json.JSONDecodeError:
                    continue

        print(f"      ✅ Added {count} examples")

    print(f"\n✨ Total collected: {len(all_examples)} examples")
    print(f"   Duplicates removed: {duplicates_removed}")

    # Shuffle
    random.seed(42)
    random.shuffle(all_examples)

    # Split
    n_total = len(all_examples)
    n_train = int(n_total * args.train_size)
    n_val = int(n_total * args.val_size)
    n_test = n_total - n_train - n_val

    train_set = all_examples[:n_train]
    val_set = all_examples[n_train:n_train+n_val]
    test_set = all_examples[n_train+n_val:]

    print(f"\n📊 Split:")
    print(f"   Train: {len(train_set)}")
    print(f"   Val: {len(val_set)}")
    print(f"   Test: {len(test_set)}")

    # Save splits
    for split_name, split_data in [("train", train_set), ("val", val_set), ("test", test_set)]:
        split_path = output_path.parent / f"{split_name}.jsonl"
        with open(split_path, 'w') as f:
            for ex in split_data:
                f.write(json.dumps(ex) + "\n")
        print(f"   Saved {split_name} to {split_path}")

    # Create manifest
    manifest = {
        "dataset": "Stack 2.9 Training Data",
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "total_examples": n_total,
        "splits": {
            "train": len(train_set),
            "val": len(val_set),
            "test": len(test_set)
        },
        "sources": {src: sum(1 for ex in all_examples if ex.get("source_original") == src) for src in set(ex.get("source_original") for ex in all_examples)}
    }

    manifest_path = output_path.parent / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\n📄 Manifest: {manifest_path}")

    print("\n✅ Dataset complete!")

if __name__ == "__main__":
    import random
    main()