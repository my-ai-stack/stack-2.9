#!/usr/bin/env python3
"""Run the Stack 2.9 MCP Server"""

import sys
import os

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp_server import main

if __name__ == "__main__":
    main()