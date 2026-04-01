#!/usr/bin/env python3
"""
Stack 2.9 - Main Entry Point
Launch the Stack 2.9 CLI and agent interface.
"""

import sys
import argparse
from pathlib import Path

# Add directories to path
stack_cli_dir = Path(__file__).parent / "stack_cli"
stack_2_9_cli = Path(__file__).parent / "stack-2-9-cli"
stack_2_9_eval = Path(__file__).parent / "stack-2-9-eval"
stack_2_9_training = Path(__file__).parent / "stack-2-9-training"

paths = [str(stack_cli_dir), str(stack_2_9_cli), str(stack_2_9_eval), str(stack_2_9_training)]
for p in paths:
    if Path(p).exists():
        sys.path.insert(0, p)


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 CLI")
    parser.add_argument("--provider", "-p", choices=["ollama", "openai", "anthropic"],
                        default="ollama", help="Model provider")
    parser.add_argument("--model", "-m", type=str, help="Model name")
    parser.add_argument("--chat", "-c", action="store_true", help="Start in chat mode")
    parser.add_argument("--eval", "-e", choices=["mbpp", "human_eval", "gsm8k", "all"],
                        help="Run evaluation benchmark")
    parser.add_argument("--patterns", action="store_true", help="View pattern statistics")
    args = parser.parse_args()

    # Try new CLI first, fall back to old
    try:
        from stack_2_9_cli.main import main as new_main
        new_main()
    except ImportError:
        try:
            from stack_cli.cli import main as cli_main
            cli_main()
        except ImportError as e:
            print(f"Error: {e}")
            print("Install dependencies: pip install -r requirements.txt")
            sys.exit(1)


if __name__ == "__main__":
    main()