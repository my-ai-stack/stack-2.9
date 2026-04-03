// Code Indexer - Semantic code search for Stack 2.9
//
// Provides RAG capabilities by indexing code and enabling semantic search.

import { readdir, readFile, writeFile, stat } from 'fs/promises'
import { join, relative, extname } from 'path'
import crypto from 'crypto'

// Types
export interface CodeChunk {
  id: string
  filePath: string
  content: string
  startLine: number
  endLine: number
  language: string
  chunkType: 'function' | 'class' | 'file' | 'block'
}

export interface CodeIndex {
  version: string
  projectPath: string
  indexedAt: string
  chunks: (CodeChunk & { embedding: number[] })[]
}

export interface CodeSearchResult {
  chunk: Omit<CodeChunk, 'id'>
  score: number
  filePath: string
  startLine: number
  endLine: number
}

// Configuration
const CHUNK_SIZE = 2000
const TOP_K = 5

// Supported file extensions
const CODE_EXTENSIONS = new Set([
  '.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java',
  '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
  '.kt', '.scala', '.vue', '.svelte', '.json', '.yaml', '.yml',
  '.md', '.txt', '.sh', '.bash', '.zsh',
])

// Directories to skip
const SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', 'out', '__pycache__',
  '.next', '.nuxt', '.svelte-kit', 'coverage', '.cache',
  '.venv', 'venv', 'env', '.env', 'vendor',
])

// Language detection
function getLanguage(filePath: string): string {
  const ext = extname(filePath).toLowerCase()
  const langMap: Record<string, string> = {
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.py': 'python',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.vue': 'vue',
    '.svelte': 'svelte',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
  }
  return langMap[ext] ?? 'text'
}

// Simple hash-based embedding (for offline use)
// In production, use @xenova/transformers or OpenAI embeddings
function generateEmbedding(content: string): number[] {
  const hash = crypto.createHash('sha256').update(content).digest()
  const embedding: number[] = []
  for (let i = 0; i < 256; i++) {
    embedding.push((hash[i % hash.length] ?? 0) / 255)
  }
  return embedding
}

// Cosine similarity
function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0
  let normA = 0
  let normB = 0
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]
    normA += a[i] * a[i]
    normB += b[i] * b[i]
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB) || 1)
}

// Split code into chunks
function splitIntoChunks(content: string, filePath: string, language: string): CodeChunk[] {
  const lines = content.split('\n')
  const chunks: CodeChunk[] = []
  let chunkLines: string[] = []
  let startLine = 1

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    chunkLines.push(line)

    // Create chunk when size exceeds limit or at logical boundaries
    const shouldChunk = chunkLines.join('\n').length > CHUNK_SIZE ||
      (line.match(/^(function|class|const|let|var|def|import|export|public|private)/) && chunkLines.length > 5)

    if (shouldChunk && chunkLines.length > 3) {
      chunks.push({
        id: crypto.randomUUID(),
        filePath,
        content: chunkLines.join('\n'),
        startLine,
        endLine: i + 1,
        language,
        chunkType: 'block',
      })
      chunkLines = []
      startLine = i + 2
    }
  }

  // Add remaining as final chunk
  if (chunkLines.length > 0) {
    chunks.push({
      id: crypto.randomUUID(),
      filePath,
      content: chunkLines.join('\n'),
      startLine,
      endLine: lines.length,
      language,
      chunkType: 'file',
    })
  }

  return chunks
}

// Walk directory and collect files
async function* walkDirectory(dir: string): AsyncGenerator<string> {
  try {
    const entries = await readdir(dir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = join(dir, entry.name)

      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name) && !entry.name.startsWith('.')) {
          yield* walkDirectory(fullPath)
        }
      } else if (entry.isFile()) {
        const ext = extname(entry.name).toLowerCase()
        if (CODE_EXTENSIONS.has(ext)) {
          yield fullPath
        }
      }
    }
  } catch (error) {
    console.warn(`[index] Cannot read directory ${dir}:`, error)
  }
}

// ─── Code Indexer Class ───

export class CodeIndexer {
  private index: CodeIndex | null = null

  async indexProject(projectPath: string): Promise<void> {
    console.log(`[index] Indexing project: ${projectPath}`)

    const chunks: (CodeChunk & { embedding: number[] })[] = []

    for await (const filePath of walkDirectory(projectPath)) {
      try {
        const content = await readFile(filePath, 'utf-8')
        const relPath = relative(projectPath, filePath)
        const language = getLanguage(filePath)

        const fileChunks = splitIntoChunks(content, relPath, language)

        for (const chunk of fileChunks) {
          chunks.push({
            ...chunk,
            embedding: generateEmbedding(chunk.content),
          })
        }
      } catch (error) {
        console.warn(`[index] Cannot read file ${filePath}:`, error)
      }
    }

    this.index = {
      version: '1.0.0',
      projectPath,
      indexedAt: new Date().toISOString(),
      chunks,
    }

    console.log(`[index] Indexed ${chunks.length} chunks from project`)
  }

  async search(query: string, topK: number = TOP_K): Promise<CodeSearchResult[]> {
    if (!this.index) {
      console.warn('[index] No index loaded')
      return []
    }

    const queryEmbedding = generateEmbedding(query)

    // Calculate similarity for each chunk
    const results = this.index.chunks.map(chunk => ({
      chunk: {
        filePath: chunk.filePath,
        content: chunk.content,
        startLine: chunk.startLine,
        endLine: chunk.endLine,
        language: chunk.language,
        chunkType: chunk.chunkType,
      },
      filePath: chunk.filePath,
      startLine: chunk.startLine,
      endLine: chunk.endLine,
      score: cosineSimilarity(queryEmbedding, chunk.embedding),
    }))

    // Sort by score and return top K
    results.sort((a, b) => b.score - a.score)
    return results.slice(0, topK)
  }

  async saveIndex(path: string): Promise<void> {
    if (!this.index) {
      throw new Error('No index to save')
    }

    await writeFile(path, JSON.stringify(this.index, null, 2))
    console.log(`[index] Saved index to ${path}`)
  }

  async loadIndex(path: string): Promise<void> {
    const content = await readFile(path, 'utf-8')
    this.index = JSON.parse(content)
    console.log(`[index] Loaded index with ${this.index.chunks.length} chunks`)
  }

  getIndexStats(): { chunkCount: number; indexedAt: string } | null {
    if (!this.index) return null
    return {
      chunkCount: this.index.chunks.length,
      indexedAt: this.index.indexedAt,
    }
  }
}

// ─── Factory ───

export function createIndexer(): CodeIndexer {
  return new CodeIndexer()
}

export default {
  CodeIndexer,
  createIndexer,
}