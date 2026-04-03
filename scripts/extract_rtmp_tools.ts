// Extract tool schemas from RTMP for training data
//
// This script extracts tool definitions from the RTMP codebase
// and adds them to stack-2.9's training data catalog.

import { readdir, readFile, writeFile } from 'fs/promises'
import { join, basename } from 'path'

const RTMP_TOOLS_DIR = '/Users/walidsobhi/.openclaw/workspace/RTMP/tools'
const STACK_CATALOG = '/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/tools/catalog.json'

interface ToolSchema {
  tool: string
  description: string
  hasPrompt: boolean
  hasImplementation: boolean
  inputSchema: Record<string, unknown>
}

async function extractToolSchemas(): Promise<ToolSchema[]> {
  const tools: ToolSchema[] = []
  const toolDirs = await readdir(RTMP_TOOLS_DIR)

  for (const toolDir of toolDirs) {
    const toolPath = join(RTMP_TOOLS_DIR, toolDir)
    const stat = await readdir(toolPath).then(() => true).catch(() => false)

    if (!stat) continue

    // Try to extract tool name and description from tool files
    let description = ''
    let hasPrompt = false
    let hasImplementation = false

    try {
      // Check for prompt.ts
      const promptPath = join(toolPath, 'prompt.ts')
      const promptContent = await readFile(promptPath, 'utf-8')
      hasPrompt = true

      // Extract first meaningful comment as description
      const comments = promptContent.match(/\/\*\*[\s\S]*?\*\//g)
      if (comments && comments.length > 0) {
        const comment = comments[0]
        description = comment
          .replace(/\/\*\*|\*\//g, '')
          .replace(/^\s*\*\s?/gm, '')
          .trim()
          .slice(0, 200)
      }
    } catch {
      // No prompt.ts
    }

    try {
      // Check for implementation files
      const toolFiles = await readdir(toolPath)
      hasImplementation = toolFiles.some(f =>
        f.endsWith('.ts') || f.endsWith('.tsx')
      )
    } catch {
      // Ignore
    }

    // Format tool name (remove Tool suffix for cleaner names)
    const toolName = toolDir.replace(/Tool$/, '')

    tools.push({
      tool: toolDir,
      description: description || `${toolName} tool`,
      hasPrompt,
      hasImplementation,
      inputSchema: {}
    })
  }

  return tools
}

async function main() {
  console.log('Extracting tool schemas from RTMP...')

  const tools = await extractToolSchemas()
  console.log(`Found ${tools.length} tools`)

  // Read existing catalog
  let existingTools: ToolSchema[] = []
  try {
    const existingContent = await readFile(STACK_CATALOG, 'utf-8')
    existingTools = JSON.parse(existingContent)
  } catch {
    console.log('No existing catalog found')
  }

  // Merge with existing (avoid duplicates)
  const existingNames = new Set(existingTools.map(t => t.tool))
  const newTools = tools.filter(t => !existingNames.has(t.tool))

  console.log(`Adding ${newTools.length} new tools`)

  // Combine
  const allTools = [...existingTools, ...newTools]

  // Write updated catalog
  await writeFile(STACK_CATALOG, JSON.stringify(allTools, null, 2))
  console.log(`Updated catalog with ${allTools.length} tools`)

  // Also print summary
  console.log('\nNew tools added:')
  for (const tool of newTools) {
    console.log(`  - ${tool.tool}`)
  }
}

main().catch(console.error)