#!/usr/bin/env python3
"""Test MCP server stdio communication"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Send initialize + tools/list on stdin, read responses
import json

init_msg = json.dumps({"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1})
list_msg = json.dumps({"jsonrpc":"2.0","method":"tools/list","params":{},"id":2})

# Write both messages
for msg in [init_msg, list_msg]:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

# Read responses
sys.stderr.write("Waiting for responses...\n")
sys.stderr.flush()
