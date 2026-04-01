#!/usr/bin/env node
/**
 * Training Data Extractor for OpenClaw
 * Extracts code patterns, conversations, tool uses from src/
 */

import { readFile, readdir, writeFile, mkdir } from 'fs/promises'
import { join, extname } from 'path'

const SRC_DIR = '/Users/walidsobhi/.openclaw/workspace/src'
const OUTPUT_DIR = '/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/src-derived'

// Tool descriptions for tool-use examples
const TOOL_PROMPTS = {
  Bash: `Executes a bash command and returns its output. Use for git operations, running scripts, file operations. Avoid: find, grep, cat, head, tail, sed, awk. Use Glob/Grep tools instead.`,
  Read: `Reads a file from the local filesystem. Returns cat -n format with line numbers. Use absolute paths. Max 2000 lines. Can read images visually.`,
  Write: `Writes a file to the local filesystem. Overwrites existing files. Must Read first for existing files. Prefer Edit for modifications.`,
  Edit: `Performs exact string replacements in files. Must Read first. Use unique old_string (2-4 lines). Use replace_all for multiple changes.`,
  Glob: `Fast file pattern matching. Supports glob patterns like "**/*.js". Returns file paths sorted by modification time.`,
  Grep: `Ripgrep-powered search tool. Full regex support. Use for content search. Glob for file name search.`,
  Agent: `Launch a new agent to handle complex, multi-step tasks autonomously. Specify subagent_type. Include description and prompt.`,
  Skill: `Execute a skill/slash command. Invoke when user asks for /command. Match skill name and call the tool.`,
  TaskCreate: `Create a structured task list for tracking progress. Use for complex multi-step tasks. Fields: subject, description, activeForm.`,
  WebSearch: `Search the web for current information. Returns formatted results with links. MUST include Sources section.`,
  WebFetch: `Fetch and process web content. Takes URL and prompt. Converts HTML to markdown. Read-only.`,
}

// Code patterns for completion
const CODE_PATTERNS = {
  toolDefinition: `export const TOOL_NAME = 'ToolName'
export function getDescription(): string {
  return \`Description here\`
}`,
  
  toolClass: `class MyTool {
  readonly name = 'MyTool'
  readonly description = 'Does something useful'
  
  async call(input: MyToolInput): Promise<ToolResult<Output>> {
    // implementation
  }
}`,
  
  zodSchema: `const MyToolInput = z.object({
  param1: z.string().describe('Description'),
  param2: z.number().optional(),
})

type MyToolInput = z.infer<typeof MyToolInput>`,
  
  reactComponent: `import React from 'react'

interface Props {
  title: string
  onAction?: () => void
}

export function MyComponent({ title, onAction }: Props) {
  return (
    <div>
      <h1>{title}</h1>
      <button onClick={onAction}>Action</button>
    </div>
  )
}`,
  
  hook: `import { useState, useEffect } from 'react'

export function useMyHook(initialValue: string) {
  const [value, setValue] = useState(initialValue)
  
  useEffect(() => {
    // side effect
    return () => {
      // cleanup
    }
  }, [])
  
  return { value, setValue }
}`,
  
  asyncFunction: `async function fetchData(url: string): Promise<Data> {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(\`HTTP \${response.status}\`)
    }
    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw error
  }
}`,
  
  typescriptInterface: `interface User {
  id: string
  name: string
  email: string
  createdAt: Date
  metadata?: Record<string, unknown>
}

type UserWithRole = User & {
  role: 'admin' | 'user' | 'guest'
}`,
  
  errorHandling: `try {
  await riskyOperation()
} catch (error) {
  if (error instanceof SpecificError) {
    handleSpecificError(error)
  } else {
    logError(error)
    throw error
  }
} finally {
  cleanup()
}`,
  
  mapFilterReduce: `const result = items
  .filter(item => item.active)
  .map(item => ({
    id: item.id,
    label: item.name.toUpperCase(),
  }))
  .sort((a, b) => a.label.localeCompare(b.label))`,
  
  promiseAll: `const results = await Promise.all([
    fetchData('/api/users'),
    fetchData('/api/posts'),
    fetchData('/api/comments'),
])`,
  
  eventHandler: `element.addEventListener('click', (event) => {
  event.preventDefault()
  const target = event.target as HTMLElement
  handleClick(target.dataset.id)
})`,
  
  contextHook: `const MyContext = createContext<MyContextType | null>(null)

export function useMyContext() {
  const context = useContext(MyContext)
  if (!context) {
    throw new Error('useMyContext must be used within provider')
  }
  return context
}`,
}

