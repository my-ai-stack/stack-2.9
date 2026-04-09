#!/bin/bash
# End-to-end MCP protocol test
cd /Users/walidsobhi/stack-2.9

# Start server in background, send JSON-RPC messages via stdin, capture responses
python3 src/mcp_server.py << 'EOF'
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"grep","arguments":{"pattern":"def main","path":"src","file_pattern":"*.py","max_results":3}},"id":2}
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"WebSearch","arguments":{"query":"AI news","max_results":2}},"id":3}
EOF
