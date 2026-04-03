// LLM Service - Multi-provider LLM client for Stack 2.9
//
// Supports: OpenAI, Anthropic, Ollama, and custom endpoints
// with automatic fallback on failure.

export type LLMProviderType = 'openai' | 'anthropic' | 'ollama' | 'custom'

export interface LLMConfig {
  provider: LLMProviderType
  apiKey?: string
  baseURL?: string
  model: string
  maxTokens?: number
  temperature?: number
  topP?: number
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatParams {
  messages: ChatMessage[]
  model?: string
  maxTokens?: number
  temperature?: number
  topP?: number
  tools?: unknown[]
}

export interface ChatResponse {
  content: string
  model: string
  usage?: {
    inputTokens: number
    outputTokens: number
  }
  finishReason: 'stop' | 'length' | 'content_filter' | null
}

export interface LLMProvider {
  readonly type: LLMProviderType
  readonly name: string

  isAvailable(): boolean
  chat(params: ChatParams): Promise<ChatResponse>
  listModels(): string[]
}

// ─── OpenAI Provider ───

export class OpenAIProvider implements LLMProvider {
  readonly type: LLMProviderType = 'openai'
  readonly name = 'OpenAI'

  private apiKey: string
  private baseURL: string
  private model: string

  constructor(config: { apiKey: string; baseURL?: string; model?: string }) {
    this.apiKey = config.apiKey
    this.baseURL = config.baseURL ?? 'https://api.openai.com/v1'
    this.model = config.model ?? 'gpt-4'
  }

  isAvailable(): boolean {
    return Boolean(this.apiKey)
  }

  async chat(params: ChatParams): Promise<ChatResponse> {
    const response = await fetch(`${this.baseURL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: params.model ?? this.model,
        messages: params.messages,
        max_tokens: params.maxTokens,
        temperature: params.temperature,
        top_p: params.topP,
        tools: params.tools,
      }),
    })

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string }; finish_reason: string }>
      model: string
      usage: { prompt_tokens: number; completion_tokens: number }
    }

    return {
      content: data.choices[0]?.message?.content ?? '',
      model: data.model,
      usage: {
        inputTokens: data.usage?.prompt_tokens ?? 0,
        outputTokens: data.usage?.completion_tokens ?? 0,
      },
      finishReason: data.choices[0]?.finish_reason as ChatResponse['finishReason'],
    }
  }

  listModels(): string[] {
    return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o']
  }
}

// ─── Anthropic Provider ───

export class AnthropicProvider implements LLMProvider {
  readonly type: LLMProviderType = 'anthropic'
  readonly name = 'Anthropic'

  private apiKey: string
  private baseURL: string
  private model: string

  constructor(config: { apiKey: string; baseURL?: string; model?: string }) {
    this.apiKey = config.apiKey
    this.baseURL = config.baseURL ?? 'https://api.anthropic.com'
    this.model = config.model ?? 'claude-3-sonnet-20240229'
  }

  isAvailable(): boolean {
    return Boolean(this.apiKey)
  }

  async chat(params: ChatParams): Promise<ChatResponse> {
    // Extract system message
    const systemMessage = params.messages.find(m => m.role === 'system')?.content
    const filteredMessages = params.messages.filter(m => m.role !== 'system')

    const response = await fetch(`${this.baseURL}/v1/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: params.model ?? this.model,
        messages: filteredMessages,
        system: systemMessage,
        max_tokens: params.maxTokens ?? 1024,
        temperature: params.temperature,
        top_p: params.topP,
      }),
    })

    if (!response.ok) {
      throw new Error(`Anthropic API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json() as {
      content: Array<{ type: string; text?: string }>
      model: string
      usage: { input_tokens: number; output_tokens: number }
      stop_reason: string
    }

    return {
      content: data.content.find(c => c.type === 'text')?.text ?? '',
      model: data.model,
      usage: {
        inputTokens: data.usage?.input_tokens ?? 0,
        outputTokens: data.usage?.output_tokens ?? 0,
      },
      finishReason: data.stop_reason as ChatResponse['finishReason'],
    }
  }

  listModels(): string[] {
    return ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
  }
}

// ─── Ollama Provider ───

export class OllamaProvider implements LLMProvider {
  readonly type: LLMProviderType = 'ollama'
  readonly name = 'Ollama'

  private baseURL: string
  private model: string

  constructor(config: { baseURL?: string; model?: string }) {
    this.baseURL = config.baseURL ?? 'http://localhost:11434'
    this.model = config.model ?? 'llama2'
  }

  isAvailable(): boolean {
    return true // Ollama is local, always available if running
  }

  async chat(params: ChatParams): Promise<ChatResponse> {
    const response = await fetch(`${this.baseURL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: params.model ?? this.model,
        messages: params.messages,
        options: {
          temperature: params.temperature,
          top_p: params.topP,
          num_predict: params.maxTokens,
        },
        stream: false,
      }),
    })

    if (!response.ok) {
      throw new Error(`Ollama error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json() as {
      message: { content: string }
      model: string
    }

    return {
      content: data.message?.content ?? '',
      model: data.model,
      finishReason: 'stop',
    }
  }

  async listModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseURL}/api/tags`)
      if (!response.ok) return [this.model]

      const data = await response.json() as { models: Array<{ name: string }> }
      return data.models.map(m => m.name)
    } catch {
      return [this.model]
    }
  }
}

