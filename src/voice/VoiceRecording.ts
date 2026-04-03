// Voice Recording Service - Audio capture for voice input
//
// Handles microphone recording for voice commands using native audio
// or fallback to SoX/arecord on Linux.

import { spawn, type ChildProcess } from 'child_process'
import { readFile } from 'fs/promises'
import { log } from '../utils/logger.js'

// Recording configuration
export const RECORDING_SAMPLE_RATE = 16000
export const RECORDING_CHANNELS = 1
const SILENCE_DURATION_SECS = '2.0'
const SILENCE_THRESHOLD = '3%'

export type RecordingAvailability = {
  available: boolean
  reason: string | null
}

export type RecordingOptions = {
  silenceDetection?: boolean
  sampleRate?: number
  channels?: number
}

/**
 * Check if recording dependencies are available
 */
export async function checkRecordingDependencies(): Promise<{
  available: boolean
  missing: string[]
}> {
  const missing: string[] = []

  // Check for SoX (rec command)
  try {
    const result = spawn('rec', ['--version'], { stdio: 'ignore' })
    await new Promise<void>((resolve) => {
      result.on('close', () => resolve())
      result.on('error', () => resolve())
      setTimeout(() => resolve(), 2000)
    })
  } catch {
    missing.push('sox (rec command)')
  }

  return { available: missing.length === 0, missing }
}

/**
 * Check if recording is available in current environment
 */
export async function checkRecordingAvailability(): Promise<RecordingAvailability> {
  // Check for environment variables that indicate remote/no-audio
  if (process.env.CLAUDE_CODE_REMOTE === 'true') {
    return {
      available: false,
      reason: 'Voice mode requires microphone access in local environment',
    }
  }

  // Check for SoX or native audio
  const deps = await checkRecordingDependencies()
  if (deps.available) {
    return { available: true, reason: null }
  }

  return {
    available: false,
    reason: `Voice recording requires SoX. Install with: brew install sox (macOS) or sudo apt-get install sox (Linux)`,
  }
}

// Active recorder process
let activeRecorder: ChildProcess | null = null
let recordingActive = false

/**
 * Start audio recording
 * @param onData Callback for audio chunks
 * @param onEnd Callback when recording ends
 * @param options Recording options
 */
export async function startRecording(
  onData: (chunk: Buffer) => void,
  onEnd: () => void,
  options: RecordingOptions = {},
): Promise<boolean> {
  const sampleRate = options.sampleRate ?? RECORDING_SAMPLE_RATE
  const channels = options.channels ?? RECORDING_CHANNELS
  const useSilenceDetection = options.silenceDetection ?? true

  log('[voice] Starting recording', { sampleRate, channels, useSilenceDetection })

  // Build SoX command arguments
  const args = [
    '-q', // quiet
    '--buffer',
    '1024',
    '-t',
    'raw',
    '-r',
    String(sampleRate),
    '-e',
    'signed',
    '-b',
    '16',
    '-c',
    String(channels),
    '-', // stdout
  ]

  // Add silence detection if enabled
  if (useSilenceDetection) {
    args.push(
      'silence',
      '1',
      '0.1',
      SILENCE_THRESHOLD,
      '1',
      SILENCE_DURATION_SECS,
      SILENCE_THRESHOLD,
    )
  }

  const child = spawn('rec', args, {
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  activeRecorder = child
  recordingActive = true

  child.stdout?.on('data', (chunk: Buffer) => {
    onData(chunk)
  })

  child.stderr?.on('data', () => {}) // Consume stderr

  child.on('close', () => {
    activeRecorder = null
    recordingActive = false
    onEnd()
  })

  child.on('error', (err) => {
    log('[voice] Recording error', err)
    activeRecorder = null
    recordingActive = false
    onEnd()
  })

  return true
}

/**
 * Stop the current recording
 */
export function stopRecording(): void {
  if (recordingActive && activeRecorder) {
    activeRecorder.kill('SIGTERM')
    activeRecorder = null
    recordingActive = false
  }
}

/**
 * Check if recording is currently active
 */
export function isRecording(): boolean {
  return recordingActive
}

/**
 * Convert audio buffer to base64 for API transfer
 */
export function audioToBase64(buffer: Buffer): string {
  return buffer.toString('base64')
}

/**
 * Convert base64 to audio buffer
 */
export function base64ToAudio(base64: string): Buffer {
  return Buffer.from(base64, 'base64')
}