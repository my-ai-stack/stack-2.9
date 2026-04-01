#!/usr/bin/env node
/**
 * Massive Training Data Extractor for OpenClaw
 * Extracts code patterns, tool definitions, and conversations from src/
 * Generates a massive JSONL dataset for training.
 * 
 * Usage: node massive-extract.js
 */

const { readdir, readFile, mkdir, writeFile } = require('fs/promises')
const { join, relative, extname } = require('path')
const fs = require('fs')

// ==================== CONFIGURATION ====================

const WORKSPACE = '/Users/walidsobhi/.openclaw/workspace'
const SRC_DIR = join(WORKSPACE, 'src')
const OUTPUT_DIR = join(WORKSPACE, 'stack-2.9', 'training-data', 'src-derived')
const OUTPUT_FILE = join(OUTPUT_DIR, 'massive_training_data.jsonl')

// Target subdirectories (relative to src/)
const TARGET_SUBDIRS = [
  'assistant',
  'buddy',
  'coordinator',
  'tools',
  'skills',
]

// File patterns to include
const INCLUDE_EXT = ['.ts', '.tsx']

// Exclude patterns
const EXCLUDE_DIRS = ['node_modules', 'dist', 'build', '.git']
const EXCLUDE_FILES = ['.d.ts']

// Minimum string length to consider as a prompt/template
const MIN_PROMPT_LENGTH = 200

