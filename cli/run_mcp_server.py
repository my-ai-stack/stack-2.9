#!/usr/bin/env python3
"""Run the Stack 2.9 MCP Server"""

import sys
import os

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.mcp_server import main

if __name__ == "__main__":
    main()