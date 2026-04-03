// Stack 2.9 LLM Module
//
// Multi-provider LLM client supporting OpenAI, Anthropic, and Ollama.

export {
  OpenAIProvider,
  AnthropicProvider,
  OllamaProvider,
  LLMRouter,
  createProvider,
  createRouter,
  createRouterFromEnv,
} from './LLMService.ts'

export type {
  LLMProviderType,
  LLMConfig,
  ChatMessage,
  ChatParams,
  ChatResponse,
  LLMProvider,
} from './LLMService.ts'

export default {
  createRouter: createRouterFromEnv,
}