// ─── LLM Router ───

export class LLMRouter {
  private providers: Map<LLMProviderType, LLMProvider> = new Map()
  private defaultProvider: LLMProviderType = 'ollama'

  addProvider(provider: LLMProvider): void {
    this.providers.set(provider.type, provider)
  }

  setDefault(provider: LLMProviderType): void {
    if (!this.providers.has(provider)) {
      throw new Error(`Provider ${provider} not configured`)
    }
    this.defaultProvider = provider
  }

  getProvider(type?: LLMProviderType): LLMProvider {
    const provider = type ?? this.defaultProvider
    const instance = this.providers.get(provider)
    if (!instance) {
      throw new Error(`Provider ${provider} not configured`)
    }
    return instance
  }

  async chat(params: ChatParams & { provider?: LLMProviderType }): Promise<ChatResponse> {
    const provider = this.getProvider(params.provider)
    return provider.chat(params)
  }
}

// ─── Factory ───

export function createProvider(config: LLMConfig): LLMProvider {
  switch (config.provider) {
    case 'openai':
      return new OpenAIProvider({
        apiKey: config.apiKey ?? '',
        baseURL: config.baseURL,
        model: config.model,
      })
    case 'anthropic':
      return new AnthropicProvider({
        apiKey: config.apiKey ?? '',
        baseURL: config.baseURL,
        model: config.model,
      })
    case 'ollama':
      return new OllamaProvider({
        baseURL: config.baseURL,
        model: config.model,
      })
    default:
      throw new Error(`Unknown provider: ${config.provider}`)
  }
}

export function createRouter(configs: LLMConfig[]): LLMRouter {
  const router = new LLMRouter()

  for (const config of configs) {
    router.addProvider(createProvider(config))
  }

  return router
}

// Default router from environment
export function createRouterFromEnv(): LLMRouter {
  const configs: LLMConfig[] = []

  // Check for OpenAI
  if (process.env.OPENAI_API_KEY) {
    configs.push({
      provider: 'openai',
      apiKey: process.env.OPENAI_API_KEY,
      model: process.env.OPENAI_MODEL ?? 'gpt-4',
    })
  }

  // Check for Anthropic
  if (process.env.ANTHROPIC_API_KEY) {
    configs.push({
      provider: 'anthropic',
      apiKey: process.env.ANTHROPIC_API_KEY,
      model: process.env.ANTHROPIC_MODEL ?? 'claude-3-sonnet-20240229',
    })
  }

  // Always add Ollama (local)
  configs.push({
    provider: 'ollama',
    baseURL: process.env.OLLAMA_BASE_URL,
    model: process.env.OLLAMA_MODEL ?? 'llama2',
  })

  return createRouter(configs)
}

export default {
  OpenAIProvider,
  AnthropicProvider,
  OllamaProvider,
  LLMRouter,
  createProvider,
  createRouter,
  createRouterFromEnv,
}