#!/usr/bin/env python3
"""
Stack 2.9 Demo Script
Showcases the capabilities of the Stack 2.9 CLI and Agent Interface.
"""

import os
import sys
from pathlib import Path

# Add stack_cli to path
sys.path.insert(0, str(Path(__file__).parent / "stack_cli"))

from stack_cli.agent import create_agent
from stack_cli.tools import list_tools
from stack_cli.context import create_context_manager

def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def demo():
    """Run the demo."""
    print_banner()
    
    # Initialize
    print("\n➤ Initializing Stack 2.9 Agent...")
    agent = create_agent()
    print(f"  ✓ Agent loaded with {len(list_tools())} tools")
    
    # Show context
    print_section("Workspace Context")
    ctx = agent.get_context()
    print(ctx)
    
    # Show available tools
    print_section("Available Tools")
    tools = list_tools()
    print(f"\nTotal tools: {len(tools)}\n")
    
    categories = {
        "File Operations": ["read", "write", "edit", "search", "grep", "copy", "move", "delete"],
        "Git Operations": ["git_status", "git_commit", "git_push", "git_pull", "git_branch", "git_log", "git_diff"],
        "Code Execution": ["run", "test", "lint", "format", "typecheck", "server", "install"],
        "Web Tools": ["web_search", "fetch", "download", "check_url", "screenshot"],
        "Memory & Context": ["memory_recall", "memory_save", "memory_list", "context_load", "project_scan"],
        "Task Planning": ["create_task", "list_tasks", "update_task", "delete_task", "create_plan", "execute_plan"]
    }
    
    for category, tool_list in categories.items():
        print(f"\n{category} ({len(tool_list)}):")
        for tool in tool_list:
            if tool in tools:
                print(f"  ✓ {tool}")
    
    # Demo: Run a sample query
    print_section("Demo: Sample Query")
    print("\nQuery: \"list my tasks\"")
    
    response = agent.process("list my tasks")
    print(f"\nResponse:\n  {response.content}")
    
    print_section("Demo: Project Scan")
    print("\nQuery: \"scan project structure\"")
    
    response = agent.process("scan project structure")
    print(f"\nResponse:\n  {response.content[:500]}...")
    
    print_section("Agent Capabilities")
    print("""
The Stack 2.9 Agent can:
  • Understand natural language queries
  • Select appropriate tools automatically
  • Generate helpful responses
  • Self-reflect and improve
  • Maintain conversation context
  • Execute complex workflows
    """)
    
    print_section("Quick Start")
    print("""
To use Stack 2.9 CLI:

1. Interactive Chat:
   $ python -m stack_cli.cli
   or
   $ stack

2. Single Command:
   $ python -m stack_cli.cli -c "read README.md"
   or
   $ stack -c "git status"

3. Specific Tools:
   $ stack -t project_scan list_tasks

4. Voice Mode (requires setup):
   $ stack -v

5. Python API:
   from stack_cli import create_agent
   agent = create_agent()
   response = agent.process("list files")
   print(response.content)
    """)
    
    print_section("Demo Complete!")
    print("\nThe Stack 2.9 CLI and Agent Interface is ready to use.")
    print("Run 'python stack.py' or 'stack' to start.\n")

def print_banner():
    """Print the banner."""
    banner = r"""
    ____                _           _         _    
   |  _ \ ___ _ __   __| |_ __ ___ (_)_ __   | | __
   | |_) / _ \ '_ \ / _` | '__/ _ \| | '_ \  | |/ /
   |  _ <  __/ | | | (_| | | | (_) | | | | | |   <
   |_| \_\___|_| |_|\__,_|_|  \___/|_|_| |_| |_|\_\
                                              
         CLI & Agent Interface v2.9.0
    """
    print(banner)

if __name__ == "__main__":
    demo()