// Generate tool-use examples
function generateToolUseExamples() {
  const examples = []
  
  // Read file example
  examples.push({
    type: 'tool_use',
    tool: 'Read',
    input: { file_path: '/path/to/file.ts' },
    description: 'Reading TypeScript source file',
  })
  
  // Write file example
  examples.push({
    type: 'tool_use',
    tool: 'Write',
    input: { 
      file_path: '/path/to/newFile.ts', 
      content: 'export function hello() { return "world" }' 
    },
    description: 'Creating new TypeScript file',
  })
  
  // Edit file example
  examples.push({
    type: 'tool_use',
    tool: 'Edit',
    input: {
      file_path: '/path/to/file.ts',
      old_string: 'const API_URL = "http://localhost:3000"',
      new_string: 'const API_URL = process.env.API_URL || "http://localhost:3000"',
    },
    description: 'Adding environment variable fallback',
  })
  
  // Bash example
  examples.push({
    type: 'tool_use',
    tool: 'Bash',
    input: { command: 'npm run build', description: 'Building the project' },
    description: 'Running build command',
  })
  
  // Glob example
  examples.push({
    type: 'tool_use',
    tool: 'Glob',
    input: { pattern: '**/*.tsx' },
    description: 'Finding all TSX files',
  })
  
  // Grep example
  examples.push({
    type: 'tool_use',
    tool: 'Grep',
    input: { 
      pattern: 'useState', 
      path: '/src', 
      type: 'tsx' 
    },
    description: 'Searching for useState in TSX files',
  })
  
  // Agent spawn example
  examples.push({
    type: 'tool_use',
    tool: 'Agent',
    input: {
      description: 'Investigate auth bug',
      subagent_type: 'worker',
      prompt: 'Investigate the auth module. Find null pointer risks around session handling. Report file paths, line numbers, types.',
    },
    description: 'Spawning research agent',
  })
  
  // Skill invocation example
  examples.push({
    type: 'tool_use',
    tool: 'Skill',
    input: { skill: 'commit', args: '-m "Fix bug"' },
    description: 'Invoking commit skill',
  })
  
  // Task creation example
  examples.push({
    type: 'tool_use',
    tool: 'TaskCreate',
    input: {
      subject: 'Fix authentication null pointer',
      description: 'Add null check for user field in session validation',
      activeForm: 'Fixing authentication bug',
    },
    description: 'Creating tracking task',
  })
  
  // Web search example
  examples.push({
    type: 'tool_use',
    tool: 'WebSearch',
    input: { query: 'TypeScript 5.4 new features 2024' },
    description: 'Searching for TypeScript features',
  })
  
  // Web fetch example
  examples.push({
    type: 'tool_use',
    tool: 'WebFetch',
    input: { 
      url: 'https://docs.example.com/api', 
      prompt: 'Extract the authentication section' 
    },
    description: 'Fetching API documentation',
  })
  
  return examples
}

// Generate conversation patterns
function generateConversationPatterns() {
  return [
    {
      type: 'conversation',
      role: 'user',
      content: 'Can you fix the null pointer in auth/validate.ts?',
    },
    {
      type: 'conversation',
      role: 'assistant',
      content: 'I\'ll investigate the auth module to understand the issue.',
      tool_calls: [
        { name: 'Agent', input: { description: 'Investigate auth bug', subagent_type: 'worker', prompt: 'Find null pointer in auth/validate.ts around session handling. Report specific line numbers.' } }
      ]
    },
    {
      type: 'conversation',
      role: 'user',
      content: '<task-notification>Agent completed - Found null at line 42</task-notification>',
    },
    {
      type: 'conversation',
      role: 'assistant',
      content: 'Found it. Let me fix the null pointer.',
      tool_calls: [
        { name: 'Read', input: { file_path: '/src/auth/validate.ts' } },
        { name: 'Edit', input: { file_path: '/src/auth/validate.ts', old_string: 'const userId = session.user.id', new_string: 'if (!session.user) return null\nconst userId = session.user.id' } }
      ]
    },
    // Pattern: Research -> Implementation -> Verification
    {
      type: 'conversation',
      role: 'user',
      content: 'Write tests for the auth module',
    },
    {
      type: 'conversation',
      role: 'assistant',
      content: 'Let me first explore the existing test structure.',
      tool_calls: [
        { name: 'Glob', input: { pattern: '**/*auth*.test.ts' } },
        { name: 'Glob', input: { pattern: '**/tests/**/*.ts' } }
      ]
    },
    {
      type: 'conversation',
      role: 'assistant',
      content: 'Now I understand the test structure. Let me write the auth tests.',
      tool_calls: [
        { name: 'Write', input: { file_path: '/tests/auth/validate.test.ts', content: '...' } }
      ]
    },
    {
      type: 'conversation',
      role: 'assistant',
      content: 'Running the tests to verify.',
      tool_calls: [
        { name: 'Bash', input: { command: 'npm test -- auth/validate' } }
      ]
    },
  ]
}

