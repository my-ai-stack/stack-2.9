#!/usr/bin/env node
/**
 * Massive Training Data Generator
 * Generates millions of training examples from OpenClaw/Claude Code source patterns
 */

import { readFileSync, writeFileSync, appendFileSync, mkdirSync, readdirSync, statSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = __dirname;

// Helper to generate variations
function generateVariations(base, count = 10) {
  const variations = [base];
  const templates = [
    (b) => `// Refactored version\n${b}`,
    (b) => `// Optimized variant\n${b}`,
    (b) => `// With error handling\n${b}`,
    (b) => `// Async version\n${b.replace(/sync/gi, 'Async').replace(/await /g, '')}`,
    (b) => `// With logging\n${b.replace(/\n}/g, '\n  console.log("debug")\n}')}`,
    (b) => `// Type-safe version\n${b.replace(/interface /g, 'type ').replace(/: string/g, ': String').replace(/: number/g, ': Number').replace(/: boolean/g, ': Boolean')}`,
    (b) => b.includes('export ') ? b : `// Extended version\n${b}`,
    (b) => b.includes('async ') ? b : b.replace(/function /g, 'async function '),
    (b) => b.includes('Promise') ? b : b.replace(/: void /g, ': Promise<void> '),
    (b) => b.includes('try') ? b : `try {\n${b}\n} catch (e) {\n  console.error(e)\n}`,
  ];
  
  for (let i = 0; i < count && i < templates.length; i++) {
    try {
      const variant = templates[i](base);
      if (variant !== base && variant.length > base.length) {
        variations.push(variant);
      }
    } catch (e) {
      // Skip invalid transformations
    }
  }
  return variations;
}

// Generate code completion pairs
function generateCompletionPairs(codePairs) {
  const completions = [];
  
  for (const pair of codePairs) {
    const code = pair.code || '';
    const comment = pair.comment || '';
    const type = pair.type || '';
    const name = pair.name || '';
    
    // Skip empty or very short code
    if (code.length < 20) continue;
    
    // Split code at various points to create completion targets
    const lines = code.split('\n');
    for (let splitAt = 1; splitAt < lines.length; splitAt++) {
      const prefix = lines.slice(0, splitAt).join('\n');
      const suffix = lines.slice(splitAt).join('\n');
      
      if (prefix.length > 20 && suffix.length > 10) {
        // Add basic completion
        completions.push({
          type: 'code_completion',
          subtype: 'function_body',
          input: prefix,
          output: suffix,
          metadata: {
            original_name: name,
            original_type: type,
            split_line: splitAt,
            total_lines: lines.length,
            has_comment: comment.length > 0,
          }
        });
        
        // Add with comment context
        if (comment.length > 0) {
          completions.push({
            type: 'code_completion',
            subtype: 'documented_function',
            input: `// ${comment}\n${prefix}`,
            output: suffix,
            metadata: {
              original_name: name,
              comment_length: comment.length,
            }
          });
        }
        
        // Early return variants (stop at key points)
        if (splitAt < lines.length / 2 && completions.length < 500000) {
          completions.push({
            type: 'code_completion',
            subtype: 'partial_implementation',
            input: prefix + '\n  // ... more implementation',
            output: suffix,
            metadata: { partial: true }
          });
        }
      }
    }
    
    // Generate from comment -> code pairs
    if (comment.length > 20) {
      completions.push({
        type: 'code_completion',
        subtype: 'comment_to_code',
        input: `// ${comment}`,
        output: code,
        metadata: {
          original_name: name,
          original_type: type,
        }
      });
    }
  }
  
  return completions;
}

// Generate tool-use examples
function generateToolUseExamples(codePairs) {
  const toolExamples = [];
  
  const toolPatterns = [
    { name: 'Bash', patterns: ['exec', 'spawn', 'child_process', 'shell', 'command'] },
    { name: 'FileRead', patterns: ['readFile', 'read', 'open', 'readSync'] },
    { name: 'FileWrite', patterns: ['writeFile', 'write', 'create', 'writeSync'] },
    { name: 'FileEdit', patterns: ['edit', 'patch', 'replace', 'modify'] },
    { name: 'Glob', patterns: ['glob', 'match', 'find', 'pattern'] },
    { name: 'Grep', patterns: ['grep', 'search', 'find', 'match'] },
    { name: 'WebFetch', patterns: ['fetch', 'http', 'request', 'url'] },
    { name: 'Task', patterns: ['task', 'worker', 'job', 'queue'] },
    { name: 'Agent', patterns: ['agent', 'subagent', 'spawn', 'create'] },
  ];
  
  for (const pair of codePairs) {
    const code = pair.code || '';
    const comment = pair.comment || '';
    
    // Find matching tools
    for (const tool of toolPatterns) {
      const matches = tool.patterns.filter(p => 
        code.toLowerCase().includes(p) || comment.toLowerCase().includes(p)
      );
      
      if (matches.length > 0) {
        // Generate tool call example
        toolExamples.push({
          type: 'tool_use',
          tool_name: tool.name,
          input: code.slice(0, 200),
          output: generateMockToolResult(tool.name, code),
          metadata: {
            matched_patterns: matches,
            code_length: code.length,
            has_comment: comment.length > 0,
          }
        });
      }
    }
    
    // Generate permission/validation examples
    if (code.includes('permission') || code.includes('validate') || code.includes('check')) {
      toolExamples.push({
        type: 'tool_use',
        tool_name: 'PermissionCheck',
        input: code.slice(0, 200),
        output: JSON.stringify({ allowed: true, reason: 'Permission granted' }),
        metadata: { category: 'security' }
      });
    }
  }
  
  return toolExamples;
}

function generateMockToolResult(toolName, code) {
  const results = {
    Bash: `{ "stdout": "command executed", "exitCode": 0 }`,
    FileRead: `{ "content": "${code.slice(0, 100)}...", "lines": ${code.split('\n').length} }`,
    FileWrite: `{ "path": "/path/to/file", "bytesWritten": ${code.length} }`,
    FileEdit: `{ "success": true, "changes": 1 }`,
    Glob: `{ "files": ["file1.ts", "file2.ts"], "count": 2 }`,
    Grep: `{ "matches": 0, "files": [] }`,
    WebFetch: `{ "status": 200, "body": "..." }`,
    Task: `{ "taskId": "task_123", "status": "pending" }`,
    Agent: `{ "agentId": "agent_456", "status": "running" }`,
  };
  return results[toolName] || '{ "success": true }';
}

// Generate conversation patterns
function generateConversationPatterns(codePairs) {
  const conversations = [];
  
  const intents = [
    'write_code', 'review_code', 'explain_code', 'debug_code', 'refactor_code',
    'test_code', 'deploy_code', 'search_code', 'read_file', 'edit_file'
  ];
  
  const responses = [
    'I\'ll help you with that', 'Let me look at the code', 'I found the issue',
    'Here\'s a better approach', 'I can refactor this', 'Let me run the tests',
    'I\'ll create the file', 'I\'ve made the changes', 'The code looks good',
    'I recommend using', 'Let me search for', 'I found several'
  ];
  
  for (let i = 0; i < Math.min(codePairs.length, 50000); i++) {
    const pair = codePairs[i];
    const code = pair.code || '';
    const comment = pair.comment || '';
    
    if (code.length < 30) continue;
    
    const intent = intents[i % intents.length];
    const response = responses[i % responses.length];
    
    conversations.push({
      type: 'conversation',
      subtype: 'code_task',
      user_message: generateUserMessage(intent, code.slice(0, 100)),
      assistant_message: `${response}. Here's the implementation:\n\n\`\`\`typescript\n${code.slice(0, 300)}\n\`\`\`\n\n${comment ? `Note: ${comment.slice(0, 100)}` : ''}`,
      metadata: {
        intent,
        code_length: code.length,
        has_explanation: comment.length > 0,
      }
    });
    
    // Multi-turn conversations
    if (i % 10 === 0) {
      conversations.push({
        type: 'conversation',
        subtype: 'multi_turn',
        turns: [
          {
            role: 'user',
            content: generateUserMessage(intent, code.slice(0, 100))
          },
          {
            role: 'assistant',
            content: `${response}. Here's the implementation:\n\n\`\`\`typescript\n${code.slice(0, 200)}\n\`\`\``
          },
          {
            role: 'user',
            content: 'Can you explain how it works?'
          },
          {
            role: 'assistant',
            content: comment || 'This code implements a specific pattern for handling the requested functionality.'
          }
        ],
        metadata: { turns: 4, topic: intent }
      });
    }
    
    // Error handling conversations
    conversations.push({
      type: 'conversation',
      subtype: 'error_resolution',
      user_message: `I'm getting an error in this code:\n\`\`\`\n${code.slice(0, 150)}\n\`\`\``,
      assistant_message: `I can see the issue. ${comment ? comment : 'The code needs better error handling.'} Here's the fix:\n\n\`\`\`typescript\n${generateErrorFixed(code)}\n\`\`\``,
      metadata: { has_fix: true }
    });
  }
  
  return conversations;
}

function generateUserMessage(intent, code) {
  const messages = {
    write_code: `Can you write code that ${code.slice(0, 50)}?`,
    review_code: `Can you review this code?\n\`\`\`\n${code}\n\`\`\``,
    explain_code: `Explain what this code does:\n\`\`\`\n${code}\n\`\`\``,
    debug_code: `Debug this code that's not working:\n\`\`\`\n${code}\n\`\`\``,
    refactor_code: `Refactor this code:\n\`\`\`\n${code}\n\`\`\``,
    test_code: `Write tests for:\n\`\`\`\n${code}\n\`\`\``,
    deploy_code: `Help me deploy this code to production`,
    search_code: `Search for patterns like: ${code.slice(0, 50)}`,
    read_file: `Read the file at ${code.slice(0, 30)}`,
    edit_file: `Edit the file with changes to: ${code.slice(0, 40)}`,
  };
  return messages[intent] || `Help with: ${code.slice(0, 50)}`;
}

function generateErrorFixed(code) {
  if (code.includes('try')) return code;
  return `try {\n  ${code.replace(/\n/g, '\n  ')}\n} catch (error) {\n  console.error('Error:', error);\n  throw error;\n}`;
}

// Generate synthetic augmentations
function generateAugmentedExamples(baseExamples, multiplier = 5) {
  const augmented = [];
  
  for (const example of baseExamples) {
    // Add original
    augmented.push(example);
    
    // Generate variations
    if (example.code) {
      const variations = generateVariations(example.code, multiplier);
      for (const variant of variations) {
        if (variant !== example.code) {
          augmented.push({
            ...example,
            code: variant,
            augmented: true,
            variation_id: augmented.length,
          });
        }
      }
    }
  }
  
  return augmented;
}

// Main execution
async function main() {
  console.log('🚀 Starting massive training data generation...');
  
  // Load source data
  const codePairsPath = join(OUTPUT_DIR, '..', 'code-pairs', 'extended_pairs_full.json');
  let codePairs = [];
  
  try {
    const data = readFileSync(codePairsPath, 'utf8');
    codePairs = JSON.parse(data);
    console.log(`📚 Loaded ${codePairs.length} code pairs`);
  } catch (e) {
    console.log('No extended_pairs_full.json found, using patterns data');
    const patternsPath = join(OUTPUT_DIR, '..', 'code-pairs', 'pairs.json');
    try {
      const data = readFileSync(patternsPath, 'utf8');
      codePairs = JSON.parse(data);
      console.log(`📚 Loaded ${codePairs.length} code pairs from pairs.json`);
    } catch (e2) {
      console.log('No pairs data found, generating synthetic patterns');
      codePairs = generateSyntheticPatterns();
    }
  }
  
  // Generate training examples
  console.log('\n📝 Generating completion pairs...');
  const completionPairs = generateCompletionPairs(codePairs);
  console.log(`   Generated ${completionPairs.length} completion pairs`);
  
  console.log('\n🔧 Generating tool-use examples...');
  const toolExamples = generateToolUseExamples(codePairs);
  console.log(`   Generated ${toolExamples.length} tool-use examples`);
  
  console.log('\n💬 Generating conversation patterns...');
  const conversations = generateConversationPatterns(codePairs);
  console.log(`   Generated ${conversations.length} conversation patterns`);
  
  // Combine all training data
  console.log('\n✨ Combining all training data...');
  const allTrainingData = [
    ...completionPairs,
    ...toolExamples,
    ...conversations,
  ];
  
  // Write to JSONL
  const outputPath = join(OUTPUT_DIR, 'training_data.jsonl');
  writeFileSync(outputPath, '');
  
  let written = 0;
  const batchSize = 10000;
  
  for (let i = 0; i < allTrainingData.length; i += batchSize) {
    const batch = allTrainingData.slice(i, i + batchSize);
    const lines = batch.map(item => JSON.stringify(item)).join('\n') + '\n';
    appendFileSync(outputPath, lines);
    written += batch.length;
    process.stdout.write(`\r   Written: ${written.toLocaleString()} / ${allTrainingData.length.toLocaleString()}`);
  }
  
  console.log(`\n\n✅ Wrote ${written.toLocaleString()} training examples to ${outputPath}`);
  
  // Generate summary
  const summary = {
    generated_at: new Date().toISOString(),
    total_examples: written,
    breakdown: {
      completion_pairs: completionPairs.length,
      tool_use_examples: toolExamples.length,
      conversation_patterns: conversations.length,
    },
    source_files: codePairs.length,
    output_format: 'jsonl',
  };
  
  writeFileSync(join(OUTPUT_DIR, 'summary.json'), JSON.stringify(summary, null, 2));
  console.log('\n📊 Summary saved to summary.json');
  
  // Return stats for reporting
  return summary;
}

function generateSyntheticPatterns() {
  // Generate synthetic patterns when no source data is available
  const patterns = [];
  
  const templates = [
    {
      code: `export async function fetchData(url: string): Promise<Data> {\n  const response = await fetch(url);\n  if (!response.ok) {\n    throw new Error(\`HTTP error! status: \${response.status}\`);\n  }\n  return response.json();\n}`,
      comment: 'Fetch data from URL with error handling',
      type: 'function',
      name: 'fetchData'
    },
    {
      code: `export function debounce<T extends (...args: any[]) => any>(\n  func: T,\n  wait: number\n): (...args: Parameters<T>) => void {\n  let timeout: NodeJS.Timeout | null = null;\n  return (...args: Parameters<T>) => {\n    if (timeout) clearTimeout(timeout);\n    timeout = setTimeout(() => func(...args), wait);\n  };\n}`,
      comment: 'Debounce function for rate limiting',
      type: 'function',
      name: 'debounce'
    },
    {
      code: `export class LRUCache<K, V> {\n  private cache = new Map<K, V>();\n  \n  constructor(private readonly maxSize: number) {}\n  \n  get(key: K): V | undefined {\n    if (!this.cache.has(key)) return undefined;\n    const value = this.cache.get(key)!;\n    this.cache.delete(key);\n    this.cache.set(key, value);\n    return value;\n  }\n  \n  set(key: K, value: V): void {\n    if (this.cache.has(key)) this.cache.delete(key);\n    else if (this.cache.size >= this.maxSize) {\n      const firstKey = this.cache.keys().next().value;\n      this.cache.delete(firstKey);\n    }\n    this.cache.set(key, value);\n  }\n}`,
      comment: 'LRU Cache implementation',
      type: 'class',
      name: 'LRUCache'
    },
  ];
  
  for (let i = 0; i < 100; i++) {
    const template = templates[i % templates.length];
    patterns.push({
      ...template,
      code: template.code.replace(/(\\d+)/g, (match) => {
        const num = parseInt(match) + i;
        return num.toString();
      }),
      name: `${template.name}_${i}`,
    });
  }
  
  return patterns;
}

main().then(summary => {
  console.log('\n🎉 Training data generation complete!');
  console.log(JSON.stringify(summary, null, 2));
  process.exit(0);
}).catch(err => {
  console.error('❌ Error:', err);
  process.exit(1);
});