// ==================== UTILITIES ====================

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`)
}

function truncate(str, maxLen) {
  if (!str) return ''
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen - 3) + '...'
}

function escapeJsonString(str) {
  if (!str) return ''
  return JSON.stringify(str)
}

// ==================== FILE DISCOVERY ====================

async function findTypeScriptFiles(dir, relativeBase = dir) {
  const results = []
  
  try {
    const entries = await readdir(dir, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = join(dir, entry.name)
      
      if (entry.isDirectory()) {
        if (EXCLUDE_DIRS.includes(entry.name) || entry.name.startsWith('.')) {
          continue
        }
        const subResults = await findTypeScriptFiles(fullPath, relativeBase)
        results.push(...subResults)
      } else if (entry.isFile()) {
        const ext = extname(entry.name)
        if (!INCLUDE_EXT.includes(ext)) continue
        
        // Skip excluded file patterns
        if (EXCLUDE_FILES.some(pattern => entry.name.endsWith(pattern))) {
          continue
        }
        
        results.push(fullPath)
      }
    }
  } catch (error) {
    console.error(`Error scanning ${dir}:`, error.message)
  }
  
  return results
}

// ==================== PATTERN EXTRACTION ====================

// Extract functions (regular, arrow, async)
function extractFunctions(code) {
  const functions = []
  
  // Match function declarations
  const funcDeclRegex = /function\s+([a-zA-Z_$][\w$]*)\s*\(/g
  let match
  while ((match = funcDeclRegex.exec(code)) !== null) {
    const name = match[1]
    // Find the function body
    const startIdx = match.index
    let braceCount = 0
    let bodyStart = -1
    let bodyEnd = -1
    
    for (let i = startIdx; i < code.length; i++) {
      if (code[i] === '{') {
        if (braceCount === 0) bodyStart = i + 1
        braceCount++
      } else if (code[i] === '}') {
        braceCount--
        if (braceCount === 0) {
          bodyEnd = i
          break
        }
      }
    }
    
    if (bodyStart > 0 && bodyEnd > bodyStart) {
      const body = code.slice(bodyStart, bodyEnd).trim()
      functions.push({
        type: 'function',
        name,
        body,
        full: code.slice(startIdx, bodyEnd + 1),
        line: code.substring(0, startIdx).split('\n').length,
      })
    }
  }
  
  // Match arrow functions with explicit name: const name = (...) => { ... }
  const arrowFuncRegex = /(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>/g
  while ((match = arrowFuncRegex.exec(code)) !== null) {
    const name = match[1]
    functions.push({
      type: 'arrow',
      name,
      body: '...',
      full: 'const ' + name + ' = (...) => { ... }',
      line: code.substring(0, match.index).split('\n').length,
    })
  }
  
  return functions.slice(0, 50) // Limit per file
}

// Extract interfaces
function extractInterfaces(code) {
  const interfaces = []
  const interfaceRegex = /interface\s+([a-zA-Z_$][\w$]*)\s*{/g
  let match
  while ((match = interfaceRegex.exec(code)) !== null) {
    const name = match[1]
    const startIdx = match.index
    let braceCount = 0
    let bodyStart = -1
    let bodyEnd = -1
    
    for (let i = startIdx; i < code.length; i++) {
      if (code[i] === '{') {
        if (braceCount === 0) bodyStart = i + 1
        braceCount++
      } else if (code[i] === '}') {
        braceCount--
        if (braceCount === 0) {
          bodyEnd = i
          break
        }
      }
    }
    
    if (bodyStart > 0 && bodyEnd > bodyStart) {
      const body = code.slice(bodyStart, bodyEnd).trim()
      interfaces.push({
        type: 'interface',
        name,
        body,
        full: code.slice(startIdx, bodyEnd + 1),
        line: code.substring(0, startIdx).split('\n').length,
      })
    }
  }
  
  return interfaces.slice(0, 20)
}

// Extract classes
function extractClasses(code) {
  const classes = []
  const classRegex = /class\s+([a-zA-Z_$][\w$]*)\s*(?:extends\s+[\w$.]+)?\s*{/g
  let match
  while ((match = classRegex.exec(code)) !== null) {
    const name = match[1]
    const startIdx = match.index
    let braceCount = 0
    let bodyStart = -1
    let bodyEnd = -1
    
    for (let i = startIdx; i < code.length; i++) {
      if (code[i] === '{') {
        if (braceCount === 0) bodyStart = i + 1
        braceCount++
      } else if (code[i] === '}') {
        braceCount--
        if (braceCount === 0) {
          bodyEnd = i
          break
        }
      }
    }
    
    if (bodyStart > 0 && bodyEnd > bodyStart) {
      const body = code.slice(bodyStart, bodyEnd).trim()
      classes.push({
        type: 'class',
        name,
        body,
        full: code.slice(startIdx, bodyEnd + 1),
        line: code.substring(0, startIdx).split('\n').length,
      })
    }
  }
  
  return classes.slice(0, 20)
}

// Extract React components
function extractComponents(code) {
  const components = []
  const lines = code.split('\n')
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const capitalizedMatch = line.match(/(?:const|function)\s+([A-Z][a-zA-Z0-9_$]*)/)
    if (!capitalizedMatch) continue
    const name = capitalizedMatch[1]
    
    // Look ahead to see if there's a return with JSX within reasonable distance
    let hasJSX = false
    for (let j = i; j < Math.min(i + 50, lines.length); j++) {
      if (lines[j].includes('return') && lines[j].match(/return\s*</)) {
        hasJSX = true
        break
      }
    }
    if (hasJSX) {
      components.push({
        type: 'component',
        name,
        full: `function ${name}(...) { return <...> }`,
        line: i + 1,
      })
    }
  }
  
  return components.slice(0, 30)
}

// Extract custom hooks
function extractHooks(functions) {
  return functions.filter(f => f.name && f.name.startsWith('use') && f.name.length > 3).slice(0, 30)
}

// Extract tool-like objects
function extractToolObjects(code) {
  const tools = []
  // Look for export const TOOL_NAME = { name: ..., description: ... }
  const nameRegex = /export\s+(?:const|let|var)\s+([A-Z_$][\w$]*)\s*=/g
  let match
  while ((match = nameRegex.exec(code)) !== null) {
    const name = match[1]
    // Check if it looks like a tool (has name, description pattern)
    const contextStart = Math.max(0, match.index - 50)
    const contextEnd = Math.min(code.length, match.index + 200)
    const context = code.slice(contextStart, contextEnd)
    
    if (context.includes('name') || context.includes('description') || name.endsWith('Tool')) {
      tools.push({
        type: 'tool',
        name,
        description: `Tool: ${name}`,
        full: context,
      })
    }
  }
  
  return tools.slice(0, 10)
}

// Extract imports and exports
function extractImportsExports(code) {
  const imports = []
  const exports = []
  const lines = code.split('\n')
  
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('import ')) {
      imports.push(trimmed)
    } else if (trimmed.startsWith('export ')) {
      exports.push(trimmed)
    }
  }
  
  return { imports, exports }
}

// ==================== EXAMPLE GENERATION ====================

function* generateCodeCompletionExamples(pattern, filePath, relativePath) {
  if (!pattern.body || pattern.body.length < 10) return
  
  const lines = pattern.full.split('\n')
  if (lines.length < 3) return
  
  const truncationPoints = [0.25, 0.5, 0.7, 0.9]
  
  for (const point of truncationPoints) {
    const splitIndex = Math.max(1, Math.floor(lines.length * point))
    const prefixLines = lines.slice(0, splitIndex)
    const suffixLines = lines.slice(splitIndex)
    
    if (suffixLines.length < 1) continue
    
    const prefix = prefixLines.join('\n')
    const suffix = suffixLines.join('\n')
    
    yield {
      category: 'code_completion',
      language: 'typescript',
      pattern_type: pattern.type,
      name: pattern.name,
      file: relativePath,
      truncation_point: point,
      context: truncate(prefix, 1500),
      completion: truncate(suffix, 1500),
    }
  }
}

function* generateInterfaceExamples(pattern, filePath, relativePath) {
  if (!pattern.body) return
  
  const lines = pattern.full.split('\n')
  if (lines.length < 3) return
  
  const mid = Math.floor(lines.length / 2)
  const prefix = lines.slice(0, mid).join('\n')
  const suffix = lines.slice(mid).join('\n')
  
  yield {
    category: 'code_completion',
    language: 'typescript',
    pattern_type: 'interface',
    name: pattern.name,
    file: relativePath,
    context: prefix + '\n  // complete',
    completion: suffix,
  }
}

function* generateClassExamples(pattern, filePath, relativePath) {
  if (!pattern.body) return
  
  const lines = pattern.full.split('\n')
  if (lines.length < 3) return
  
  yield {
    category: 'code_completion',
    language: 'typescript',
    pattern_type: 'class_body',
    name: pattern.name,
    file: relativePath,
    context: lines[0] + '\n  ',
    completion: lines.slice(1).join('\n'),
  }
}

function* generateComponentExamples(pattern, filePath, relativePath) {
  yield {
    category: 'code_completion',
    language: 'tsx',
    pattern_type: 'component_skeleton',
    name: pattern.name,
    file: relativePath,
    context: `function ${pattern.name}(props) {`,
    completion: `  return <div>...</div>\n}`,
  }
}

function* generateHookExamples(pattern, filePath, relativePath) {
  yield {
    category: 'code_completion',
    language: 'typescript',
    pattern_type: 'hook',
    name: pattern.name,
    file: relativePath,
    context: `function ${pattern.name}(initialValue) {`,
    completion: `const [value, setValue] = useState(initialValue)\n  // ...\n  return { value, setValue }\n}`,
  }
}

