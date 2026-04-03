// Stack 2.9 Voice Module
//
// Voice integration for the Stack 2.9 AI coding assistant.
// Provides voice input/output capabilities through Python FastAPI backend.

import { VoiceApiClient, initVoiceClient, getVoiceClient } from './VoiceApiClient'
import {
  startRecording,
  stopRecording,
  isRecording,
  checkRecordingAvailability,
  checkRecordingDependencies,
  audioToBase64,
  base64ToAudio,
  RECORDING_SAMPLE_RATE,
  RECORDING_CHANNELS,
  type RecordingAvailability,
  type RecordingOptions,
} from './VoiceRecording'

import {
  VoiceRecordingTool,
  VoiceSynthesisTool,
  VoiceCloneTool,
  VoiceStatusTool,
  voiceTools,
  type ToolResult,
} from './VoiceTools'

export {
  VoiceApiClient,
  initVoiceClient,
  getVoiceClient,
  startRecording,
  stopRecording,
  isRecording,
  checkRecordingAvailability,
  checkRecordingDependencies,
  audioToBase64,
  base64ToAudio,
  RECORDING_SAMPLE_RATE,
  RECORDING_CHANNELS,
  VoiceRecordingTool,
  VoiceSynthesisTool,
  VoiceCloneTool,
  VoiceStatusTool,
  voiceTools,
}

export type {
  RecordingAvailability,
  RecordingOptions,
  ToolResult,
}

// Type exports from VoiceApiClient
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
  audioData?: string
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

// Convenience function to initialize voice with config from environment
export function initVoiceFromEnv(): VoiceApiClient | null {
  const apiUrl = process.env.VOICE_API_URL
  if (!apiUrl) {
    console.warn('[voice] VOICE_API_URL not set, voice features disabled')
    return null
  }

  return initVoiceClient({
    apiUrl,
    timeout: parseInt(process.env.VOICE_TIMEOUT ?? '30000', 10),
  })
}

export default {
  initVoiceClient,
  getVoiceClient,
  initVoiceFromEnv,
  voiceTools,
}