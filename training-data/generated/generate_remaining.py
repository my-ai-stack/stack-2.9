#!/usr/bin/env python3
"""Generate remaining code completion examples to reach 1000 total."""

import json
import random

random.seed(42)

# Additional TypeScript patterns
TS_PATTERNS_MORE = [
    # More async patterns
    {
        "input": "export async function fetchWithRetry(\n  url: string,\n  options?: RequestInit,\n  maxRetries: number = 3,\n): Promise<Response> {",
        "output": "let lastError: Error;\n  for (let i = 0; i < maxRetries; i++) {\n    try {\n      return await fetch(url, options);\n    } catch (e) {\n      lastError = e as Error;\n      if (i < maxRetries - 1) {\n        await new Promise(r => setTimeout(r, 1000 * (i + 1)));\n      }\n    }\n  }\n  throw lastError!;"
    },
    {
        "input": "export async function parallelLimit(\n  tasks: Array<() => Promise<any>>,\n  limit: number,\n): Promise<any[]> {",
        "output": "const results: any[] = [];\n  const executing: Promise<any>[] = [];\n  \n  for (const task of tasks) {\n    const p = task().then(result => {\n      results.push(result);\n      executing.splice(executing.indexOf(p), 1);\n    });\n    executing.push(p);\n    \n    if (executing.length >= limit) {\n      await Promise.race(executing);\n    }\n  }\n  \n  await Promise.all(executing);\n  return results;"
    },
    {
        "input": "export function createCache<K, V>(\n  loadFn: (key: K) => Promise<V>,\n  maxSize: number = 100,\n): Cache<K, V> {",
        "output": "const cache = new Map<K, V>();\n  return {\n    async get(key: K): Promise<V> {\n      if (cache.has(key)) return cache.get(key)!;\n      const value = await loadFn(key);\n      if (cache.size >= maxSize) {\n        const firstKey = cache.keys().next().value;\n        cache.delete(firstKey);\n      }\n      cache.set(key, value);\n      return value;\n    },\n    clear(): void { cache.clear(); },\n  };"
    },
    {
        "input": "export class Semaphore {\n  private permits: number;\n  private waiters: Array<() => void> = [];\n  \n  constructor(initialPermits: number) {\n    this.permits = initialPermits;\n  }\n  \n  async acquire(): Promise<void> {",
        "output": "if (this.permits > 0) {\n      this.permits--;\n      return;\n    }\n    return new Promise(resolve => this.waiters.push(resolve));"
    },
    {
        "input": "export class Semaphore {\n  release(): void {",
        "output": "this.permits++;\n    if (this.waiters.length > 0) {\n      const resolve = this.waiters.shift()!;\n      this.permits--;\n      resolve();\n    }"
    },
    {
        "input": "export async function withLock<T>(\n  lock: Mutex,\n  fn: () => Promise<T>,\n): Promise<T> {",
        "output": "await lock.acquire();\n  try {\n    return await fn();\n  } finally {\n    lock.release();\n  }"
    },
    {
        "input": "export class AsyncBatch<T, R> {\n  private queue: T[] = [];\n  private processor!: (items: T[]) => Promise<R[]>;\n  private timer: NodeJS.Timeout | null = null;\n  \n  constructor(\n    private readonly batchSize: number,\n    private readonly delayMs: number,\n    processor: (items: T[]) => Promise<R[]>,\n  ) {\n    this.processor = processor;\n  }\n  \n  async add(item: T): Promise<R | null> {",
        "output": "this.queue.push(item);\n    if (this.queue.length >= this.batchSize) {\n      return this.flush();\n    }\n    if (!this.timer) {\n      this.timer = setTimeout(() => this.flush(), this.delayMs);\n    }\n    return null;"
    },
    {
        "input": "export class AsyncBatch<T, R> {\n  async flush(): Promise<R[]> {",
        "output": "if (this.timer) {\n      clearTimeout(this.timer);\n      this.timer = null;\n    }\n    if (this.queue.length === 0) return [];\n    const items = this.queue.splice(0);\n    return this.processor(items);"
    },
    # More data structures
    {
        "input": "export class BTreeNode<K, V> {\n  keys: K[] = [];\n  values: V[] = [];\n  children: BTreeNode<K, V>[] = [];\n  isLeaf: boolean = true;\n}\n\nexport class BTree<K, V> {\n  private root: BTreeNode<K, V>;\n  \n  constructor(private readonly t: number) {\n    this.root = new BTreeNode<K, V>();\n  }\n  \n  search(key: K): V | undefined {",
        "output": "let node = this.root;\n    while (true) {\n      const i = node.keys.findIndex(k => k >= key);\n      if (i >= 0 && node.keys[i] === key) {\n        return node.values[i];\n      }\n      if (node.isLeaf) return undefined;\n      node = node.children[i];\n    }"
    },
    {
        "input": "export class SkipListNode<T> {\n  forward: SkipListNode<T>[] = [];\n  \n  constructor(\n    public key: number,\n    public value: T,\n    public level: number,\n  ) {\n    this.forward = new Array(level + 1).fill(null!);\n  }\n}\n\nexport class SkipList<T> {\n  private head: SkipListNode<T>;\n  private level = 0;\n  private readonly maxLevel = 16;\n  \n  constructor() {\n    this.head = new SkipListNode<T>(-Infinity, undefined!, 0);\n  }\n  \n  private randomLevel(): number {",
        "output": "let lvl = 0;\n    while (Math.random() < 0.5 && lvl < this.maxLevel) lvl++;\n    return lvl;"
    },
    {
        "input": "export class SkipList<T> {\n  insert(key: number, value: T): void {",
        "output": "const update = new Array(this.maxLevel + 1).fill(this.head);\n    let node = this.head;\n    \n    for (let i = this.level; i >= 0; i--) {\n      while (node.forward[i] && node.forward[i].key < key) {\n        node = node.forward[i];\n      }\n      update[i] = node;\n    }\n    \n    node = node.forward[0];\n    if (node && node.key === key) {\n      node.value = value;\n      return;\n    }\n    \n    const lvl = this.randomLevel();\n    if (lvl > this.level) {\n      for (let i = this.level + 1; i <= lvl; i++) {\n        update[i] = this.head;\n      }\n      this.level = lvl;\n    }\n    \n    const newNode = new SkipListNode<T>(key, value, lvl);\n    for (let i = 0; i <= lvl; i++) {\n      newNode.forward[i] = update[i].forward[i];\n      update[i].forward[i] = newNode;\n    }"
    },
    # Parser patterns
    {
        "input": "export function parseJSONLogLine(line: string): LogEntry | null {",
        "output": "try {\n    const entry = JSON.parse(line);\n    return {\n      timestamp: entry.ts || entry.timestamp || Date.now(),\n      level: entry.level || 'info',\n      message: entry.msg || entry.message || '',\n      meta: entry.meta || {},\n    };\n  } catch {\n    return null;\n  }"
    },
    {
        "input": "export function parseCommandArgs(args: string[]): Record<string, string | boolean> {",
        "output": "const result: Record<string, string | boolean> = {};\n  let currentKey: string | null = null;\n  \n  for (const arg of args) {\n    if (arg.startsWith('--')) {\n      currentKey = arg.slice(2);\n      result[currentKey] = true;\n    } else if (arg.startsWith('-')) {\n      for (const char of arg.slice(1)) {\n        result[char] = true;\n      }\n    } else if (currentKey) {\n      result[currentKey] = arg;\n      currentKey = null;\n    }\n  }\n  \n  return result;"
    },
    {
        "input": "export function tokenizeTemplate(template: string): TemplateToken[] {",
        "output": "const tokens: TemplateToken[] = [];\n  const regex = /\\{\\{([^}]+)\\}\\}/g;\n  let lastIndex = 0;\n  let match;\n  \n  while ((match = regex.exec(template)) !== null) {\n    if (match.index > lastIndex) {\n      tokens.push({ type: 'text', value: template.slice(lastIndex, match.index) });\n    }\n    tokens.push({ type: 'variable', value: match[1].trim() });\n    lastIndex = regex.lastIndex;\n  }\n  \n  if (lastIndex < template.length) {\n    tokens.push({ type: 'text', value: template.slice(lastIndex) });\n  }\n  \n  return tokens;"
    },
    {
        "input": "export function renderTemplate(\n  template: string,\n  data: Record<string, any>,\n): string {",
        "output": "const tokens = tokenizeTemplate(template);\n  return tokens.map(token => {\n    if (token.type === 'text') return token.value;\n    const value = token.value.split('.').reduce((acc, key) => acc?.[key], data);\n    return value?.toString() ?? '';\n  }).join('');"
    },
    # Validation patterns
    {
        "input": "export function validateEmail(email: string): boolean {",
        "output": "const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;\n  return emailRegex.test(email);"
    },
    {
        "input": "export function validateUrl(url: string): boolean {",
        "output": "try {\n    new URL(url);\n    return true;\n  } catch {\n    return false;\n  }"
    },
    {
        "input": "export function validateSchema(\n  data: unknown,\n  schema: JSONSchema,\n): ValidationError[] {",
        "output": "const errors: ValidationError[] = [];\n  \n  if (schema.type === 'object') {\n    if (typeof data !== 'object' || data === null) {\n      errors.push({ path: '', message: 'Expected object' });\n      return errors;\n    }\n    for (const [key, propSchema] of Object.entries(schema.properties || {})) {\n      if ((schema.required || []).includes(key) && !(key in (data as object))) {\n        errors.push({ path: key, message: 'Required property missing' });\n      }\n    }\n  }\n  \n  return errors;"
    },
    # More OpenClaw patterns
    {
        "input": "export async function loadToolsFromSkill(\n  skillPath: string,\n): Promise<Tool[]> {",
        "output": "try {\n    const skill = await import(skillPath);\n    return skill.default?.tools || [];\n  } catch (e) {\n    console.error(`Failed to load skill from ${skillPath}:`, e);\n    return [];\n  }"
    },
    {
        "input": "export function formatToolResult(\n  result: ToolResult,\n  format: 'text' | 'json' = 'text',\n): string {",
        "output": "if (format === 'json') {\n    return JSON.stringify(result, null, 2);\n  }\n  if (!result.success) {\n    return `Error: ${result.error}`;\n  }\n  return typeof result.result === 'object'\n    ? JSON.stringify(result.result, null, 2)\n    : String(result.result);"
    },
    {
        "input": "export async function executeToolChain(\n  tools: Tool[],\n  initialInput: any,\n): Promise<ToolResult[]> {",
        "output": "const results: ToolResult[] = [];\n  let currentInput = initialInput;\n  \n  for (const tool of tools) {\n    const result = await executeTool(tool, { input: currentInput }, getDefaultContext());\n    results.push(result);\n    if (!result.success) break;\n    currentInput = result.result;\n  }\n  \n  return results;"
    },
    {
        "input": "export function createToolRouter(\n  tools: Map<string, Tool>,\n): ToolRouter {",
        "output": "return {\n    route(toolName: string): Tool | undefined {\n      return tools.get(toolName);\n    },\n    routeByPattern(pattern: string): Tool | undefined {\n      for (const [name, tool] of tools) {\n        if (name.includes(pattern) || tool.aliases?.some(a => a.includes(pattern))) {\n          return tool;\n        }\n      }\n      return undefined;\n    },\n  };"
    },
    {
        "input": "export class MemoryStore {\n  private entities: Map<string, MemoryEntity> = new Map();\n  private relations: Relation[] = [];\n  \n  async save(entity: MemoryEntity): Promise<void> {",
        "output": "this.entities.set(entity.name, {\n    ...entity,\n    updatedAt: Date.now(),\n  });"
    },
    {
        "input": "export class MemoryStore {\n  async search(query: string): Promise<MemoryEntity[]> {",
        "output": "const queryLower = query.toLowerCase();\n  const results: MemoryEntity[] = [];\n  \n  for (const entity of this.entities.values()) {\n    if (\n      entity.name.toLowerCase().includes(queryLower) ||\n      entity.observations.some(o => o.toLowerCase().includes(queryLower))\n    ) {\n      results.push(entity);\n    }\n  }\n  \n  return results;"
    },
    {
        "input": "export class MemoryStore {\n  async getRelations(\n    entityName: string,\n    relationType?: string,\n  ): Promise<Relation[]> {",
        "output": "return this.relations.filter(r =>\n    (r.from === entityName || r.to === entityName) &&\n    (!relationType || r.relationType === relationType)\n  );"
    },
    {
        "input": "export function buildContextWindow(\n  messages: Message[],\n  maxTokens: number,\n): Message[] {",
        "output": "let totalTokens = 0;\n  const result: Message[] = [];\n  \n  for (let i = messages.length - 1; i >= 0; i--) {\n    const msg = messages[i];\n    const tokens = estimateTokens(msg.content);\n    if (totalTokens + tokens > maxTokens) break;\n    result.unshift(msg);\n    totalTokens += tokens;\n  }\n  \n  return result;"
    },
    {
        "input": "export function estimateTokens(text: string): number {",
        "output": "return Math.ceil(text.length / 4);"
    },
    # Agent behavior patterns
    {
        "input": "export function detectIntent(input: string): Intent {",
        "output": "const lower = input.toLowerCase();\n  \n  if (lower.startsWith('/')) {\n    return { type: 'command', command: lower.slice(1).split(' ')[0] };\n  }\n  \n  if (/\\b(what is|who is|when|where|why|how)\\b/.test(lower)) {\n    return { type: 'question' };\n  }\n  \n  if (/(file|read|write|edit|create|delete)/.test(lower)) {\n    return { type: 'file_operation' };\n  }\n  \n  if (/\\b(run|execute|send|create)\\b/.test(lower)) {\n    return { type: 'action' };\n  }\n  \n  return { type: 'general' };"
    },
    {
        "input": "export function buildSystemPrompt(\n  config: AgentConfig,\n  context: Context,\n): string {",
        "output": "let prompt = config.systemPrompt || '';\n  prompt += '\\n\\nCurrent context:\\n';\n  prompt += `- Workspace: ${context.workspaceRoot}\\n`;\n  prompt += `- Current time: ${new Date().toISOString()}\\n`;\n  prompt += `- Available tools: ${context.tools.map(t => t.name).join(', ')}\\n`;\n  return prompt;"
    },
    {
        "input": "export async function streamToString(\n  stream: ReadableStream<string>,\n): Promise<string> {",
        "output": "let result = '';\n  const reader = stream.getReader();\n  \n  while (true) {\n    const { done, value } = await reader.read();\n    if (done) break;\n    result += value;\n  }\n  \n  return result;"
    },
    {
        "input": "export function parseFilePath(\n  relativePath: string,\n  workspaceRoot: string,\n): { fullPath: string; exists: boolean } {",
        "output": "const fullPath = path.join(workspaceRoot, relativePath);\n  return {\n    fullPath,\n    exists: fs.existsSync(fullPath),\n  };"
    },
    {
        "input": "export function watchDirectory(\n  dirPath: string,\n  callback: (event: FSWatcherEvent) => void,\n): FSWatcher {",
        "output": " const watcher = fs.watch(dirPath, { recursive: true }, (event, filename) => {\n    callback({ event, filename, path: path.join(dirPath, filename || '') });\n  });\n  return watcher;"
    },
    # More utility patterns
    {
        "input": "export function deepMerge<T extends object>(\n  target: T,\n  ...sources: Partial<T>[]\n): T {",
        "output": "for (const source of sources) {\n    for (const key in source) {\n      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {\n        if (!target[key]) Object.assign(target, { [key]: {} });\n        deepMerge(target[key] as object, source[key] as object);\n      } else {\n        Object.assign(target, { [key]: source[key] });\n      }\n    }\n  }\n  return target;"
    },
    {
        "input": "export function debounceImmediate<T extends (...args: any[]) => any>(\n  fn: T,\n  wait: number,\n): T {",
        "output": "let timeout: NodeJS.Timeout | null = null;\n  return ((...args: Parameters<T>) => {\n    if (timeout) clearTimeout(timeout);\n    timeout = setTimeout(() => { timeout = null; }, wait);\n    fn(...args);\n  }) as T;"
    },
    {
        "input": "export function chunkAsync<T, R>(\n  items: T[],\n  size: number,\n  fn: (chunk: T[]) => Promise<R[]>,\n): AsyncGenerator<R> {",
        "output": "let index = 0;\n  while (index < items.length) {\n    const chunk = items.slice(index, index + size);\n    const results = await fn(chunk);\n    yield* results;\n    index += size;\n  }"
    },
    {
        "input": "export function parseMarkdownTable(\n  markdown: string,\n): { headers: string[]; rows: string[][] } | null {",
        "output": "const lines = markdown.trim().split('\\n');\n  if (lines.length < 2) return null;\n  \n  const headers = lines[0].split('|').filter(c => c.trim()).map(c => c.trim());\n  const rows = lines.slice(2).map(line =>\n    line.split('|').filter(c => c.trim()).map(c => c.trim())\n  );\n  \n  return { headers, rows };"
    },
    {
        "input": "export function formatBytes(bytes: number): string {",
        "output": "if (bytes === 0) return '0 Bytes';\n  const k = 1024;\n  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];\n  const i = Math.floor(Math.log(bytes) / Math.log(k));\n  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];"
    },
    {
        "input": "export function formatDuration(ms: number): string {",
        "output": "if (ms < 1000) return `${ms}ms`;\n  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;\n  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;\n  return `${(ms / 3600000).toFixed(1)}h`;"
    },
    {
        "input": "export function formatRelativeTime(timestamp: number): string {",
        "output": "const diff = Date.now() - timestamp;\n  if (diff < 60000) return 'just now';\n  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;\n  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;\n  return `${Math.floor(diff / 86400000)}d ago`;"
    },
    {
        "input": "export function parseEnvironment(env: Record<string, string>): Config {",
        "output": "return {\n    port: parseInt(env.PORT || '3000', 10),\n    host: env.HOST || 'localhost',\n    debug: env.DEBUG === 'true',\n    logLevel: env.LOG_LEVEL || 'info',\n    databaseUrl: env.DATABASE_URL,\n    apiKey: env.API_KEY,\n  };"
    },
    {
        "input": "export function createLogger(prefix: string): Logger {",
        "output": " return {\n    info: (msg: string, meta?: object) => console.log(`[${prefix}]`, msg, meta || {}),\n    warn: (msg: string, meta?: object) => console.warn(`[${prefix}]`, msg, meta || {}),\n    error: (msg: string, meta?: object) => console.error(`[${prefix}]`, msg, meta || {}),\n    debug: (msg: string, meta?: object) => console.debug(`[${prefix}]`, msg, meta || {}),\n  };"
    },
    {
        "input": "export async function readDirRecursive(\n  dir: string,\n): Promise<string[]> {",
        "output": "const results: string[] = [];\n  const entries = await readdir(dir, { withFileTypes: true });\n  \n  for (const entry of entries) {\n    const fullPath = path.join(dir, entry.name);\n    if (entry.isDirectory()) {\n      results.push(...await readDirRecursive(fullPath));\n    } else {\n      results.push(fullPath);\n    }\n  }\n  \n  return results;"
    },
    {
        "input": "export async function copyDirectory(\n  src: string,\n  dest: string,\n): Promise<void> {",
        "output": "await mkdir(dest, { recursive: true });\n  const entries = await readdir(src, { withFileTypes: true });\n  \n  for (const entry of entries) {\n    const srcPath = path.join(src, entry.name);\n    const destPath = path.join(dest, entry.name);\n    \n    if (entry.isDirectory()) {\n      await copyDirectory(srcPath, destPath);\n    } else {\n      await copyFile(srcPath, destPath);\n    }\n  }"
    },
    {
        "input": "export async function walkDirectory(\n  root: string,\n  callback: (file: string, stats: Stats) => void | Promise<void>,\n): Promise<void> {",
        "output": "const entries = await readdir(root, { withFileTypes: true });\n  \n  for (const entry of entries) {\n    const fullPath = path.join(root, entry.name);\n    const stats = await stat(fullPath);\n    \n    await callback(fullPath, stats);\n    \n    if (entry.isDirectory()) {\n      await walkDirectory(fullPath, callback);\n    }\n  }"
    },
    {
        "input": "export function findFiles(\n  dir: string,\n  pattern: RegExp,\n): string[] {",
        "output": "const results: string[] = [];\n  const entries = readdirSync(dir, { withFileTypes: true });\n  \n  for (const entry of entries) {\n    const fullPath = path.join(dir, entry.name);\n    if (entry.isDirectory()) {\n      results.push(...findFiles(fullPath, pattern));\n    } else if (pattern.test(entry.name)) {\n      results.push(fullPath);\n    }\n  }\n  \n  return results;"
    },
    {
        "input": "export function matchGlob(\n  filename: string,\n  pattern: string,\n): boolean {",
        "output": "const regexPattern = pattern\n    .replace(/[.+^${}()|[\\]\\\\]/g, '\\\\$&')\n    .replace(/\\*/g, '.*')\n    .replace(/\\?/g, '.');\n  \n  return new RegExp(`^${regexPattern}$`, 'i').test(filename);"
    },
    {
        "input": "export function parseGlob(pattern: string): { base: string; glob: string } {",
        "output": "const starIndex = pattern.indexOf('*');\n  if (starIndex === -1) return { base: pattern, glob: '' };\n  \n  const lastSlash = pattern.lastIndexOf('/', starIndex);\n  return {\n    base: lastSlash === -1 ? '.' : pattern.slice(0, lastSlash),\n    glob: pattern.slice(lastSlash + 1),\n  };"
    },
    {
        "input": "export function resolveRelativePath(\n  base: string,\n  relative: string,\n): string {",
        "output": "const baseParts = base.split('/');\n  const relParts = relative.split('/');\n  \n  for (const part of relParts) {\n    if (part === '..') {\n      baseParts.pop();\n    } else if (part !== '.') {\n      baseParts.push(part);\n    }\n  }\n  \n  return baseParts.join('/');"
    },
    {
        "input": "export function normalizePath(path: string): string {",
        "output": "return path\n    .replace(/\\\\+/g, '/')\n    .replace(/\\/+/g, '/')\n    .replace(/^\\.\\//, '')\n    .replace(/\\/\\.\\//g, '/');"
    },
    {
        "input": "export function isSubPath(parent: string, child: string): boolean {",
        "output": "const rel = path.relative(parent, child);\n  return !rel.startsWith('..') && !path.isAbsolute(rel);"
    },
    {
        "input": "export function getCommonPath(paths: string[]): string {",
        "output": "if (paths.length === 0) return '';\n  if (paths.length === 1) return path.dirname(paths[0]);\n  \n  const parts = paths.map(p => p.split('/'));\n  const common: string[] = [];\n  \n  for (let i = 0; i < parts[0].length; i++) {\n    const part = parts[0][i];\n    if (parts.every(p => p[i] === part)) {\n      common.push(part);\n    } else {\n      break;\n    }\n  }\n  \n  return common.join('/');"
    },
    {
        "input": "export function sanitizeFilename(filename: string): string {",
        "output": "return filename\n    .replace(/[^\\w\\s.-]/g, '')\n    .replace(/[\\s]+/g, '-')\n    .toLowerCase();"
    },
    {
        "input": "export function getExtension(filename: string): string {",
        "output": "const lastDot = filename.lastIndexOf('.');\n  return lastDot === -1 ? '' : filename.slice(lastDot + 1);"
    },
    {
        "input": "export function stripExtension(filename: string): string {",
        "output": "const lastDot = filename.lastIndexOf('.');\n  return lastDot === -1 ? filename : filename.slice(0, lastDot);"
    },
    {
        "input": "export function changeExtension(filename: string, newExt: string): string {",
        "output": " const oldExt = getExtension(filename);\n  const base = oldExt ? filename.slice(0, -oldExt.length) : filename;\n  return newExt ? base + '.' + newExt : base;"
    },
    {
        "input": "export function listDir(dir: string): string[] {",
        "output": "return readdirSync(dir);"
    },
    {
        "input": "export function fileExists(path: string): boolean {",
        "output": "try {\n    statSync(path);\n    return true;\n  } catch {\n    return false;\n  }"
    },
    {
        "input": "export function dirExists(path: string): boolean {",
        "output": "try {\n    const stats = statSync(path);\n    return stats.isDirectory();\n  } catch {\n    return false;\n  }"
    },
    {
        "input": "export function getFileSize(path: string): number {",
        "output": "return statSync(path).size;"
    },
    {
        "input": "export function getFileModifiedTime(path: string): number {",
        "output": "return statSync(path).mtimeMs;"
    },
    {
        "input": "export async function readJSONFile<T>(path: string): Promise<T> {",
        "output": "const content = await readFile(path, 'utf-8');\n  return JSON.parse(content) as T;"
    },
    {
        "input": "export async function writeJSONFile<T>(\n  path: string,\n  data: T,\n): Promise<void> {",
        "output": "const content = JSON.stringify(data, null, 2);\n  await writeFile(path, content, 'utf-8');"
    },
    {
        "input": "export async function appendToFile(\n  path: string,\n  content: string,\n): Promise<void> {",
        "output": "await appendFile(path, content, 'utf-8');"
    },
    {
        "input": "export function readFileSync(path: string): string {",
        "output": "return fs.readFileSync(path, 'utf-8');"
    },
    {
        "input": "export function writeFileSync(path: string, content: string): void {",
        "output": "fs.writeFileSync(path, content, 'utf-8');"
    },
    {
        "input": "export async function createTempFile(\n  content: string,\n  ext?: string,\n): Promise<string> {",
        "output": "const tmp = await mkdtemp(tmpdir + '/');\n  const file = path.join(tmp, `file${ext || '.txt'}`);\n  await writeFile(file, content, 'utf-8');\n  return file;"
    },
    {
        "input": "export async function withTempFile<T>(\n  content: string,\n  ext: string,\n  fn: (path: string) => Promise<T>,\n): Promise<T> {",
        "output": "const file = await createTempFile(content, ext);\n  try {\n    return await fn(file);\n  } finally {\n    await unlink(file);\n  }"
    },
    {
        "input": "export function matchPattern(\n  text: string,\n  pattern: string | RegExp,\n): RegExpMatchArray | null {",
        "output": "if (typeof pattern === 'string') {\n    pattern = new RegExp(pattern);\n  }\n  return text.match(pattern);"
    },
    {
        "input": "export function extractMatches(\n  text: string,\n  pattern: RegExp,\n): string[] {",
        "output": " const matches: string[] = [];\n  let match;\n  while ((match = pattern.exec(text)) !== null) {\n    matches.push(match[0]);\n    if (!pattern.global) break;\n  }\n  return matches;"
    },
    {
        "input": "export function replaceAll(\n  text: string,\n  search: string,\n  replace: string,\n): string {",
        "output": "return text.split(search).join(replace);"
    },
    {
        "input": "export function camelToSnake(str: string): string {",
        "output": "return str.replace(/[A-Z]/g, c => '_' + c.toLowerCase());"
    },
    {
        "input": "export function snakeToCamel(str: string): string {",
        "output": "return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());"
    },
    {
        "input": "export function kebabToCamel(str: string): string {",
        "output": "return str.replace(/-([a-z])/g, (_, c) => c.toUpperCase());"
    },
    {
        "input": "export function pascalCase(str: string): string {",
        "output": "return str.replace(/(?:^|[-_\\s]+)([a-z])/g, (_, c) => c.toUpperCase());"
    },
    {
        "input": "export function pluralize(word: string): string {",
        "output": "if (word.endsWith('y')) return word.slice(0, -1) + 'ies';\n  if (word.endsWith('s') || word.endsWith('x') || word.endsWith('z')) return word + 'es';\n  if (word.endsWith('f')) return word.slice(0, -1) + 'ves';\n  if (word.endsWith('fe')) return word.slice(0, -2) + 'ves';\n  return word + 's';"
    },
    {
        "input": "export function singularize(word: string): string {",
        "output": "if (word.endsWith('ies')) return word.slice(0, -3) + 'y';\n  if (word.endsWith('es')) return word.slice(0, -2);\n  if (word.endsWith('s') && !word.endsWith('ss')) return word.slice(0, -1);\n  return word;"
    },
    {
        "input": "export function toWords(str: string): string[] {",
        "output": "return str\n    .replace(/([A-Z])/g, ' $1')\n    .toLowerCase()\n    .split(/[\\s_-]+/)\n    .filter(Boolean);"
    },
    {
        "input": "export function repeat(str: string, count: number): string {",
        "output": "return str.repeat(count);"
    },
    {
        "input": "export function padCenter(str: string, length: number, char: string = ' '): string {",
        "output": "const padLen = Math.max(0, length - str.length);\n  const leftPad = Math.floor(padLen / 2);\n  const rightPad = padLen - leftPad;\n  return char.repeat(leftPad) + str + char.repeat(rightPad);"
    },
    {
        "input": "export function wordWrap(str: string, maxWidth: number): string[] {",
        "output": "const words = str.split(' ');\n  const lines: string[] = [];\n  let currentLine = '';\n  \n  for (const word of words) {\n    if (currentLine.length + word.length + 1 > maxWidth) {\n      if (currentLine) lines.push(currentLine.trim());\n      currentLine = word;\n    } else {\n      currentLine += (currentLine ? ' ' : '') + word;\n    }\n  }\n  \n  if (currentLine) lines.push(currentLine.trim());\n  return lines;"
    },
    {
        "input": "export function levenshteinDistance(a: string, b: string): number {",
        "output": "if (!a.length) return b.length;\n  if (!b.length) return a.length;\n  \n  const matrix = Array(a.length + 1).fill(null).map(() => Array(b.length + 1).fill(0));\n  \n  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;\n  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;\n  \n  for (let i = 1; i <= a.length; i++) {\n    for (let j = 1; j <= b.length; j++) {\n      const cost = a[i - 1] === b[j - 1] ? 0 : 1;\n      matrix[i][j] = Math.min(\n        matrix[i - 1][j] + 1,\n        matrix[i][j - 1] + 1,\n        matrix[i - 1][j - 1] + cost\n      );\n    }\n  }\n  \n  return matrix[a.length][b.length];"
    },
    {
        "input": "export function similarity(a: string, b: string): number {",
        "output": "const maxLen = Math.max(a.length, b.length);\n  if (maxLen === 0) return 1;\n  return 1 - levenshteinDistance(a, b) / maxLen;"
    },
    {
        "input": "export function randomString(length: number): string {",
        "output": "const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';\n  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('');"
    },
    {
        "input": "export function randomAlphanumeric(length: number): string {",
        "output": "return randomString(length);"
    },
    {
        "input": "export function randomHex(length: number): string {",
        "output": "return Array.from({ length }, () => Math.floor(Math.random() * 16).toString(16)).join('');"
    },
    {
        "input": "export function randomUUID(): string {",
        "output": "return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {\n    const r = Math.random() * 16 | 0;\n    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);\n  });"
    },
    {
        "input": "export function hashCode(str: string): number {",
        "output": "let hash = 0;\n  for (let i = 0; i < str.length; i++) {\n    const char = str.charCodeAt(i);\n    hash = ((hash << 5) - hash) + char;\n    hash = hash & hash;\n  }\n  return hash;"
    },
    {
        "input": "export function murmurhash(str: string): number {",
        "output": "let h = 0;\n  for (let i = 0; i < str.length; i++) {\n    h ^= str.charCodeAt(i);\n    h = (h * 0x5bd1e995) >>> 0;\n  }\n  return h >>> 0;"
    },
    {
        "input": "export function base64Encode(str: string): string {",
        "output": "return Buffer.from(str, 'utf-8').toString('base64');"
    },
    {
        "input": "export function base64Decode(str: string): string {",
        "output": "return Buffer.from(str, 'base64').toString('utf-8');"
    },
    {
        "input": "export function urlEncode(str: string): string {",
        "output": "return encodeURIComponent(str);"
    },
    {
        "input": "export function urlDecode(str: string): string {",
        "output": "return decodeURIComponent(str);"
    },
    {
        "input": "export function htmlEncode(str: string): string {",
        "output": " return str\n    .replace(/&/g, '&amp;')\n    .replace(/</g, '&lt;')\n    .replace(/>/g, '&gt;')\n    .replace(/\"/g, '&quot;')\n    .replace(/'/g, '&#39;');"
    },
    {
        "input": "export function htmlDecode(str: string): string {",
        "output": "return str\n    .replace(/&amp;/g, '&')\n    .replace(/&lt;/g, '<')\n    .replace(/&gt;/g, '>')\n    .replace(/&quot;/g, '\"')\n    .replace(/&#39;/g, \"'\");"
    },
    {
        "input": "export function escapeShellArg(str: string): string {",
        "output": "return \"'\" + str.replace(/'/g, \"'\\\\''\") + \"'\";"
    },
    {
        "input": "export function unescapeShellArg(str: string): string {",
        "output": "if (str.startsWith(\"'\") && str.endsWith(\"'\")) {\n    return str.slice(1, -1).replace(/\\\\'/g, \"'\");\n  }\n  return str;"
    },
    {
        "input": "export function parseHexColor(hex: string): { r: number; g: number; b: number } | null {",
        "output": "const match = hex.match(/^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i);\n  if (!match) return null;\n  return {\n    r: parseInt(match[1], 16),\n    g: parseInt(match[2], 16),\n    b: parseInt(match[3], 16),\n  };"
    },
    {
        "input": "export function rgbToHex(r: number, g: number, b: number): string {",
        "output": "return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');"
    },
    {
        "input": "export function hslToRgb(h: number, s: number, l: number): { r: number; g: number; b: number } {",
        "output": "const c = (1 - Math.abs(2 * l - 1)) * s;\n  const x = c * (1 - Math.abs((h / 60) % 2 - 1));\n  const m = l - c / 2;\n  \n  let r = 0, g = 0, b = 0;\n  if (h < 60) { r = c; g = x; }\n  else if (h < 120) { r = x; g = c; }\n  else if (h < 180) { g = c; b = x; }\n  else if (h < 240) { g = x; b = c; }\n  else if (h < 300) { r = x; b = c; }\n  else { r = c; b = x; }\n  \n  return {\n    r: Math.round((r + m) * 255),\n    g: Math.round((g + m) * 255),\n    b: Math.round((b + m) * 255),\n  };"
    },
    {
        "input": "export function clamp(value: number, min: number, max: number): number {",
        "output": "return Math.min(Math.max(value, min), max);"
    },
    {
        "input": "export function lerp(a: number, b: number, t: number): number {",
        "output": "return a + (b - a) * t;"
    },
    {
        "input": "export function mapRange(\n  value: number,\n  inMin: number,\n  inMax: number,\n  outMin: number,\n  outMax: number,\n): number {",
        "output": "return outMin + ((value - inMin) / (inMax - inMin)) * (outMax - outMin);"
    },
    {
        "input": "export function sign(value: number): number {",
        "output": "return value < 0 ? -1 : value > 0 ? 1 : 0;"
    },
    {
        "input": "export function roundTo(value: number, nearest: number): number {",
        "output": "return Math.round(value / nearest) * nearest;"
    },
    {
        "input": "export function isEven(n: number): boolean {",
        "output": "return n % 2 === 0;"
    },
    {
        "input": "export function isOdd(n: number): boolean {",
        "output": "return n % 2 !== 0;"
    },
    {
        "input": "export function gcd(a: number, b: number): number {",
        "output": "return b === 0 ? a : gcd(b, a % b);"
    },
    {
        "input": "export function lcm(a: number, b: number): number {",
        "output": "return Math.abs(a * b) / gcd(a, b);"
    },
    {
        "input": "export function factorial(n: number): number {",
        "output": "if (n <= 1) return 1;\n  return n * factorial(n - 1);"
    },
    {
        "input": "export function fibonacci(n: number): number {",
        "output": "if (n <= 1) return n;\n  let a = 0, b = 1;\n  for (let i = 2; i <= n; i++) {\n    [a, b] = [b, a + b];\n  }\n  return b;"
    },
    {
        "input": "export function isPrime(n: number): boolean {",
        "output": "if (n < 2) return false;\n  if (n === 2) return true;\n  if (n % 2 === 0) return false;\n  for (let i = 3; i <= Math.sqrt(n); i += 2) {\n    if (n % i === 0) return false;\n  }\n  return true;"
    },
    {
        "input": "export function primesUpTo(n: number): number[] {",
        "output": "const result: number[] = [];\n  for (let i = 2; i <= n; i++) {\n    if (isPrime(i)) result.push(i);\n  }\n  return result;"
    },
    {
        "input": "export function isPowerOfTwo(n: number): boolean {",
        "output": "return n > 0 && (n & (n - 1)) === 0;"
    },
    {
        "input": "export function nextPowerOfTwo(n: number): number {",
        "output": "if (n <= 0) return 1;\n  return Math.pow(2, Math.ceil(Math.log2(n)));"
    },
    {
        "input": "export function bitCount(n: number): number {",
        "output": "n = n - ((n >>> 1) & 0x55555555);\n  n = (n & 0x33333333) + ((n >>> 2) & 0x33333333);\n  n = (n + (n >>> 4)) & 0x0f0f0f0f;\n  n = n + (n >>> 8);\n  n = n + (n >>> 16);\n  return n & 0x3f;"
    },
    {
        "input": "export function reverseBits(n: number, bits: number = 32): number {",
        "output": "let result = 0;\n  for (let i = 0; i < bits; i++) {\n    result = (result << 1) | (n & 1);\n    n >>>= 1;\n  }\n  return result;"
    },
    {
        "input": "export function swapBits(n: number, i: number, j: number): number {",
        "output": "const bit1 = (n >>> i) & 1;\n  const bit2 = (n >>> j) & 1;\n  if (bit1 === bit2) return n;\n  const mask = (1 << i) | (1 << j);\n  return n ^ mask;"
    },
    {
        "input": "export function parseBoolean(value: any): boolean {",
        "output": "if (typeof value === 'boolean') return value;\n  if (typeof value === 'string') {\n    return value.toLowerCase() === 'true' || value === '1' || value === 'yes';\n  }\n  return Boolean(value);"
    },
    {
        "input": "export function defaultTo<T>(value: T | null | undefined, defaultValue: T): T {",
        "output": "return value ?? defaultValue;"
    },
    {
        "input": "export function or<T>(value: T | null | undefined, fallback: T): T {",
        "output": "return value || fallback;"
    },
    {
        "input": "export function isNullOrUndefined(value: any): value is null | undefined {",
        "output": "return value == null;"
    },
    {
        "input": "export function isEmptyString(value: any): boolean {",
        "output": "return value === '' || value == null;"
    },
    {
        "input": "export function isValidNumber(value: any): boolean {",
        "output": "return typeof value === 'number' && !isNaN(value) && isFinite(value);"
    },
    {
        "input": "export function coerceNumber(value: any, fallback: number = 0): number {",
        "output": "const num = Number(value);\n  return isValidNumber(num) ? num : fallback;"
    },
    {
        "input": "export function coerceArray<T>(value: any): T[] {",
        "output": "return Array.isArray(value) ? value : value != null ? [value] : [];"
    },
    {
        "input": "export function coerceObject<T extends object>(value: any): T {",
        "output": "return typeof value === 'object' && value !== null ? value : {} as T;"
    },
    {
        "input": "export function mergeDefaults<T extends object>(\n  defaults: T,\n  overrides: Partial<T>,\n): T {",
        "output": " return { ...defaults, ...overrides };"
    },
    {
        "input": "export function removeNil<T>(array: (T | null | undefined)[]): T[] {",
        "output": "return array.filter((item): item is T => item != null);"
    },
    {
        "input": "export function uniqueBy<T>(\n  array: T[],\n  keyFn: (item: T) => string,\n): T[] {",
        "output": "const seen = new Set<string>();\n  return array.filter(item => {\n    const key = keyFn(item);\n    if (seen.has(key)) return false;\n    seen.add(key);\n    return true;\n  });"
    },
    {
        "input": "export function groupByKey<T>(\n  array: T[],\n  keyFn: (item: T) => string,\n): Record<string, T[]> {",
        "output": " return array.reduce((acc, item) => {\n    const key = keyFn(item);\n    if (!acc[key]) acc[key] = [];\n    acc[key].push(item);\n    return acc;\n  }, {} as Record<string, T[]>);"
    },
    {
        "input": "export function sortByKey<T>(\n  array: T[],\n  keyFn: (item: T) => number | string,\n  order: 'asc' | 'desc' = 'asc',\n): T[] {",
        "output": " return [...array].sort((a, b) => {\n    const aKey = keyFn(a);\n    const bKey = keyFn(b);\n    const cmp = aKey < bKey ? -1 : aKey > bKey ? 1 : 0;\n    return order === 'asc' ? cmp : -cmp;\n  });"
    },
    {
        "input": "export function pluck<T extends object, K extends keyof T>(\n  array: T[],\n  key: K,\n): T[K][] {",
        "output": "return array.map(item => item[key]);"
    },
    {
        "input": "export function where<T extends object>(\n  array: T[],\n  predicate: Partial<T>,\n): T[] {",
        "output": "return array.filter(item =>\n    Object.entries(predicate).every(([k, v]) => item[k as keyof T] === v)\n  );"
    },
    {
        "input": "export function findWhere<T extends object>(\n  array: T[],\n  predicate: Partial<T>,\n): T | undefined {",
        "output": "return array.find(item =>\n    Object.entries(predicate).every(([k, v]) => item[k as keyof T] === v)\n  );"
    },
    {
        "input": "export function reject<T>(\n  array: T[],\n  predicate: (item: T) => boolean,\n): T[] {",
        "output": "return array.filter(item => !predicate(item));"
    },
    {
        "input": "export function compactMap<T, R>(\n  array: T[],\n  fn: (item: T) => R | null | undefined,\n): R[] {",
        "output": " return array.map(fn).filter((item): item is R => item != null);"
    },
    {
        "input": "export function flatMap<T, R>(\n  array: T[],\n  fn: (item: T) => R[],\n): R[] {",
        "output": "return array.reduce<R[]>((acc, item) => acc.concat(fn(item)), []);"
    },
    {
        "input": "export function intersperse<T>(array: T[], separator: T): T[] {",
        "output": "return array.flatMap(item => [item, separator]).slice(0, -1);"
    },
    {
        "input": "export function interleave<T>(...arrays: T[][]): T[] {",
        "output": "const result: T[] = [];\n  const maxLen = Math.max(...arrays.map(a => a.length));\n  for (let i = 0; i < maxLen; i++) {\n    for (const arr of arrays) {\n      if (i < arr.length) result.push(arr[i]);\n    }\n  }\n  return result;"
    },
    {
        "input": "export function transpose<T>(matrix: T[][]): T[][] {",
        "output": "if (!matrix.length) return [];\n  return matrix[0].map((_, i) => matrix.map(row => row[i]));"
    },
    {
        "input": "export function zipAll<T>(...arrays: (T | undefined)[][]): T[][] {",
        "output": "const maxLen = Math.max(...arrays.map(a => a.length));\n  return Array.from({ length: maxLen }, (_, i) =>\n    arrays.map(arr => arr[i])\n  );"
    },
    {
        "input": "export function range(start: number, end?: number, step: number = 1): number[] {",
        "output": "if (end === undefined) {\n    end = start;\n    start = 0;\n  }\n  const result: number[] = [];\n  for (let i = start; step > 0 ? i < end : i > end; i += step) {\n    result.push(i);\n  }\n  return result;"
    },
    {
        "input": "export function sum(nums: number[]): number {",
        "output": "return nums.reduce((a, b) => a + b, 0);"
    },
    {
        "input": "export function product(nums: number[]): number {",
        "output": "return nums.reduce((a, b) => a * b, 1);"
    },
    {
        "input": "export function average(nums: number[]): number {",
        "output": "return nums.length ? sum(nums) / nums.length : 0;"
    },
    {
        "input": "export function median(nums: number[]): number {",
        "output": "const sorted = [...nums].sort((a, b) => a - b);\n  const mid = Math.floor(sorted.length / 2);\n  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;"
    },
    {
        "input": "export function mode(nums: number[]): number {",
        "output": "const counts = new Map<number, number>();\n  let maxCount = 0;\n  let modeValue = nums[0];\n  for (const num of nums) {\n    const count = (counts.get(num) || 0) + 1;\n    counts.set(num, count);\n    if (count > maxCount) {\n      maxCount = count;\n      modeValue = num;\n    }\n  }\n  return modeValue;"
    },
    {
        "input": "export function variance(nums: number[]): number {",
        "output": "const avg = average(nums);\n  return average(nums.map(n => Math.pow(n - avg, 2)));"
    },
    {
        "input": "export function stdDev(nums: number[]): number {",
        "output": "return Math.sqrt(variance(nums));"
    },
    {
        "input": "export function percentile(nums: number[], p: number): number {",
        "output": "const sorted = [...nums].sort((a, b) => a - b);\n  const index = (p / 100) * (sorted.length - 1);\n  const lower = Math.floor(index);\n  const upper = Math.ceil(index);\n  const weight = index - lower;\n  return sorted[lower] * (1 - weight) + sorted[upper] * weight;"
    },
    {
        "input": "export function min(nums: number[]): number | undefined {",
        "output": "return nums.length ? Math.min(...nums) : undefined;"
    },
    {
        "input": "export function max(nums: number[]): number | undefined {",
        "output": "return nums.length ? Math.max(...nums) : undefined;"
    },
    {
        "input": "export function minMax(nums: number[]): [number, number] | undefined {",
        "output": "if (!nums.length) return undefined;\n  return [Math.min(...nums), Math.max(...nums)];"
    },
    {
        "input": "export function clamp(nums: number[], min: number, max: number): number[] {",
        "output": "return nums.map(n => Math.min(Math.max(n, min), max));"
    },
    {
        "input": "export function normalize(nums: number[]): number[] {",
        "output": "const [min, max] = minMax(nums) || [0, 1];\n  return nums.map(n => (n - min) / (max - min));"
    },
    {
        "input": "export function movingAverage(nums: number[], window: number): number[] {",
        "output": "const result: number[] = [];\n  for (let i = 0; i <= nums.length - window; i++) {\n    const slice = nums.slice(i, i + window);\n    result.push(average(slice));\n  }\n  return result;"
    },
    {
        "input": "export function exponentialMovingAverage(\n  nums: number[],\n  alpha: number = 0.3,\n): number[] {",
        "output": "const result: number[] = [nums[0]];\n  for (let i = 1; i < nums.length; i++) {\n    result.push(alpha * nums[i] + (1 - alpha) * result[i - 1]);\n  }\n  return result;"
    },
    {
        "input": "export function cumulativeSum(nums: number[]): number[] {",
        "output": "let sum = 0;\n  return nums.map(n => sum += n);"
    },
    {
        "input": "export function differences(nums: number[]): number[] {",
        "output": "return nums.slice(1).map((n, i) => n - nums[i]);"
    },
    {
        "input": "export function ratio(a: number, b: number): number {",
        "output": "return b !== 0 ? a / b : 0;"
    },
    {
        "input": "export function percentage(value: number, total: number): number {",
        "output": "return total !== 0 ? (value / total) * 100 : 0;"
    },
    {
        "input": "export function percentOf(part: number, whole: number): number {",
        "output": "return percentage(part, whole);"
    },
    {
        "input": "export function percentChange(oldValue: number, newValue: number): number {",
        "output": "return oldValue !== 0 ? ((newValue - oldValue) / oldValue) * 100 : 0;"
    },
    {
        "input": "export function compound(principal: number, rate: number, times: number): number {",
        "output": "return principal * Math.pow(1 + rate / 100, times);"
    },
    {
        "input": "export function compoundMonthly(\n  principal: number,\n  annualRate: number,\n  months: number,\n): number {",
        "output": " const monthlyRate = annualRate / 100 / 12;\n  return principal * Math.pow(1 + monthlyRate, months);"
    },
    {
        "input": "export function compoundContinuous(\n  principal: number,\n  rate: number,\n  time: number,\n): number {",
        "output": "return principal * Math.exp(rate * time);"
    },
    {
        "input": "export function pmt(\n  principal: number,\n  monthlyRate: number,\n  months: number,\n): number {",
        "output": "if (monthlyRate === 0) return principal / months;\n  return (\n    (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) /\n    (Math.pow(1 + monthlyRate, months) - 1)\n  );"
    },
]

def generate_examples():
    """Generate additional examples to reach 1000 total."""
    examples = []
    
    for pattern in TS_PATTERNS_MORE:
        examples.append({
            "prompt": pattern["input"],
            "completion": pattern["output"]
        })
    
    return examples

def main():
    current_count = 386  # What we have from the first file
    
    # Generate more examples
    new_examples = generate_examples()
    
    print(f"Current examples: {current_count}")
    print(f"Generating {len(new_examples)} more examples...")
    
    # Append to file
    output_path = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/generated/code_completion_batch_01.jsonl"
    
    with open(output_path, 'a') as f:
        for example in new_examples:
            record = {
                "prompt": example["prompt"],
                "completion": example["completion"]
            }
            f.write(json.dumps(record) + "\n")
    
    # Verify
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    print(f"Total examples now: {len(lines)}")

if __name__ == "__main__":
    main()