function* generateToolExamples(pattern, filePath, relativePath) {
  yield {
    category: 'tool_definition',
    tool_type: 'object',
    tool_name: pattern.name,
    file: relativePath,
    context: `const ${pattern.name} = {`,
    completion: `  name: '${pattern.name}',\n  description: '${pattern.description}',\n  async call(input, context) { ... }\n}`,
  }
}

// ==================== CONVERSATION PATTERNS ====================

function generateConversationExamples() {
  const patterns = [
    {
      user: "Can you investigate the authentication bug?",
      assistant: "I'll investigate the authentication module to find the root cause.",
      tool_calls: [{ name: 'Agent', args: { description: 'Investigate auth bug', subagent_type: 'worker', prompt: 'Investigate the authentication module. Find potential issues with session handling.' } }],
    },
    {
      user: "Update the API endpoint to use environment variables",
      assistant: "Let me read the configuration file first.",
      tool_calls: [{ name: 'Read', args: { file_path: '/src/config/api.ts' } }],
    },
    {
      user: "Find all TypeScript files that use useState",
      assistant: "I'll search for files using useState.",
      tool_calls: [
        { name: 'Glob', args: { pattern: '**/*.tsx' } },
        { name: 'Grep', args: { pattern: 'useState', type: 'tsx' } }
      ],
    },
    {
      user: "Commit these changes with a proper message",
      assistant: "I'll stage the changes and create a commit.",
      tool_calls: [{ name: 'Skill', args: { skill: 'commit', args: '-m "feat: add authentication module"' } }],
    },
    {
      user: "Make sure the tests pass after the changes",
      assistant: "I'll run the test suite to verify everything works.",
      tool_calls: [{ name: 'Bash', args: { command: 'npm test', description: 'Run test suite' } }],
    },
    {
      user: "What's the latest TypeScript feature?",
      assistant: "Let me search for the latest TypeScript features.",
      tool_calls: [{ name: 'WebSearch', args: { query: 'TypeScript 5.4 latest features 2024' } }],
    },
  ]
  
  for (const pattern of patterns) {
    yield {
      category: 'conversation',
      pattern_name: 'user_assistant_tool',
      user: pattern.user,
      assistant: pattern.assistant,
      tool_calls: pattern.tool_calls,
    }
  }
}

