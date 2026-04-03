// Voice API Client - Connects to Python voice server (Coqui TTS)
//
// This client provides TypeScript bindings to the Python FastAPI voice service
// for voice cloning and text-to-speech synthesis.

export interface VoiceConfig {
  apiUrl: string
  timeout?: number
}

export interface VoiceModel {
  name: string
  description?: string
}

export interface CloneVoiceRequest {
  voiceName: string
  audioPath?: string
  audioData?: string // base64 encoded audio
}

export interface SynthesizeRequest {
  text: string
  voiceName: string
  language?: string
}

export interface VoiceListResponse {
  voices: VoiceModel[]
  count: number
}

export interface CloneVoiceResponse {
  success: boolean
  voiceName: string
  message: string
}

export class VoiceApiClient {
  private apiUrl: string
  private timeout: number

  constructor(config: VoiceConfig) {
    this.apiUrl = config.apiUrl.replace(/\/$/, '')
    this.timeout = config.timeout ?? 30000
  }

  /**
   * List all available voice models
   */
  async listVoices(): Promise<VoiceListResponse> {
    const response = await fetch(`${this.apiUrl}/voices`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(this.timeout),
    })

    if (!response.ok) {
      throw new Error(`Failed to list voices: ${response.status} ${response.statusText}`)
    }

    return response.json() as Promise<VoiceListResponse>
  }

  /**
   * Clone a voice from audio sample(s)
   */
  async cloneVoice(request: CloneVoiceRequest): Promise<CloneVoiceResponse> {
    const response = await fetch(`${this.apiUrl}/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(this.timeout),
    })

    if (!response.ok) {
      throw new Error(`Failed to clone voice: ${response.status} ${response.statusText}`)
    }

    return response.json() as Promise<CloneVoiceResponse>
  }

  /**
   * Synthesize speech with a cloned voice
   * Returns audio data as a Blob
   */
  async synthesize(request: SynthesizeRequest): Promise<Blob> {
    const response = await fetch(`${this.apiUrl}/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(this.timeout),
    })

    if (!response.ok) {
      throw new Error(`Failed to synthesize: ${response.status} ${response.statusText}`)
    }

    return response.blob()
  }

  /**
   * Stream speech synthesis for real-time applications
   */
  async *streamSynthesize(request: SynthesizeRequest): AsyncGenerator<Uint8Array> {
    const response = await fetch(`${this.apiUrl}/synthesize_stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(this.timeout),
    })

    if (!response.ok) {
      throw new Error(`Failed to stream synthesize: ${response.status} ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('Empty response body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        yield value
      }
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Check if voice server is available
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      })
      return response.ok
    } catch {
      return false
    }
  }
}

// Default client instance
let defaultClient: VoiceApiClient | null = null

/**
 * Initialize the default voice client
 */
export function initVoiceClient(config: VoiceConfig): VoiceApiClient {
  defaultClient = new VoiceApiClient(config)
  return defaultClient
}

/**
 * Get the default voice client
 */
export function getVoiceClient(): VoiceApiClient | null {
  return defaultClient
}