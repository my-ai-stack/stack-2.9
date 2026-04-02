#!/usr/bin/env python3
"""
Download benchmark datasets (HumanEval and MBPP) into ./data/ directory.
Uses huggingface datasets library for reliable downloads.
"""

import os
import json
from pathlib import Path
from datasets import load_dataset
import argparse

def download_humaneval(output_dir: str = "./data"):
    """Download HumanEval dataset (164 problems)."""
    output_path = Path(output_dir) / "humaneval"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"⬇️  Downloading HumanEval to {output_path}...")

    try:
        # Load HumanEval from huggingface
        dataset = load_dataset("openai_humaneval", split="test")

        problems = {}
        for idx, item in enumerate(dataset):
            problem_id = f"HumanEval/{idx}"
            problems[problem_id] = {
                "task_id": problem_id,
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"],
                "test": item["test"],
                "entry_point": item["entry_point"]
            }

        # Save as JSONL (one problem per line)
        output_file = output_path / "humaneval.jsonl"
        with open(output_file, 'w') as f:
            for problem in problems.values():
                f.write(json.dumps(problem) + '\n')

        # Also save a meta file
        meta_file = output_path / "meta.json"
        with open(meta_file, 'w') as f:
            json.dump({
                "name": "HumanEval",
                "num_problems": len(problems),
                "source": "openai_humaneval",
                "description": "164 hand-written programming problems"
            }, f, indent=2)

        print(f"✅ HumanEval: {len(problems)} problems saved to {output_file}")
        return len(problems)

    except Exception as e:
        print(f"❌ Failed to download HumanEval: {e}")
        return 0

def download_mbpp(output_dir: str = "./data"):
    """Download MBPP dataset (500 problems)."""
    output_path = Path(output_dir) / "mbpp"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"⬇️  Downloading MBPP to {output_path}...")

    try:
        # Load MBPP from huggingface
        dataset = load_dataset("mbpp", split="test")

        problems = {}
        for idx, item in enumerate(dataset):
            problem_id = f"MBPP/{idx}"
            problems[problem_id] = {
                "task_id": problem_id,
                "text": item["text"],
                "code": item["code"],
                "test_list": item["test_list"],
                "test_func": item["test_func"],
                "challenge_test_list": item.get("challenge_test_list", [])
            }

        # Save as JSONL
        output_file = output_path / "mbpp.jsonl"
        with open(output_file, 'w') as f:
            for problem in problems.values():
                f.write(json.dumps(problem) + '\n')

        # Meta file
        meta_file = output_path / "meta.json"
        with open(meta_file, 'w') as f:
            json.dump({
                "name": "MBPP",
                "num_problems": len(problems),
                "source": "mbpp",
                "description": "500 beginner-friendly Python programming problems"
            }, f, indent=2)

        print(f"✅ MBPP: {len(problems)} problems saved to {output_file}")
        return len(problems)

    except Exception as e:
        print(f"❌ Failed to download MBPP: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Download benchmark datasets")
    parser.add_argument("--output-dir", type=str, default="./data",
                        help="Output directory (default: ./data)")
    parser.add_argument("--benchmark", type=str, choices=["humaneval", "mbpp", "both"],
                        default="both", help="Which benchmark to download")
    args = parser.parse_args()

    print("📥 Benchmark Dataset Downloader")
    print(f"📁 Target directory: {args.output_dir}")

    total_downloaded = 0

    if args.benchmark in ["humaneval", "both"]:
        total_downloaded += download_humaneval(args.output_dir)

    if args.benchmark in ["mbpp", "both"]:
        total_downloaded += download_mbpp(args.output_dir)

    print(f"\n🎉 Total problems downloaded: {total_downloaded}")
    print(f"📂 Data saved in: {Path(args.output_dir).resolve()}")

if __name__ == "__main__":
    main()