// Generate code completion pairs
function generateCodeCompletionPairs() {
  const pairs = []
  
  // Tool definition completion
  pairs.push({
    type: 'code_completion',
    context: `import { z } from 'zod'

export const TOOL_NAME = 'MyTool'`,
    completion: `export const DESCRIPTION = 'Does something useful'

export async function getPrompt(): Promise<string> {
  return \`Use this tool to...\`
}`,
    language: 'typescript',
  })
  
  // React component completion
  pairs.push({
    type: 'code_completion',
    context: `import React from 'react'

interface Props {
  title: string
}`,
    completion: `export function MyComponent({ title }: Props) {
  return (
    <div>
      <h1>{title}</h1>
    </div>
  )
}`,
    language: 'tsx',
  })
  
  // Hook completion
  pairs.push({
    type: 'code_completion',
    context: `import { useState, useEffect } from 'react'

export function useUserData(userId: string) {`,
    completion: `  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchUser(userId).then(setUser).finally(() => setLoading(false))
  }, [userId])
  
  return { user, loading }
}`,
    language: 'typescript',
  })
  
  // Tool call completion
  pairs.push({
    type: 'code_completion',
    context: `// User wants to read a TypeScript file
`,
    completion: `{ name: 'Read', input: { file_path: '/src/index.ts' } }`,
    language: 'json',
  })
  
  // Error handling completion
  pairs.push({
    type: 'code_completion',
    context: `async function fetchData(url: string) {
  try {
    const response = await fetch(url)
`,
    completion: `    if (!response.ok) {
      throw new Error(\`HTTP \${response.status}: \${response.statusText}\`)
    }
    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw error
  }
}`,
    language: 'typescript',
  })
  
  // Type definition completion
  pairs.push({
    type: 'code_completion',
    context: `interface ToolResult<T> {
  data: T
`,
    completion: `  newMessages?: Message[]
  contextModifier?: (context: ToolUseContext) => ToolUseContext
}`,
    language: 'typescript',
  })
  
  return pairs
}

// Main extraction function
async function extractTrainingData() {
  console.log('Starting training data extraction...')
  
  // Ensure output directory exists
  await mkdir(OUTPUT_DIR, { recursive: true })
  
  const allData = []
  
  // 1. Add tool descriptions
  for (const [tool, desc] of Object.entries(TOOL_PROMPTS)) {
    allData.push({
      category: 'tool_description',
      tool,
      description: desc,
    })
  }
  
  // 2. Add code patterns
  for (const [name, code] of Object.entries(CODE_PATTERNS)) {
    allData.push({
      category: 'code_pattern',
      pattern_name: name,
      code,
    })
  }
  
  // 3. Add tool-use examples
  allData.push(...generateToolUseExamples())
  
  // 4. Add conversation patterns
  allData.push(...generateConversationPatterns())
  
  // 5. Add code completion pairs
  allData.push(...generateCodeCompletionPairs())
  
  // Write JSONL output
  const jsonlPath = join(OUTPUT_DIR, 'training_data.jsonl')
  const jsonContent = allData.map(item => JSON.stringify(item)).join('\n')
  await writeFile(jsonlPath, jsonContent)
  
  console.log(`Wrote ${allData.length} training examples to ${jsonlPath}`)
  
  // Also write a summary
  const summary = {
    total_examples: allData.length,
    categories: {
      tool_description: allData.filter(d => d.category === 'tool_description').length,
      code_pattern: allData.filter(d => d.category === 'code_pattern').length,
      tool_use: allData.filter(d => d.type === 'tool_use').length,
      conversation: allData.filter(d => d.type === 'conversation').length,
      code_completion: allData.filter(d => d.type === 'code_completion').length,
    }
  }
  
  await writeFile(join(OUTPUT_DIR, 'summary.json'), JSON.stringify(summary, null, 2))
  
  console.log('Done!')
  return summary
}

extractTrainingData().catch(console.error)