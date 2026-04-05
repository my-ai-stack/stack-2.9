# Tool Calling Training Data Analysis

**Generated:** 2026-04-06  
**Files Analyzed:** 
- `training-data/tool_examples.jsonl` (original)
- `training-data_v2/tool_examples.jsonl` (regenerated)

---

## Executive Summary

The original tool calling training data had **significant quality issues** that limited its usefulness for training a production AI coding assistant. The data was synthetically generated with systematic errors.

**Key Findings on Original Data:**
- ❌ 10.5% of tool calls use incorrect parameters (mismatched search queries, wrong files)
- ❌ Heavy prompt duplication (7.5x average)
- ❌ No multi-step tool chains (only 1 tool per example)
- ❌ All examples use identical tool definitions

**Action Taken:** Generated 500 new examples using the project's generator script.

**Recommendation:** The original data needs substantial improvements before use in training.

---

## 1. Statistics Overview

### Original Data (tool_examples.jsonl)

| Metric | Value |
|--------|-------|
| Total Examples | 1,000 |
| Unique Prompts | 133 |
| Average Duplication | 7.52x |
| Unique Tool Sequences | 5 |
| Examples with Issues | ~107 (10.7%) |

### New Data (tool_examples_v2.jsonl)

| Metric | Value |
|--------|-------|
| Total Examples | 500 |
| File Size | 1.9 MB |
| Tools per Example | 5 (static definition) |

### Tool Call Distribution (Original)

| Tool | Call Count |
|------|------------|
| Bash | 200 |
| FileRead | 200 |
| FileWrite | 200 |
| WebSearch | 200 |
| Grep | 200 |

All examples have exactly **one tool call** - no multi-step chains exist.

---

## 2. Prompt Diversity Analysis (Original Data)

### Prompt Categories

| Category | Count | Percentage |
|----------|-------|------------|
| Python | 207 | 20.7% |
| React | 149 | 14.9% |
| File Read | 134 | 13.4% |
| File Write | 119 | 11.9% |
| Other | 114 | 11.4% |
| Run Command | 80 | 8.0% |
| Docker/K8s | 67 | 6.7% |
| Search | 50 | 5.0% |
| Git | 40 | 4.0% |
| Testing | 31 | 3.1% |
| Package Management | 9 | 0.9% |

### Most Duplicated Prompts

| Prompt | Occurrences |
|--------|-------------|
| "Run the tests with pytest" | 40 |
| "Run npm install to install dependencies" | 40 |
| "Write a simple React component to src/components/Button.jsx" | 67 |

---

## 3. Tool Usage Breakdown

### Tool Definitions

All 1,000 original examples use **identical tool definitions** with 5 tools:
- `Bash` - Execute bash commands
- `FileRead` - Read file contents
- `FileWrite` - Create/overwrite files
- `WebSearch` - Search the web
- `Grep` - Search for patterns in files

### Tool Call Issues Found (Original Data)

#### Wrong Search Patterns (105 instances / 10.5%)

The `WebSearch` tool frequently uses queries that don't match the user's question:

| User Question | Actual Search Query |
|--------------|---------------------|
| "How do I use async/await in Python?" | "AWS Lambda cold start optimization" |
| "How do I use React hooks properly?" | "SQL join types explained" |
| "What's the difference between Docker and Kubernetes?" | "Git rebase vs merge" |
| "How do I use React hooks properly?" | "TypeScript generics tutorial" |
| "What's the difference between Docker and Kubernetes?" | "TypeScript generics tutorial" |

#### Wrong File Paths (2 instances)

The `FileWrite` tool sometimes writes to incorrect file types:

| User Request | Written Path |
|-------------|--------------|
| "Create a src/components/Header.jsx file" | Written to `config.json` |
| "Create a src/middleware.py file with settings" | Written to `config.yaml` |

#### Pattern/File Type Mismatches (Grep)

The `Grep` tool sometimes searches with mismatched patterns:

| Pattern | File Pattern | Issue |
|---------|-------------|-------|
| `class ` | `*.ts` | Python pattern in TypeScript files |
| `SELECT ` | `*.js` | SQL pattern in JavaScript files |
| `TODO` | `*.md` | Searching TODO in markdown files |

---

## 4. Data Quality Issues

### Critical Issues

1. **No Multi-Step Tool Chains**
   - All 1,000 examples use exactly one tool call
   - Real coding tasks typically require 2-5+ tool calls
   - Example: "Read file → Find pattern → Search docs → Write fix"

2. **Search Query Mismatches**
   - 10.5% of WebSearch calls have irrelevant queries
   - Indicates the generator script has logic errors

3. **Heavy Prompt Duplication**
   - 133 unique prompts duplicated to 1,000 examples
   - "Write a simple React component" appears 67 times
   - This creates overfitting to specific prompts

4. **Identical Tool Definitions**
   - All examples use the same 5 tools with identical descriptions
   - No variation in tool schemas or parameter structures

### Moderate Issues

5. **File Path Hallucination**
   - Tool calls reference files that don't exist in actual codebase
   - Example: asking for `tests/test_main.py` but reading `src/app.js`

6. **Response Fabrication**
   - Assistant responses sometimes claim to show content that wasn't actually read
   - Example: "Here's the README.md" when README.md wasn't the file requested

---

## 5. Recommendations for Improvement

### Immediate Actions (Completed)

1. ✅ **Regenerated Data**
   ```
   Generated 500 new examples in training-data_v2/tool_examples.jsonl
   ```

### Script Fixes Needed

The generator script (`scripts/generate_tool_data.py`) needs:

1. Fix `TOOL_CALL_PAIRS` mapping - queries don't match questions
2. Fix `FILE_PATTERNS` - wrong file types for requested content
3. Add multi-step chain generation
4. Add prompt variation templates
5. Add validation to check query/content relevance

### Future Improvements

1. **Add Multi-Step Examples**
   - Real tasks require reading files, searching, editing
   - Generate chains of 2-4 tool calls per example

2. **Increase Prompt Diversity**
   - Target 500+ unique prompts instead of duplicating
   - Use template variations and paraphrasing

3. **Vary Tool Definitions**
   - Different tools per example
   - Add tool variations (e.g., different Bash commands)

---

## 6. Conclusion

The original `tool_examples.jsonl` data is **NOT suitable for production training** without significant improvements:

- ~10% of examples have incorrect tool parameters
- Heavy duplication leads to overfitting
- No multi-step chains fail to represent real coding workflows
- Synthetic generation errors are systematic

**Action Completed:** Generated 500 new examples via the project's generator script.

**Remaining Work:** Fix the underlying generator script to eliminate the systematic errors before full-scale regeneration.

---

## Appendix: Quick Stats

### Original Data
```
Total examples:        1,000
Unique prompts:        133
Tool call issues:      107 (10.7%)
Multi-tool chains:     0 (0%)
Identical tool defs:   100%
Average duplication:   7.52x
```

### New Data (Generated)
```
Total examples:        500
File size:             1.9 MB
Location:              training-data_v2/tool_examples.jsonl
```