// Voice Integration Example - Demonstrates voice tools with Stack 2.9
//
// This example shows how to:
// 1. Initialize the voice client
// 2. Clone a voice from audio sample
// 3. Record voice commands
// 4. Synthesize speech responses

import {
  initVoiceClient,
  VoiceRecordingTool,
  VoiceSynthesisTool,
  VoiceCloneTool,
  VoiceStatusTool,
} from '../voice/index.js'
import { log } from '../utils/logger.js'

/**
 * Example: Initialize voice client and check status
 */
async function checkVoiceStatus() {
  log('Checking voice service status...')

  // Initialize client (or use environment variables)
  const client = initVoiceClient({
    apiUrl: process.env.VOICE_API_URL ?? 'http://localhost:8000',
  })

  const statusTool = new VoiceStatusTool()
  const result = await statusTool.execute()

  log('Voice status:', result)
  return result
}

/**
 * Example: Clone a voice from audio sample
 */
async function cloneVoiceExample() {
  log('Cloning voice from sample...')

  const client = initVoiceClient({
    apiUrl: process.env.VOICE_API_URL ?? 'http://localhost:8000',
  })

  const cloneTool = new VoiceCloneTool()
  const result = await cloneTool.execute({
    voiceName: 'my_voice',
    audioPath: './audio_samples/my_voice.wav',
  })

  log('Clone result:', result)
  return result
}

/**
 * Example: Record voice command
 */
async function recordVoiceCommand() {
  log('Starting voice recording...')

  const recordingTool = new VoiceRecordingTool()

  // Record with max 30 second duration
  const result = await recordingTool.execute({ maxDuration: 30000 })

  if (result.success) {
    const data = result.data as { duration?: number; sampleRate?: number } | undefined
    log('Recording captured:', {
      duration: data?.duration,
      sampleRate: data?.sampleRate,
    })
  } else {
    log('Recording failed:', result.error)
  }

  return result
}

/**
 * Example: Synthesize speech response
 */
async function synthesizeResponse(text: string) {
  log(`Synthesizing: "${text}"`)

  const client = initVoiceClient({
    apiUrl: process.env.VOICE_API_URL ?? 'http://localhost:8000',
  })

  const synthTool = new VoiceSynthesisTool()
  const result = await synthTool.execute({
    text,
    voiceName: 'my_voice',
  })

  if (result.success) {
    log('Audio generated successfully')
  } else {
    log('Synthesis failed:', result.error)
  }

  return result
}

/**
 * Example: Complete voice conversation workflow
 */
async function voiceConversation() {
  // 1. Check status
  await checkVoiceStatus()

  // 2. Record user's voice command
  const recording = await recordVoiceCommand()
  if (!recording.success) {
    log('Cannot proceed without voice input')
    return
  }

  // 3. In real implementation, send audio to STT service
  // const text = await transcribe(recording.data.audio)

  // 4. Process with Stack 2.9 (simulated)
  const responseText = 'I have analyzed your code and found 3 potential improvements.'

  // 5. Synthesize response
  await synthesizeResponse(responseText)
}

// Run examples if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  log('Running voice integration examples...')

  // Check status
  await checkVoiceStatus()

  // Uncomment to run other examples:
  // await cloneVoiceExample()
  // await recordVoiceCommand()
  // await synthesizeResponse('Hello, this is a test response.')
  // await voiceConversation()
}

export default {
  checkVoiceStatus,
  cloneVoiceExample,
  recordVoiceCommand,
  synthesizeResponse,
  voiceConversation,
}