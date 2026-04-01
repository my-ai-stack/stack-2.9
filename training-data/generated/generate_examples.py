#!/usr/bin/env python3
"""
Generate 1,000 diverse code completion examples for Stack 2.9 training.
Based on patterns from OpenClaw codebase (agents, tools, async patterns).
"""

import json
import random

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# TypeScript/TSX Code Completion Patterns
# ============================================================================

TS_PATTERNS = [
    # Async Queue patterns
    {
        "input": '''export class AsyncQueue<T> {
  private queue: T[] = []
  private waiting: Array<(value: T) => void> = []

  async enqueue(item: T): Promise<void> {''',
        "output": '''if (this.waiting.length > 0) {
      const resolve = this.waiting.shift()!
      resolve(item)
    } else {
      this.queue.push(item)
    }''',
        "metadata": {"language": "typescript", "pattern": "async_queue_enqueue", "complexity": "medium"}
    },
    {
        "input": '''export class AsyncQueue<T> {
  private queue: T[] = []
  private waiting: Array<(value: T) => void> = []

  async dequeue(): Promise<T> {''',
        "output": '''if (this.queue.length > 0) {
      return this.queue.shift()!
    }
    return new Promise(resolve => {
      this.waiting.push(resolve)
    })''',
        "metadata": {"language": "typescript", "pattern": "async_queue_dequeue", "complexity": "medium"}
    },
    
    # LRUCache patterns
    {
        "input": '''export class LRUCache<K, V> {
  private cache = new Map<K, V>();
  
  constructor(private readonly maxSize: number) {}
  
  get(key: K): V | undefined {''',
        "output": '''if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key)!;
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;''',
        "metadata": {"language": "typescript", "pattern": "lru_cache_get", "complexity": "medium"}
    },
    {
        "input": '''export class LRUCache<K, V> {
  private cache = new Map<K, V>();
  
  set(key: K, value: V): void {
    if (this.cache.has(key)) this.cache.delete(key);
    else if (this.cache.size >= this.maxSize) {''',
        "output": '''const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);''',
        "metadata": {"language": "typescript", "pattern": "lru_cache_eviction", "complexity": "medium"}
    },
    
    # Debounce/Throttle
    {
        "input": '''export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);''',
        "output": '''timeout = setTimeout(() => func(...args), wait);''',
        "metadata": {"language": "typescript", "pattern": "debounce_timeout", "complexity": "simple"}
    },
    {
        "input": '''export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  return (...args: Parameters<T>) => {''',
        "output": '''if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }''',
        "metadata": {"language": "typescript", "pattern": "throttle", "complexity": "medium"}
    },
    
    # Retry patterns
    {
        "input": '''export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number
    delay?: number
    backoff?: number
  } = {},
): Promise<T> {
  const { maxAttempts = 3, delay = 1000, backoff = 2 } = options;
  let lastError: Error | undefined;
  let currentDelay = delay;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {''',
        "output": '''return await fn()
    } catch (e) {
      lastError = e as Error;
      if (attempt < maxAttempts) {
        await new Promise(r => setTimeout(r, currentDelay));
        currentDelay *= backoff;
      }
    }
  }
  throw lastError''',
        "metadata": {"language": "typescript", "pattern": "retry_loop", "complexity": "high"}
    },
    
    # Generator patterns
    {
        "input": '''export function* getChunks<T>(
  items: T[],
  chunkSize: number,
): Generator<T[]> {
  for (let i = 0; i < items.length; i += chunkSize) {''',
        "output": '''yield items.slice(i, i + chunkSize);''',
        "metadata": {"language": "typescript", "pattern": "chunk_generator", "complexity": "simple"}
    },
    {
        "input": '''export async function* readLinesReverse(
  filePath: string,
): AsyncGenerator<string> {
  const fileHandle = await open(filePath, 'r');
  const stat = await fileHandle.stat();
  let remaining = stat.size;
  let position = stat.size;
  let line = '';
  while (position > 0) {''',
        "output": '''position--;
    const buffer = Buffer.alloc(1);
    await fileHandle.read(buffer, 0, 1, position);
    const char = buffer.toString();
    if (char === '\\n') {
      if (line) yield line.split('').reverse().join('');
      line = '';
    } else {
      line += char;
    }
  }
  if (line) yield line.split('').reverse().join('');''',
        "metadata": {"language": "typescript", "pattern": "read_lines_reverse", "complexity": "high"}
    },
    
    # Memory/Tool patterns
    {
        "input": '''export async function parseHistoryEntry(
  line: string,
): Promise<LogEntry | null> {
  try {''',
        "output": '''const entry = JSON.parse(line);
    if (typeof entry.display !== 'string') return null;
    return entry as LogEntry;
  } catch {
    return null;
  }''',
        "metadata": {"language": "typescript", "pattern": "parse_history_entry", "complexity": "simple"}
    },
    {
        "input": '''export function parseReferences(
  input: string,
): Array<{ id: number; match: string; index: number }> {
  const referencePattern = /\\[\\(Pasted text|Image|\\.\\.\\.Truncated text) #(\\d+)(?: \\+\\d+ lines)?\\(\\.)*\\]/g;
  const matches = [...input.matchAll(referencePattern)];''',
        "output": '''return matches
    .map(match => ({
      id: parseInt(match[2] || '0'),
      match: match[0],
      index: match.index,
    }))
    .filter(match => match.id > 0);''',
        "metadata": {"language": "typescript", "pattern": "parse_references", "complexity": "medium"}
    },
    {
        "input": '''export function filterToolProgressMessages(
  progressMessagesForMessage: ProgressMessage[],
): ProgressMessage<ToolProgressData>[] {''',
        "output": '''return progressMessagesForMessage.filter(
  (msg): msg is ProgressMessage<ToolProgressData> =>
    msg.data?.type !== 'hook_progress',
);''',
        "metadata": {"language": "typescript", "pattern": "filter_progress", "complexity": "simple"}
    },
    {
        "input": '''export function toolMatchesName(
  tool: { name: string; aliases?: string[] },
  name: string,
): boolean {''',
        "output": '''return tool.name === name || tool.aliases?.includes(name) ?? false;''',
        "metadata": {"language": "typescript", "pattern": "tool_matches", "complexity": "simple"}
    },
    
    # Task generation
    {
        "input": '''export function generateTaskId(type: TaskType): string {
  const prefix = getTaskIdPrefix(type);
  const bytes = randomBytes(8);
  let id = prefix;
  for (const byte of bytes) {''',
        "output": '''id += TASK_ID_ALPHABET[byte % 36];''',
        "metadata": {"language": "typescript", "pattern": "generate_task_id", "complexity": "simple"}
    },
    
    # Vim motion patterns
    {
        "input": '''export function resolveMotion(
  cursor: Cursor,
  motion: string,
  count: number,
  ctx: VimContext,
): Cursor {''',
        "output": '''// Handle word motions
  if (motion === 'w') {
    return moveWordForward(cursor, count);
  } else if (motion === 'b') {
    return moveWordBackward(cursor, count);
  } else if (motion === 'e') {
    return moveWordEnd(cursor, count);
  }
  // Handle line motions
  if (motion === '$') {
    return new Cursor(cursor.line, ctx.lines[cursor.line].length);
  } else if (motion === '0') {
    return new Cursor(cursor.line, 0);
  }
  return cursor;''',
        "metadata": {"language": "typescript", "pattern": "vim_motion", "complexity": "high"}
    },
    
    # Chunk encoding
    {
        "input": '''function encodeChunk(data: Buffer): Buffer {
  const varint: number[] = [];
  let n = data.length;
  while (n > 0x7f) {''',
        "output": '''varint.push((n & 0x7f) | 0x80);
    n >>>= 7;''',
        "metadata": {"language": "typescript", "pattern": "encode_chunk", "complexity": "medium"}
    },
    
    # Agent session patterns
    {
        "input": '''export class AgentSession {
  private messages: Message[] = []
  private tools: Map<string, Tool> = new Map()
  
  async processMessage(input: string): Promise<Response> {''',
        "output": '''const context = await this.buildContext()
    const toolCalls = this.extractToolCalls(input)
    
    for (const toolCall of toolCalls) {
      const tool = this.tools.get(toolCall.name)
      if (tool) {
        const result = await tool.execute(toolCall.args)
        this.messages.push({ type: 'tool', name: toolCall.name, result })
      }
    }
    
    return this.generateResponse(context)''',
        "metadata": {"language": "typescript", "pattern": "agent_session_process", "complexity": "high"}
    },
    
    # Context manager patterns
    {
        "input": '''export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>''',
        "output": '''setTimeout(() => reject(new Error('Operation timed out')), timeoutMs)
    )
  ])
}''',
        "metadata": {"language": "typescript", "pattern": "with_timeout", "complexity": "simple"}
    },
    
    # Event emitter patterns
    {
        "input": '''export class EventEmitter<T extends Record<string, any>> {
  private listeners: Map<keyof T, Set<Function>> = new Map()
  
  on<K extends keyof T>(event: K, handler: T[K]): void {''',
        "output": '''if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)''',
        "metadata": {"language": "typescript", "pattern": "event_emitter_on", "complexity": "simple"}
    },
    {
        "input": '''export class EventEmitter<T extends Record<string, any>> {
  private listeners: Map<keyof T, Set<Function>> = new Map()
  
  emit<K extends keyof T>(event: K, data: Parameters<T[K]>[0]): void {''',
        "output": '''const handlers = this.listeners.get(event)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }''',
        "metadata": {"language": "typescript", "pattern": "event_emitter_emit", "complexity": "simple"}
    },
    
    # Streaming response patterns
    {
        "input": '''export async function* streamResponse(
  text: string,
  delayMs: number = 20,
): AsyncGenerator<string> {
  for (const char of text) {''',
        "output": '''yield char
    await sleep(delayMs)''',
        "metadata": {"language": "typescript", "pattern": "stream_response", "complexity": "simple"}
    },
]

