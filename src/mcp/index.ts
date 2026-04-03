// Stack 2.9 MCP Module
//
// Model Context Protocol client for tool extensibility.

export {
  MCPClient,
  MCPConnectionManager,
  createMCPClient,
} from './MCPClient.ts'

export type {
  MCPTransportType,
  MCPConfig,
  MCP_SERVER_CONFIG,
  MCPTool,
  MCPResource,
} from './MCPClient.ts'

export default {
  MCPConnectionManager,
}