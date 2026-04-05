# Stack 2.9 Evaluation Datasets

## Files

| File | Count | Description |
|------|-------|-------------|
| `humaneval_50.jsonl` | 50 | HumanEval subset with difficulty ratings |
| `mbpp_100.jsonl` | 100 | MBPP-style programming problems |
| `tool_scenarios_50.jsonl` | 50 | Multi-step tool calling scenarios |

## Format

### HumanEval
```json
{"task_id": "humaneval_1", "difficulty": "medium", "prompt": "def solution(x):\n", "test": "assert solution(5) == 5"}
```

### MBPP
```json
{"task_id": "mbpp_1", "difficulty": "easy", "prompt": "def task(arr):\n", "test": "assert task([1,2,3]) == 6"}
```

### Tool Scenarios
```json
{"task_id": "tool_scenario_1", "difficulty": "hard", "prompt": "Task: Read file and count errors", "tools_needed": ["FileRead", "Grep"], "expected_steps": 3}
```

## Usage

```python
from evaluate_model import load_benchmark

benchmarks = load_benchmark("evaluation/humaneval_50.jsonl")
# Run evaluation...
```
