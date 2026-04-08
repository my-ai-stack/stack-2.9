# Stack 2.9 Training Data

This directory contains synthetic training data for fine-tuning code generation models.

## Directory Structure

```
training-data/
├── README.md                           # This file
├── tool_examples.jsonl                 # Tool-calling examples (Qwen2.5-Coder format)
├── tool_examples.json                  # Same as above in JSON format
├── code_completion/                    # Pure code completion examples
│   ├── code_completion.jsonl
│   └── code_completion.json
└── training-data-expanded/            # Additional generated data
    └── tool_examples.jsonl             # 5000 expanded tool-calling examples
```

## Data Formats

### Tool-Calling Examples

**Format:** Qwen2.5-Coder style with `tool_calls`

Each example contains:
- `messages`: Array of conversation messages (system, user, assistant, tool)
- `tools`: Array of tool definitions

**Example structure:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful AI assistant..."},
    {"role": "user", "content": "Read the file at src/main.py..."},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1234",
          "type": "function",
          "function": {
            "name": "FileRead",
            "arguments": "{\"path\": \"src/main.py\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "content": "Successfully read file: src/main.py\n...",
      "tool_call_id": "call_1234",
      "name": "FileRead"
    },
    {"role": "assistant", "content": "Here's the contents..."}
  ],
  "tools": [...]
}
```

**Available Tools:**
- `Bash` - Execute bash commands
- `FileRead` - Read file contents
- `FileWrite` - Write/create files
- `WebSearch` - Search the web
- `Grep` - Search patterns in files

### Code Completion Examples

**Format:** Chat-based with context and completion

Each example contains:
- `messages`: Array of conversation messages
- `language`: Programming language (python, javascript, go, rust, typescript)
- `difficulty`: easy, medium, hard
- `variant`: basic, explain, debug, optimize
- `context`: The code context to complete
- `completion`: The expected completion

**Example structure:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful AI assistant..."},
    {"role": "user", "content": "Complete the following code:\n```python\ndef greet(name):\n```"},
    {"role": "assistant", "content": "Here's the completed code:\n```python\ndef greet(name):\n    return f\"Hello, {name}!\"\n```"}
  ],
  "language": "python",
  "difficulty": "easy",
  "variant": "basic",
  "description": "Simple function that returns a greeting",
  "context": "def greet(name):",
  "completion": "    return f\"Hello, {name}!\""
}
```

## Generation Scripts

### Tool Data Generator

```bash
python3 scripts/generate_tool_data.py \
    --num-examples 5000 \
    --output-dir training-data-expanded \
    --output-format jsonl
```

### Code Completion Generator

```bash
python3 scripts/generate_code_completion_data.py \
    --num-examples 1000 \
    --output-dir training-data/code-completion \
    --languages python javascript go rust typescript \
    --difficulties easy medium hard \
    --variants basic explain debug optimize
```

## Difficulty Levels

| Level | Description |
|-------|-------------|
| **easy** | Simple functions, basic operations, single concepts |
| **medium** | Intermediate patterns, async operations, error handling |
| **hard** | Complex algorithms, data structures, design patterns |

## Variants

| Variant | Description |
|---------|-------------|
| **basic** | Standard code completion |
| **explain** | Code completion with explanation |
| **debug** | Bug fixing and completion |
| **optimize** | Performance optimization and completion |

## Supported Languages

- Python
- JavaScript
- Go
- Rust
- TypeScript

## Usage

### Training with MLflow

```bash
mlflow run . -P num_examples=5000
```

### Loading Data for Training

```python
import json

# Load JSONL
with open("training-data/tool_examples.jsonl", "r") as f:
    for line in f:
        example = json.loads(line)
        # Process example
        pass

# Load JSON
with open("training-data/tool_examples.json", "r") as f:
    data = json.load(f)
```

## Augmentation

The tool-calling generator applies augmentation to create diversity:
- Varying file paths
- Varying command options
- Varying search queries
- Varying code snippets

## Quality Guidelines

- All generated code is syntactically correct
- Examples include realistic context
- Tools have proper arguments and responses
- Code completions are deterministic and correct
