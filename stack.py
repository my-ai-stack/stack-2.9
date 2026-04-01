#!/usr/bin/env python3
"""
Stack 2.9 - Main Entry Point
Launch the Stack 2.9 CLI and agent interface.
"""

import sys
from pathlib import Path

# Add stack_cli to path
stack_cli_dir = Path(__file__).parent / "stack_cli"
if stack_cli_dir.exists():
    sys.path.insert(0, str(stack_cli_dir))

try:
    from stack_cli.cli import main as cli_main
except ImportError as e:
    print(f"Error importing Stack CLI: {e}")
    print("Make sure you've installed dependencies: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    cli_main()