# ============================================================================
# Python Code Completion Patterns
# ============================================================================

PY_PATTERNS = [
    # Async context manager
    {
        "input": '''class AsyncContextManager:
    async def __aenter__(self):
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):''',
        "output": '''await self.cleanup()
        return False''',
        "metadata": {"language": "python", "pattern": "async_context_manager", "complexity": "simple"}
    },
    
    # Dataclass with validator
    {
        "input": '''from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentConfig:
    name: str
    max_retries: int = 3
    timeout: float = 30.0
    tools: List[str] = field(default_factory=list)
    
    def __post_init__(self):''',
        "output": '''if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")''',
        "metadata": {"language": "python", "pattern": "dataclass_validator", "complexity": "medium"}
    },
    
    # Retry decorator
    {
        "input": '''import asyncio
import functools
from typing import TypeVar, Callable, Any

T = TypeVar('T')

def retry_async(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:''',
        "output": '''for attempt in range(1, max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts:
                    raise
                await asyncio.sleep(delay * attempt)''',
        "metadata": {"language": "python", "pattern": "retry_decorator", "complexity": "medium"}
    },
    
    # Thread pool executor
    {
        "input": '''from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any

def parallel_map(func: Callable, items: List[Any], max_workers: int = 4) -> List[Any]:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:''',
        "output": '''future_to_item = {executor.submit(func, item): item for item in items}
        for future in as_completed(future_to_item):
            results.append(future.result())
    return results''',
        "metadata": {"language": "python", "pattern": "parallel_map", "complexity": "medium"}
    },
    
    # JSON Lines reader
    {
        "input": '''import json
from typing import Iterator, Dict, Any

def read_jsonl(file_path: str) -> Iterator[Dict[str, Any]]:
    with open(file_path, 'r') as f:
        for line in f:''',
        "output": '''line = line.strip()
            if line:
                yield json.loads(line)''',
        "metadata": {"language": "python", "pattern": "read_jsonl", "complexity": "simple"}
    },
    {
        "input": '''import json
from typing import Iterator, Dict, Any

def write_jsonl(file_path: str, items: Iterator[Dict[str, Any]]) -> int:
    count = 0
    with open(file_path, 'w') as f:
        for item in items:''',
        "output": '''f.write(json.dumps(item) + '\\n')
            count += 1
    return count''',
        "metadata": {"language": "python", "pattern": "write_jsonl", "complexity": "simple"}
    },
    
    # Singleton pattern
    {
        "input": '''class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:''',
        "output": '''cls._instance = super().__new__(cls)
        return cls._instance''',
        "metadata": {"language": "python", "pattern": "singleton", "complexity": "simple"}
    },
    
    # Builder pattern
    {
        "input": '''class QueryBuilder:
    def __init__(self):
        self._filters = []
        self._limit = None
        self._offset = None
    
    def filter(self, **kwargs) -> 'QueryBuilder':''',
        "output": '''self._filters.append(kwargs)
        return self''',
        "metadata": {"language": "python", "pattern": "builder_filter", "complexity": "simple"}
    },
    {
        "input": '''class QueryBuilder:
    def __init__(self):
        self._filters = []
        self._limit = None
        self._offset = None
    
    def limit(self, n: int) -> 'QueryBuilder':
        self._limit = n
        return self
    
    def build(self) -> str:''',
        "output": '''query = "SELECT * FROM items"
        if self._filters:
            query += " WHERE " + " AND ".join(self._filters)
        if self._limit:
            query += f" LIMIT {self._limit}"
        if self._offset:
            query += f" OFFSET {self._offset}"
        return query''',
        "metadata": {"language": "python", "pattern": "builder_build", "complexity": "medium"}
    },
    
    # Cache decorator
    {
        "input": '''import functools
from typing import Callable, Any

def memoize(func: Callable) -> Callable:
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:''',
        "output": '''key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]''',
        "metadata": {"language": "python", "pattern": "memoize", "complexity": "simple"}
    },
    
    # Rate limiter
    {
        "input": '''import time
from collections import deque
from typing import Deque

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls: Deque[float] = deque()
    
    def acquire(self) -> bool:''',
        "output": '''now = time.time()
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False''',
        "metadata": {"language": "python", "pattern": "rate_limiter", "complexity": "medium"}
    },
    
    # Circular buffer
    {
        "input": '''from typing import List, Optional

class CircularBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: List[Optional[str]] = [None] * capacity
        self.head = 0
        self.size = 0
    
    def append(self, item: str) -> None:''',
        "output": '''self.buffer[self.head] = item
        self.head = (self.head + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)''',
        "metadata": {"language": "python", "pattern": "circular_buffer", "complexity": "medium"}
    },
    
    # Priority queue item
    {
        "input": '''import heapq
from typing import Any, Tuple

class PriorityQueue:
    def __init__(self):
        self._heap: List[Tuple[int, Any]] = []
    
    def push(self, priority: int, item: Any) -> None:''',
        "output": '''heapq.heappush(self._heap, (priority, item))''',
        "metadata": {"language": "python", "pattern": "priority_queue_push", "complexity": "simple"}
    },
    {
        "input": '''import heapq
from typing import Any, Tuple

class PriorityQueue:
    def __init__(self):
        self._heap: List[Tuple[int, Any]] = []
    
    def pop(self) -> Any:''',
        "output": '''if not self._heap:
            raise IndexError("pop from empty priority queue")
        _, item = heapq.heappop(self._heap)
        return item''',
        "metadata": {"language": "python", "pattern": "priority_queue_pop", "complexity": "simple"}
    },
    
    # Chain of responsibility
    {
        "input": '''from abc import ABC, abstractmethod
from typing import Optional, Any

class Handler(ABC):
    def __init__(self):
        self._next_handler: Optional[Handler] = None
    
    def set_next(self, handler: 'Handler') -> 'Handler':''',
        "output": '''self._next_handler = handler
        return handler''',
        "metadata": {"language": "python", "pattern": "chain_set_next", "complexity": "simple"}
    },
    {
        "input": '''from abc import ABC, abstractmethod
from typing import Optional, Any

class Handler(ABC):
    def __init__(self):
        self._next_handler: Optional[Handler] = None
    
    @abstractmethod
    def handle(self, request: Any) -> Optional[str]:
        pass
    
    def _try_next(self, request: Any) -> Optional[str]:''',
        "output": '''if self._next_handler:
            return self._next_handler.handle(request)
        return None''',
        "metadata": {"language": "python", "pattern": "chain_try_next", "complexity": "simple"}
    },
]

