# Stack 2.9 Training Data Format

This document describes the format and structure of training data for Stack 2.9.

## Overview

Training data is stored in JSONL format (JSON Lines), where each line is a valid JSON object representing a single training example.

## File Structure

```
training-data/
├── tool_examples.jsonl          # Original examples (1000)
├── augmented_tool_examples.jsonl # Augmented examples (2-5x)
└── scaled/                      # Processed datasets
    ├── train.jsonl
    └── val.jsonl
```

## Example Format

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant that can use tools to help users solve problems."
    },
    {
      "role": "user",
      "content": "Can you show me the tests/test_main.py file?"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_$1180",
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
      "content": "Successfully read file: README.md\n```markdown\n# My Project\n\nA sample project for Stack 2.9.\n```",
      "tool_call_id": "call_$1180",
      "name": "FileRead"
    },
    {
      "role": "assistant",
      "content": "Here's the README.md:\n\n```markdown\n# My Project\n\nA sample project for Stack 2.9.\n```"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "Bash",
        "description": "Execute bash commands in the terminal.",
        "parameters": {
          "type": "object",
          "properties": {
            "command": {"type": "string", "description": "The bash command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds"}
          },
          "required": ["command"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "FileRead",
        "description": "Read the contents of a file.",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string", "description": "Path to the file to read"},
            "offset": {"type": "integer", "description": "Line number to start from"},
            "limit": {"type": "integer", "description": "Max lines to read"}
          },
          "required": ["path"]
        }
      }
    }
  ]
}
```

## Field Definitions

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | array | Yes | Array of message objects |
| `tools` | array | Yes | Available tools/functions |
| `source` | string | No | Data source identifier |

### Message Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | One of: system, user, assistant, tool |
| `content` | string | Yes* | Message content (null if tool_calls present) |
| `tool_calls` | array | No* | Tool call requests |
| `tool_call_id` | string | No* | ID linking to tool response |
| `name` | string | No* | Tool name (for tool messages) |

*Content is required unless `tool_calls` is present. `tool_call_id` and `name` required for role="tool".

### Tool Call Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique call identifier |
| `type` | string | Yes | Always "function" |
| `function` | object | Yes | Function name and arguments |
| `function.name` | string | Yes | Tool/function name |
| `function.arguments` | object/string | Yes | JSON arguments |

## Data Sources

- **random_synthetic**: Auto-generated with random parameters
- **synthetic_template**: Template-based synthetic examples
- **augmented_***: Augmented from other sources
- **original**: Human-curated examples

## Augmentation

The augmentation script applies these transformations:

1. **Paraphrasing**: Reword user prompts (70% chance)
2. **Difficulty scaling**: Add complexity modifiers
3. **Parameter variation**: Change file paths, commands
4. **Filler words**: Add "please", "thanks" (30% chance)
5. **Edge cases**: Empty input, multi-step, error handling

Run augmentation:
```bash
python scripts/augment_training_data.py \
  --input training-data/tool_examples.jsonl \
  --output training-data/augmented.jsonl \
  --multiplier 3
```

## Validation

Run validation to check data quality:
```bash
python scripts/validate_training_data.py --input training-data/tool_examples.jsonl
```

Checks include:
- Required fields present
- Valid JSON syntax
- Message role ordering
- Tool call structure
- No empty entries

## Converting to Training Format

For training, convert to standard format:
```python
# Example conversion
python scripts/combine_datasets.py \
  --input training-data/augmented.jsonl \
  --output data/final/train.jsonl \
  --format chatml
```