// ==================== SYSTEM PROMPT EXAMPLES ====================

function generateSystemPromptExamples() {
  const sections = [
    { section: 'doing_tasks', content: 'The user will primarily request you to perform software engineering tasks. These may include solving bugs, adding new functionality, refactoring code, explaining code, and more.' },
    { section: 'tools_guidance', content: 'To read files use Read instead of cat, head, tail, or sed. To edit files use Edit instead of sed or awk.' },
    { section: 'security', content: 'Be careful not to introduce security vulnerabilities such as command injection, XSS, SQL injection, and other OWASP top 10 vulnerabilities.' },
    { section: 'output_efficiency', content: 'IMPORTANT: Go straight to the point. Try the simplest approach first without going in circles. Do not overdo it. Be extra concise.' },
  ]
  
  for (const section of sections) {
    yield {
      category: 'system_prompt',
      section_type: section.section,
      instruction: section.content,
    }
  }
}

// ==================== MAIN ====================

async function main() {
  log('Starting massive training data extraction...')
  
  // Ensure output directory exists
  await mkdir(OUTPUT_DIR, { recursive: true })
  
  // Collect all files
  const allFiles = []
  for (const subdir of TARGET_SUBDIRS) {
    const dirPath = join(SRC_DIR, subdir)
    const files = await findTypeScriptFiles(dirPath, SRC_DIR)
    allFiles.push(...files)
  }
  
  log(`Found ${allFiles.length} TypeScript files to process`)
  
  // Open output stream
  const stream = fs.createWriteStream(OUTPUT_FILE, { encoding: 'utf-8' })
  
  let totalExamples = 0
  
  // Generate conversation examples
  for (const example of generateConversationExamples()) {
    stream.write(JSON.stringify(example) + '\n')
    totalExamples++
  }
  
  // Generate system prompt examples
  for (const example of generateSystemPromptExamples()) {
    stream.write(JSON.stringify(example) + '\n')
    totalExamples++
  }
  
  // Process each file
  let processed = 0
  for (const filePath of allFiles) {
    try {
      const code = await readFile(filePath, 'utf-8')
      const relativePath = relative(SRC_DIR, filePath)
      
      // Extract patterns
      const functions = extractFunctions(code)
      const interfaces = extractInterfaces(code)
      const classes = extractClasses(code)
      const components = extractComponents(code)
      const hooks = extractHooks(functions)
      const tools = extractToolObjects(code)
      const { imports, exports } = extractImportsExports(code)
      
      // Generate examples
      for (const func of functions) {
        for (const example of generateCodeCompletionExamples(func, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      for (const iface of interfaces) {
        for (const example of generateInterfaceExamples(iface, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      for (const cls of classes) {
        for (const example of generateClassExamples(cls, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      for (const comp of components) {
        for (const example of generateComponentExamples(comp, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      for (const hook of hooks) {
        for (const example of generateHookExamples(hook, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      for (const tool of tools) {
        for (const example of generateToolExamples(tool, filePath, relativePath)) {
          stream.write(JSON.stringify(example) + '\n')
          totalExamples++
        }
      }
      
      // Add file metadata
      stream.write(JSON.stringify({
        category: 'file_metadata',
        file: relativePath,
        functions: functions.length,
        interfaces: interfaces.length,
        classes: classes.length,
        components: components.length,
        hooks: hooks.length,
        tools: tools.length,
        imports: imports.length,
        exports: exports.length,
      }) + '\n')
      totalExamples++
      
      processed++
      if (processed % 100 === 0) {
        log(`Processed ${processed} files, ${totalExamples} examples generated...`)
      }
      
    } catch (error) {
      console.error(`Error processing ${filePath}:`, error.message)
    }
  }
  
  stream.end()
  
  log(`Completed! Generated ${totalExamples} training examples`)
  log(`Output written to: ${OUTPUT_FILE}`)
  
  // Get file size
  const stats = fs.statSync(OUTPUT_FILE)
  const sizeMB = (stats.size / (1024 * 1024)).toFixed(2)
  log(`Output file size: ${sizeMB} MB`)
}

main().catch(console.error)
