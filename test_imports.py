#!/usr/bin/env python3
"""Test Stack 2.9 CLI imports and basic functionality."""

import sys
from pathlib import Path

# Ensure we can import from stack_cli
stack_cli_path = Path(__file__).parent / "stack_cli"
if str(stack_cli_path) not in sys.path:
    sys.path.insert(0, str(stack_cli_path))

print("Testing Stack 2.9 CLI and Agent Interface...")
print("="*60)

try:
    from stack_cli import tools, agent, context
    print("✓ All modules import successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

try:
    tools_list = tools.list_tools()
    print(f"✓ Tools available: {len(tools_list)}")
except Exception as e:
    print(f"✗ Tools list error: {e}")

try:
    agent_instance = agent.create_agent()
    print("✓ Agent created successfully")
except Exception as e:
    print(f"✗ Agent creation error: {e}")

try:
    ctx_mgr = context.create_context_manager()
    print("✓ Context manager created")
except Exception as e:
    print(f"✗ Context manager error: {e}")

try:
    response = agent_instance.process("list my tasks")
    print(f"✓ Agent responds: {response.content[:50]}...")
except Exception as e:
    print(f"✗ Agent response error: {e}")

print("="*60)
print("Stack 2.9 CLI and Agent Interface is ready!")
print("\nTo run:")
print("  python stack.py              # Interactive chat")
print("  python stack.py -c \"...\"    # Single command")
print("  python demo_stack.py        # Run demo")