# ============================================================================
# Shell Script Patterns
# ============================================================================

SHELL_PATTERNS = [
    # Error handling
    {
        "input": '''#!/bin/bash
set -euo pipefail

main() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then''',
        "output": '''echo "Error: File not found: $file" >&2
        return 1
    fi''',
        "metadata": {"language": "shell", "pattern": "check_file_exists", "complexity": "simple"}
    },
    {
        "input": '''#!/bin/bash
set -euo pipefail

main() {
    local cmd="$1"
    shift
    
    if ! command -v "$cmd" &> /dev/null; then''',
        "output": '''echo "Error: Required command not found: $cmd" >&2
        exit 1
    fi
    
    "$cmd" "$@"''',
        "metadata": {"language": "shell", "pattern": "require_command", "complexity": "simple"}
    },
    
    # Loop patterns
    {
        "input": '''#!/bin/bash
set -euo pipefail

main() {
    local dir="${1:-.}"
    
    while IFS= read -r file; do''',
        "output": '''echo "Processing: $file"
        # Add your processing logic here
    done < <(find "$dir" -type f -name "*.txt")''',
        "metadata": {"language": "shell", "pattern": "process_files", "complexity": "medium"}
    },
    {
        "input": '''#!/bin/bash
set -euo pipefail

main() {
    local arr=("$@")
    
    for item in "${arr[@]}"; do''',
        "output": '''echo "Item: $item"
    done''',
        "metadata": {"language": "shell", "pattern": "iterate_array", "complexity": "simple"}
    },
    
    # Parallel execution
    {
        "input": '''#!/bin/bash
set -euo pipefail

run_parallel() {
    local max_jobs=4
    local pids=()
    
    for item in "$@"; do
        process_item "$item" &
        pids+=($!)
        
        if [[ ${#pids[@]} -ge $max_jobs ]]; then''',
        "output": '''wait "${pids[0]}"
            pids=("${pids[@]:1}")
        fi
    done
    
    wait''',
        "metadata": {"language": "shell", "pattern": "parallel_jobs", "complexity": "high"}
    },
    
    # Cleanup trap
    {
        "input": '''#!/bin/bash
set -euo pipefail

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT INT TERM

main() {''',
        "output": '''# Your main logic here
    echo "Working in: $TEMP_DIR"''',
        "metadata": {"language": "shell", "pattern": "cleanup_trap", "complexity": "simple"}
    },
    
    # JSON parsing
    {
        "input": '''#!/bin/bash
set -euo pipefail

parse_json() {
    local json="$1"
    local key="$2"
    
    echo "$json" | grep -o "\"$key\":\"[^\"]*"\"""',
        "output": '''| cut -d'"' -f4''',
        "metadata": {"language": "shell", "pattern": "parse_json_key", "complexity": "medium"}
    },
    
    # Progress indicator
    {
        "input": '''#!/bin/bash
set -euo pipefail

show_progress() {
    local current=$1
    local total=$2
    local width=50''',
        "output": '''local percent=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))
    printf "\\r[%s%s] %d%%" "$(printf '#%.0s' $(seq 1 $completed))" \\
        "$(printf '.%.0s' $(seq 1 $remaining))" "$percent"''',
        "metadata": {"language": "shell", "pattern": "progress_bar", "complexity": "medium"}
    },
]

# ============================================================================
# OpenClaw-Specific Patterns (Tools, Memory, Agents)
# ============================================================================

OPENCLAW_PATTERNS = [
    # Memory operations
    {
        "input": '''export async function searchMemory(
  query: string,
  options: { maxResults?: number } = {}
): Promise<MemoryResult[]> {
  const { maxResults = 10 } = options;
  const embedding = await embedText(query);''',
        "output": '''const results = await vectorStore.search(embedding, maxResults)
  return results.map(r => ({
    content: r.text,
    score: r.score,
    metadata: r.metadata
  }))''',
        "metadata": {"language": "typescript", "pattern": "memory_search", "complexity": "high", "domain": "openclaw"}
    },
    {
        "input": '''export async function createMemoryEntity(
  name: string,
  entityType: string,
  observations: string[]
): Promise<void> {''',
        "output": '''const entity: MemoryEntity = {
    name,
    entityType,
    observations,
    createdAt: Date.now()
  }
  await memoryStore.save(entity)''',
        "metadata": {"language": "typescript", "pattern": "memory_create_entity", "complexity": "medium", "domain": "openclaw"}
    },
    {
        "input": '''export async function addMemoryObservation(
  entityName: string,
  content: string
): Promise<void> {
  const entity = await memoryStore.get(entityName);''',
        "output": '''if (!entity) {
    throw new Error(`Entity not found: ${entityName}`);
  }
  entity.observations.push(content);
  await memoryStore.save(entity);''',
        "metadata": {"language": "typescript", "pattern": "memory_add_observation", "complexity": "medium", "domain": "openclaw"}
    },
    
    # Tool execution
    {
        "input": '''export async function executeTool(
  tool: Tool,
  args: Record<string, any>,
  context: ExecutionContext
): Promise<ToolResult> {
  const startTime = Date.now();
  try {''',
        "output": '''const result = await tool.fn(args, context);
    return {
      success: true,
      result,
      duration: Date.now() - startTime
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      duration: Date.now() - startTime
    };
  }''',
        "metadata": {"language": "typescript", "pattern": "tool_execute", "complexity": "medium", "domain": "openclaw"}
    },
    {
        "input": '''export function validateToolArgs(
  toolSchema: ToolSchema,
  args: unknown
): ValidationResult {''',
        "output": '''const errors: string[] = [];
  for (const [name, schema] of Object.entries(toolSchema.properties)) {
    if (schema.required && !(name in args)) {
      errors.push(`Missing required argument: ${name}`);
    }
  }
  return { valid: errors.length === 0, errors };''',
        "metadata": {"language": "typescript", "pattern": "tool_validate_args", "complexity": "medium", "domain": "openclaw"}
    },
    
    # Session management
    {
        "input": '''export class SessionManager {
  private sessions: Map<string, Session> = new Map();
  
  createSession(userId: string): Session {''',
        "output": '''const session: Session = {
    id: generateSessionId(),
    userId,
    createdAt: Date.now(),
    messages: [],
    toolsUsed: new Set()
  };
  this.sessions.set(session.id, session);
  return session;''',
        "metadata": {"language": "typescript", "pattern": "session_create", "complexity": "medium", "domain": "openclaw"}
    },
    {
        "input": '''export class SessionManager {
  private sessions: Map<string, Session> = new Map();
  
  getSession(sessionId: string): Session | undefined {''',
        "output": '''return this.sessions.get(sessionId);''',
        "metadata": {"language": "typescript", "pattern": "session_get", "complexity": "simple", "domain": "openclaw"}
    },
    {
        "input": '''export class SessionManager {
  private sessions: Map<string, Session> = new Map();
  
  async cleanupExpiredSessions(maxAgeMs: number): Promise<number> {''',
        "output": '''const now = Date.now();
  let cleaned = 0;
  for (const [id, session] of this.sessions) {
    if (now - session.createdAt > maxAgeMs) {
      await this.persistSession(session);
      this.sessions.delete(id);
      cleaned++;
    }
  }
  return cleaned;''',
        "metadata": {"language": "typescript", "pattern": "session_cleanup", "complexity": "medium", "domain": "openclaw"}
    },
    
    # Agent patterns
    {
        "input": '''export async function processAgentMessage(
  message: string,
  context: AgentContext
): Promise<AgentResponse> {
  const intent = await detectIntent(message);''',
        "output": '''if (intent.type === 'tool_call') {
    const results = await executeToolCalls(intent.tools, context);
    return { type: 'tool_result', results };
  } else if (intent.type === 'query') {
    const answer = await answerQuery(message, context);
    return { type: 'answer', content: answer };
  }
  return { type: 'fallback', content: 'Could not process request' };''',
        "metadata": {"language": "typescript", "pattern": "agent_process", "complexity": "high", "domain": "openclaw"}
    },
    {
        "input": '''export function createAgent(
  config: AgentConfig
): Agent {
  const agent: Agent = {
    id: generateAgentId(),
    config,
    state: 'idle',
    history: []''',
        "output": '''return agent;''',
        "metadata": {"language": "typescript", "pattern": "agent_create", "complexity": "simple", "domain": "openclaw"}
    },
    
    # Skill loading
    {
        "input": '''export async function loadSkill(
  skillPath: string
): Promise<Skill> {
  const module = await import(skillPath);''',
        "output": '''if (!module.default || !module.default.name) {
    throw new Error(`Invalid skill module: ${skillPath}`);
  }
  return {
    name: module.default.name,
    description: module.default.description,
    tools: module.default.tools || [],
    handlers: module.default.handlers || {}
  };''',
        "metadata": {"language": "typescript", "pattern": "skill_load", "complexity": "medium", "domain": "openclaw"}
    },
    {
        "input": '''export async function listSkills(): Promise<Skill[]> {
  const skillDirs = await glob('**/SKILL.md');''',
        "output": ''' const skills: Skill[] = [];
  for (const dir of skillDirs) {
    const skill = await loadSkill(dir.replace('/SKILL.md', ''));
    skills.push(skill);
  }
  return skills;''',
        "metadata": {"language": "typescript", "pattern": "skill_list", "complexity": "medium", "domain": "openclaw"}
    },
    
    # File operations
    {
        "input": '''export async function readWorkspaceFile(
  relativePath: string
): Promise<string | null> {
  const workspaceRoot = getWorkspaceRoot();
  const fullPath = path.join(workspaceRoot, relativePath);''',
        "output": '''try {
    return await readFile(fullPath, 'utf-8');
  } catch (e) {
    return null;
  }''',
        "metadata": {"language": "typescript", "pattern": "workspace_read", "complexity": "simple", "domain": "openclaw"}
    },
    {
        "input": '''export async function writeWorkspaceFile(
  relativePath: string,
  content: string
): Promise<void> {
  const workspaceRoot = getWorkspaceRoot();
  const fullPath = path.join(workspaceRoot, relativePath);''',
        "output": '''await mkdir(path.dirname(fullPath), { recursive: true });
  await writeFile(fullPath, content, 'utf-8');''',
        "metadata": {"language": "typescript", "pattern": "workspace_write", "complexity": "medium", "domain": "openclaw"}
    },
    
    # Conversation history
    {
        "input": '''export function formatConversationHistory(
  messages: Message[],
  options: { maxMessages?: number } = {}
): string {''',
        "output": '''const { maxMessages = 100 } = options;
  const recent = messages.slice(-maxMessages);
  return recent.map(m => `[${m.role}]: ${m.content}`).join('\\n');''',
        "metadata": {"language": "typescript", "pattern": "conversation_history", "complexity": "simple", "domain": "openclaw"}
    },
    {
        "input": '''export async function* getTimestampedHistory(): AsyncGenerator<TimestampedHistoryEntry> {
  const currentProject = getProjectRoot();
  const seen = new Set<string>();

  for await (const entry of makeLogEntryReader()) {
    if (!entry || typeof entry.project !== 'string') continue;
    if (entry.project !== currentProject) continue;
    if (seen.has(entry.display)) continue;''',
        "output": '''seen.add(entry.display);
    yield {
      display: entry.display,
      timestamp: entry.timestamp,
      resolve: () => logEntryToHistoryEntry(entry),
    };
    if (seen.size >= MAX_HISTORY_ITEMS) return;''',
        "metadata": {"language": "typescript", "pattern": "timestamped_history", "complexity": "high", "domain": "openclaw"}
    },
]

# ============================================================================
# GENERATE VARIATIONS
# ============================================================================

def generate_variations(base_patterns, count_target):
    """Generate variations of base patterns to reach count_target."""
    variations = list(base_patterns)
    
    # Generate variations by changing variable names, types, etc.
    while len(variations) < count_target:
        for pattern in base_patterns:
            if len(variations) >= count_target:
                break
            
            # Create a variation
            variation = create_variation(pattern)
            if variation:
                variations.append(variation)
    
    return variations[:count_target]

def create_variation(pattern):
    """Create a variation of a pattern with different names/types."""
    lang = pattern.get("metadata", {}).get("language", "typescript")
    
    # Type variations
    if lang == "typescript":
        type_options = ["string", "number", "boolean", "object", "any", "unknown"]
        generic_options = ["T", "K", "V", "R", "TResult", "TData", "TResult", "TItem"]
        
        new_pattern = {
            "input": pattern["input"].replace(
                random.choice(list(set(type_options + generic_options))),
                random.choice(generic_options)
            ),
            "output": pattern["output"],
            "metadata": {**pattern.get("metadata", {})}
        }
        return new_pattern
    
    return None

def create_type_variation(pattern):
    """Create a TypeScript type-based variation."""
    types = ["string", "number", "boolean", "object", "any", "unknown", "void", "null", "undefined"]
    generics = ["T", "K", "V", "R", "TResult", "TData", "TResult", "TItem", "TKey", " TValue"]
    
    new_input = pattern["input"]
    
    # Replace type names
    for t in types:
        if t in new_input and random.random() > 0.7:
            new_type = random.choice([x for x in types if x != t])
            new_input = new_input.replace(t, new_type, 1)
            break
    
    # Replace generics
    for g in generics:
        if g in new_input and random.random() > 0.5:
            new_gen = random.choice([x for x in generics if x != g])
            new_input = new_input.replace(g, new_gen, 1)
            break
    
    return {
        "input": new_input,
        "output": pattern["output"],
        "metadata": pattern.get("metadata", {})
    }

# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_all_examples():
    """Generate all 1000 examples."""
    all_patterns = []
    
    # Add base patterns
    all_patterns.extend(TS_PATTERNS)
    all_patterns.extend(PY_PATTERNS)
    all_patterns.extend(SHELL_PATTERNS)
    all_patterns.extend(OPENCLAW_PATTERNS)
    
    base_count = len(all_patterns)
    print(f"Base patterns: {base_count}")
    
    # Generate more patterns through variation
    # We'll create additional patterns by extending the base ones
    additional = []
    
    # TypeScript method completions
    ts_methods = [
        ("map", "return items.map(item => transform(item))"),
        ("filter", "return items.filter(item => predicate(item))"),
        ("reduce", "return items.reduce((acc, item) => accumulator(acc, item), initial)"),
        ("forEach", "items.forEach(item => { console.log(item) })"),
        ("find", "return items.find(item => matcher(item)) || null"),
    ]
    
    for _ in range(150):
        method, completion = random.choice(ts_methods)
        additional.append({
            "input": f"const result = items.{method}((item) => {{",
            "output": completion,
            "metadata": {"language": "typescript", "pattern": f"array_{method}", "complexity": "simple"}
        })
    
    # Python comprehensions
    py_comprehensions = [
        ("list", "[x for x in items]"),
        ("dict", "{k: v for k, v in items.items()}"),
        ("set", "{x for x in items}"),
        ("filter", "[x for x in items if predicate(x)]"),
    ]
    
    for _ in range(150):
        comp_type, completion = random.choice(py_comprehensions)
        additional.append({
            "input": f"result = {comp_type[:-1]}",
            "output": completion,
            "metadata": {"language": "python", "pattern": f"comprehension_{comp_type}", "complexity": "simple"}
        })
    
    # Error handling patterns
    error_handling_ts = [
        ("try { await doSomething() }", "} catch (e) { console.error(e) }"),
        ("if (!result)", "return null"),
        ("if (error)", "throw new Error(error.message)"),
    ]
    
    for _ in range(100):
        cond, completion = random.choice(error_handling_ts)
        additional.append({
            "input": cond,
            "output": completion,
            "metadata": {"language": "typescript", "pattern": "error_handling", "complexity": "simple"}
        })
    
    error_handling_py = [
        ("try:", "    pass"),
        ("except Exception as e:", "    print(e)"),
        ("finally:", "    cleanup()"),
    ]
    
    for _ in range(100):
        cond, completion = random.choice(error_handling_py)
        additional.append({
            "input": cond,
            "output": completion,
            "metadata": {"language": "python", "pattern": "error_handling", "complexity": "simple"}
        })
    
    # Import statements
    ts_imports = [
        ("import", "from './module'"),
        ("export", "class Foo {}"),
        ("export", "function bar() {}"),
        ("export", "const CONFIG = {}"),
    ]
    
    for _ in range(100):
        kw, completion = random.choice(ts_imports)
        additional.append({
            "input": kw,
            "output": completion,
            "metadata": {"language": "typescript", "pattern": "import_export", "complexity": "simple"}
        })
    
    # Function signatures
    func_sigs = [
        ("async function fetchData(url: string)", "): Promise<Data> {"),
        ("function processItems(items: T[])", "): T[] {"),
        ("const handleClick = (event: Event)", "): void => {"),
        ("export default class Agent implements IAgent", " {"),
        ("interface ToolConfig {", "name: string;"),
    ]
    
    for _ in range(100):
        sig, completion = random.choice(func_sigs)
        additional.append({
            "input": sig,
            "output": completion,
            "metadata": {"language": "typescript", "pattern": "function_signature", "complexity": "medium"}
        })
    
    all_patterns.extend(additional)
    
    # Ensure we have exactly 1000
    if len(all_patterns) > 1000:
        all_patterns = all_patterns[:1000]
    elif len(all_patterns) < 1000:
        # Pad with additional variations
        while len(all_patterns) < 1000:
            base = random.choice(all_patterns[:base_count])
            all_patterns.append(create_type_variation(base))
    
    return all_patterns

def main():
    print("Generating 1000 code completion examples...")
    
    examples = generate_all_examples()
    
    output_path = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/generated/code_completion_batch_01.jsonl"
    
    with open(output_path, 'w') as f:
        for i, example in enumerate(examples):
            record = {
                "prompt": example["input"],
                "completion": example["output"]
            }
            f.write(json.dumps(record) + "\n")
    
    print(f"Generated {len(examples)} examples to {output_path}")
    
    # Verify
    with open(output_path, 'r') as f:
        lines = f.readlines()
    print(f"Verified: {len(lines)} lines written")

if __name__ == "__main__":
    main()
