# Data Scaling Strategy - Stack 2.9

## Target: 50K+ Training Examples

### Current State
- Synthetic examples: 213
- Code-comment pairs: 4,045
- Advanced patterns: 306
- **Total estimated:** ~5,000-6,000 examples

### Target: 50,000+ examples

---

## Scaling Plan

### 1. Mine OpenClaw Session Logs (10K examples)

**Where to look:**
- `~/.openclaw/sessions/` - OpenClaw session logs
- `~/.claude/sessions/` - Claude Code sessions (if exists)
- `~/.anthropic/` - Anthropic Claude logs
- Any custom session history in project directories

**Format:** Likely JSON, JSONL, or Markdown
**What to extract:**
- Full conversations with tool use
- User prompts + assistant responses + tool calls + tool results
- Multi-turn dialogues
- Error recovery patterns
- Different tool combinations

**Expected yield:** 5,000-15,000 examples depending on usage history.

---

### 2. Synthetic Data with Template-Based Generation (20K examples)

**Approach:** Create hundreds of templates for each tool pattern and generate variations.

**For each of 37 tools:**
- Create 10-20 scenario templates (e.g., for FileReadTool: "Read file X", "Show me Y", "What's in Z?")
- Generate 200-500 variations by:
  * Changing file names, function names, variables
  * Varying parameter values
  * Changing phrasing (synonyms, active/passive, question/command)
  * Adding noise (typos, extra spaces, filler words)
  * Combining multiple tool calls in sequence

**Total:** 37 tools × 500 variations = 18,500 examples

**Tools with highest priority:**
- FileReadTool, FileWriteTool, GlobTool, GrepTool (common)
- BashTool, TaskCreateTool, Agent-related tools (complex workflows)
- MCPTool (extension patterns)

---

### 3. Public Dataset Integration (20K examples)

**Datasets to download (Hugging Face - free):**

#### a) OpenAssistant (oasst1)
- Conversations from OpenAssistant project
- Filter: coding-related threads
- Transform: Convert to tool-use format (synthesize tool calls from intent)
- Estimated: 5,000 examples

#### b) CodeAct
- Already has executable code actions
- Direct mapping to our tools
- Estimated: 10,000 examples

#### c) CodeContests
- Competition problems + solutions
- Format as code generation tasks
- Filter permissive licenses only
- Estimated: 3,000 examples

#### d) StarCoder Data (permissive subset)
- Various code tasks
- Estimated: 2,000 examples

**Total:** ~20,000 examples

---

### 4. Code-Pair Expansion (10K+ additional)

Already have 4,045 code-comment pairs from src/.

**Additional extraction:**
- Parse ALL TypeScript/JS files in src/ more thoroughly
- Include:
  * Function + JSDoc
  * Class + class comment
  * Interface + description
  * Error handlers
  * Complex algorithms with inline comments
  * Test cases + implementation
- Target: 10,000 additional pairs

**Method:**
- Enhanced parser that finds all code blocks with preceding comment
- Use local NLP (if needed) to generate comments for code without them
- Filter for meaningful pairs (>3 lines code, substantive comment)

---

### 5. Data Augmentation (5K examples)

From existing high-quality examples:
- Paraphrase user prompts (local NLP tools)
- Swap tools in similar contexts (e.g., FileRead → Glob)
- Add/remove context information
- Create "failed tool" scenarios with recovery
- Vary complexity levels

Target: 5,000 augmented examples

---

## Total Estimate

- OpenClaw logs: 10K
- Synthetic templates: 20K
- Public datasets: 20K
- Code-pairs: 10K
- Augmentation: 5K
- **Total: ~65,000 examples** (exceeds 50K target)

---

## Implementation Steps

1. **Session log mining script** - `scripts/mine_sessions.py`
2. **Synthetic data generator** - `scripts/generate_synthetic.py`
3. **Public dataset downloader** - `scripts/download_datasets.py`
4. **Code-pair extractor** - `scripts/extract_code_pairs.py`
5. **Data augmenter** - `scripts/augment_data.py`
6. **Quality filter** - `scripts/quality_filter.py`
7. **Dataset combiner** - `scripts/combine_datasets.py`

All scripts save to `training-data/scaled/` with source tracking.

---

## Quality Control

- All examples validated against tool schemas
- Deduplication (exact and near-duplicate)
- Minimum quality thresholds
- Balance across tools and complexity
- 80/10/10 train/val/test split

---

## Timeline (Manual)

Day 1: Session mining + code-pair extraction
Day 2: Synthetic generation + public dataset integration
Day 3: Augmentation + quality filtering + combining

We can produce 50K+ examples within a few days of focused work.

---

**Status:** Ready to implement step 1 (session mining) now.