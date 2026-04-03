// Simple logger utility for Stack 2.9

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

let currentLevel: LogLevel = 'info'

export function setLogLevel(level: LogLevel): void {
  currentLevel = level
}

function shouldLog(level: LogLevel): boolean {
  return LOG_LEVELS[level] >= LOG_LEVELS[currentLevel]
}

function formatMessage(level: LogLevel, message: string, data?: unknown): string {
  const timestamp = new Date().toISOString()
  const dataStr = data ? ` ${JSON.stringify(data)}` : ''
  return `[${timestamp}] [${level.toUpperCase()}] ${message}${dataStr}`
}

export function debug(message: string, data?: unknown): void {
  if (shouldLog('debug')) {
    console.log(formatMessage('debug', message, data))
  }
}

export function log(message: string, data?: unknown): void {
  if (shouldLog('info')) {
    console.log(formatMessage('info', message, data))
  }
}

export function warn(message: string, data?: unknown): void {
  if (shouldLog('warn')) {
    console.warn(formatMessage('warn', message, data))
  }
}

export function error(message: string, data?: unknown): void {
  if (shouldLog('error')) {
    console.error(formatMessage('error', message, data))
  }
}

export default { debug, log, warn, error, setLogLevel }