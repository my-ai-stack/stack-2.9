// MCP Client - Model Context Protocol client for Stack 2.9
//
// Provides MCP server integration for tool extensibility.
// Supports stdio, SSE, and HTTP transports.

export type MCPTransportType = 'stdio' | 'sse' | 'http'

export interface MCPConfig {
  name: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  url?: string
  transport?: MCPTransportType
}

export interface MCPTool {
  name: string
  description: string
  inputSchema: Record<string, unknown>
}

export interface MCPResource {
  uri: string
  name: string
  description?: string
  mimeType?: string
}

export interface MCP_SERVER_CONFIG {
  name: string
  transport: 'stdio' | 'sse' | 'http'
  command?: string
  args?: string[]
  env?: Record<string, string>
  url?: string
}

interface MCPRequest {
  jsonrpc: '2.0'
  id: number | string
  method: string
  params?: Record<string, unknown>
}

interface MCPResponse {
  jsonrpc: '2.0'
  id: number | string
  result?: unknown
  error?: {
    code: number
    message: string
    data?: unknown
  }
}

// ─── MCP Client ───

export class MCPClient {
  private config: MCP_SERVER_CONFIG
  private requestId = 0
  private pendingRequests: Map<number | string, {
    resolve: (value: unknown) => void
    reject: (error: Error) => void
  }> = new Map()

  constructor(config: MCP_SERVER_CONFIG) {
    this.config = config
  }

  get name(): string {
    return this.config.name
  }

  get transport(): string {
    return this.config.transport
  }

  // Send an MCP request and wait for response
  async sendRequest(method: string, params?: Record<string, unknown>): Promise<unknown> {
    const id = ++this.requestId
    const request: MCPRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params,
    }

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject })

      if (this.config.transport === 'stdio') {
        this.sendStdioRequest(request)
      } else if (this.config.transport === 'http' || this.config.transport === 'sse') {
        this.sendHttpRequest(request)
      }
    })
  }

  private async sendStdioRequest(request: MCPRequest): Promise<void> {
    // In stdio mode, would spawn the process and communicate via stdin/stdout
    console.log('[mcp] Stdio request:', request)
  }

  private async sendHttpRequest(request: MCPRequest): Promise<void> {
    const url = this.config.url
    if (!url) {
      throw new Error('MCP HTTP client requires URL')
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`MCP request failed: ${response.status}`)
      }

      const data = await response.json() as MCPResponse
      const pending = this.pendingRequests.get(data.id)
      if (pending) {
        if (data.error) {
          pending.reject(new Error(data.error.message))
        } else {
          pending.resolve(data.result)
        }
        this.pendingRequests.delete(data.id)
      }
    } catch (error) {
      // Reject all pending requests
      for (const [, pending] of this.pendingRequests) {
        pending.reject(error as Error)
      }
      this.pendingRequests.clear()
    }
  }

  // List available tools
  async listTools(): Promise<MCPTool[]> {
    try {
      const result = await this.sendRequest('tools/list') as {
        tools: Array<{
          name: string
          description?: string
          inputSchema?: Record<string, unknown>
        }>
      }
      return (result.tools ?? []).map(t => ({
        name: t.name,
        description: t.description ?? '',
        inputSchema: t.inputSchema ?? {},
      }))
    } catch {
      return []
    }
  }

  // Call a tool
  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    return this.sendRequest('tools/call', { name, arguments: args })
  }

  // List available resources
  async listResources(): Promise<MCPResource[]> {
    try {
      const result = await this.sendRequest('resources/list') as {
        resources: Array<{
          uri: string
          name: string
          description?: string
          mimeType?: string
        }>
      }
      return (result.resources ?? []).map(r => ({
        uri: r.uri,
        name: r.name,
        description: r.description,
        mimeType: r.mimeType,
      }))
    } catch {
      return []
    }
  }

  // Read a resource
  async readResource(uri: string): Promise<unknown> {
    return this.sendRequest('resources/read', { uri })
  }
}

// ─── MCP Connection Manager ───

export class MCPConnectionManager {
  private connections: Map<string, MCPClient> = new Map()

  async addServer(config: MCP_SERVER_CONFIG): Promise<MCPClient> {
    const client = new MCPClient(config)
    this.connections.set(config.name, client)

    // Initialize the connection
    try {
      await client.sendRequest('initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'stack-2.9',
          version: '1.0.0',
        },
      })
      console.log(`[mcp] Connected to ${config.name}`)
    } catch (error) {
      console.error(`[mcp] Failed to connect to ${config.name}:`, error)
    }

    return client
  }

  getServer(name: string): MCPClient | undefined {
    return this.connections.get(name)
  }

  removeServer(name: string): void {
    this.connections.delete(name)
  }

  listServers(): string[] {
    return Array.from(this.connections.keys())
  }

  async closeAll(): Promise<void> {
    for (const [name, client] of this.connections) {
      try {
        await client.sendRequest('shutdown')
      } catch {
        // Ignore shutdown errors
      }
      console.log(`[mcp] Disconnected from ${name}`)
    }
    this.connections.clear()
  }
}

// ─── Factory ───

export function createMCPClient(config: MCPConfig): MCPClient {
  const serverConfig: MCP_SERVER_CONFIG = {
    name: config.name,
    transport: config.transport ?? 'stdio',
    command: config.command,
    args: config.args,
    env: config.env,
    url: config.url,
  }

  return new MCPClient(serverConfig)
}

export default {
  MCPClient,
  MCPConnectionManager,
  createMCPClient,
}