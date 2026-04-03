// Voice Tools - Tools for voice input/output in the AI assistant
//
// Provides tools for:
// - VoiceRecordingTool: Record voice commands
// - VoiceSynthesisTool: Speak responses
// - VoiceCloneTool: Clone voices from samples

import { log } from '../utils/logger'
import { initVoiceClient, getVoiceClient } from './VoiceApiClient'
import {
  startRecording,
  stopRecording,
  isRecording,
  checkRecordingAvailability,
  audioToBase64,
  type RecordingAvailability
} from './VoiceRecording'

// Tool result types
export interface ToolResult {
  success: boolean
  data?: unknown
  error?: string
}

// Voice config type
export interface VoiceConfig {
  apiUrl: string
  timeout?: number
}

// ─── Voice Recording Tool ───

/**
 * VoiceRecordingTool - Records voice input from microphone
 */
export class VoiceRecordingTool {
  name = 'VoiceRecordingTool'
  description = 'Record voice input from the microphone for voice commands'

  async execute(options?: { maxDuration?: number }): Promise<ToolResult> {
    try {
      // Check availability
      const availability = await checkRecordingAvailability()
      if (!availability.available) {
        return { success: false, error: availability.reason ?? 'Recording not available' }
      }

      // Start recording
      let audioChunks: Buffer[] = []

      const started = await startRecording(
        (chunk) => {
          audioChunks.push(chunk)
        },
        () => {
          log('[voice] Recording ended')
        },
        { silenceDetection: true }
      )

      if (!started) {
        return { success: false, error: 'Failed to start recording' }
      }

      // Wait for recording to end (silence detection)
      await new Promise<void>((resolve) => {
        const checkInterval = setInterval(() => {
          if (!isRecording()) {
            clearInterval(checkInterval)
            resolve()
          }
        }, 100)

        // Timeout after maxDuration
        if (options?.maxDuration) {
          setTimeout(() => {
            clearInterval(checkInterval)
            stopRecording()
            resolve()
          }, options.maxDuration)
        }
      })

      // Combine audio chunks
      const audioBuffer = Buffer.concat(audioChunks)
      const base64Audio = audioToBase64(audioBuffer)

      return {
        success: true,
        data: {
          audio: base64Audio,
          duration: audioBuffer.length / (16000 * 2),
          sampleRate: 16000,
          channels: 1,
        },
      }
    } catch (error) {
      log('[voice] Recording error', error)
      return { success: false, error: String(error) }
    }
  }

  stop(): void {
    stopRecording()
  }
}

// ─── Voice Synthesis Tool ───

/**
 * VoiceSynthesisTool - Convert text to speech using cloned voice
 */
export class VoiceSynthesisTool {
  private client: ReturnType<typeof getVoiceClient>

  constructor(config?: VoiceConfig) {
    if (config) {
      this.client = initVoiceClient(config)
    } else {
      this.client = getVoiceClient()
    }
  }

  name = 'VoiceSynthesisTool'
  description = 'Convert text to speech using a cloned voice'

  async execute(request: { text: string; voiceName?: string }): Promise<ToolResult> {
    const client = this.client
    if (!client) {
      return {
        success: false,
        error: 'Voice client not initialized. Call initVoiceClient() first.',
      }
    }

    try {
      const audioBlob = await client.synthesize({
        text: request.text,
        voiceName: request.voiceName ?? 'default',
      })

      // Convert blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer()
      const base64Audio = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )

      return {
        success: true,
        data: {
          audio: base64Audio,
          format: 'wav',
          text: request.text,
        },
      }
    } catch (error) {
      log('[voice] Synthesis error', error)
      return { success: false, error: String(error) }
    }
  }

  async *streamExecute(request: { text: string; voiceName?: string }): AsyncGenerator<Uint8Array> {
    const client = this.client
    if (!client) {
      throw new Error('Voice client not initialized')
    }

    yield* client.streamSynthesize({
      text: request.text,
      voiceName: request.voiceName ?? 'default',
    })
  }
}

// ─── Voice Clone Tool ───

/**
 * VoiceCloneTool - Clone a voice from audio samples
 */
export class VoiceCloneTool {
  private client: ReturnType<typeof getVoiceClient>

  constructor(config?: VoiceConfig) {
    if (config) {
      this.client = initVoiceClient(config)
    } else {
      this.client = getVoiceClient()
    }
  }

  name = 'VoiceCloneTool'
  description = 'Clone a voice from audio samples for use in synthesis'

  async execute(request: { voiceName: string; audioPath?: string; audioData?: string }): Promise<ToolResult> {
    const client = this.client
    if (!client) {
      return {
        success: false,
        error: 'Voice client not initialized. Call initVoiceClient() first.',
      }
    }

    try {
      const result = await client.cloneVoice({
        voiceName: request.voiceName,
        audioPath: request.audioPath,
        audioData: request.audioData,
      })

      return {
        success: result.success,
        data: result,
      }
    } catch (error) {
      log('[voice] Clone error', error)
      return { success: false, error: String(error) }
    }
  }
}

// ─── Voice Status Tool ───

/**
 * VoiceStatusTool - Check voice service availability
 */
export class VoiceStatusTool {
  private client: ReturnType<typeof getVoiceClient>

  constructor(config?: VoiceConfig) {
    if (config) {
      this.client = initVoiceClient(config)
    } else {
      this.client = getVoiceClient()
    }
  }

  name = 'VoiceStatusTool'
  description = 'Check voice service status and list available voices'

  async execute(): Promise<ToolResult> {
    try {
      // Check recording availability
      const recordingAvail = await checkRecordingAvailability()

      // Check voice API availability
      let apiAvailable = false
      let voices: string[] = []

      const client = this.client
      if (client) {
        apiAvailable = await client.healthCheck()
        if (apiAvailable) {
          const voiceList = await client.listVoices()
          voices = voiceList.voices.map((v: { name: string }) => v.name)
        }
      }

      return {
        success: true,
        data: {
          recording: recordingAvail,
          api: apiAvailable,
          voices,
        },
      }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  }
}

// ─── Tool Registry ───

export const voiceTools = {
  VoiceRecordingTool,
  VoiceSynthesisTool,
  VoiceCloneTool,
  VoiceStatusTool,
}

export default voiceTools