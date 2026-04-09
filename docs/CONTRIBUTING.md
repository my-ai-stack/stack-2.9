# Contributing to Stack 2.9

> Last updated: April 2026

Thank you for your interest in contributing to Stack 2.9! This document outlines how you can help.

## Project State

**Before contributing, understand where the project stands:**

| Area | Status | Notes |
|------|--------|-------|
| Basic code generation | ✅ Working | Main strength of the model |
| Tool calling | ⚠️ Not trained | Needs fine-tuning on tool patterns |
| Benchmark scores | ⚠️ Pending | Full evaluation not yet run |
| Self-evolution | 🔧 Incomplete | Components exist but not connected |
| Documentation | 🔧 In progress | Some areas need work |

## Quick Start

```bash
# 1. Fork the repository
git fork https://github.com/my-ai-stack/stack-2.9.git

# 2. Clone your fork
git clone https://github.com/YOUR_USER/stack-2.9.git
cd stack-2.9

# 3. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows

# 4. Install dependencies
pip install -r requirements.txt
```

## What to Work On

### High Priority

1. **Evaluation** - Run full HumanEval/MBPP benchmarks
   - See `stack/eval/run_proper_evaluation.py`
   - Requires: Python, Ollama or API key

2. **Tool calling tests** - Test and document tool usage
   - Run `python stack.py -c "Your command here"`
   - Report what works/doesn't in issues

3. **Documentation** - Improve tool definitions, API docs
   - Check `docs/TOOLS.md` for accuracy
   - Update `stack/internal/ARCHITECTURE.md`

### Medium Priority

4. **Training scripts** - Improve fine-tuning pipeline
   - See `stack/training/`
   - ⚠️ Do NOT modify Kaggle notebook or training data generation

5. **Deployment** - Fix deployment scripts
   - See `stack/deploy/`, `runpod_deploy.sh`

### Lower Priority

6. **Pattern Memory** - Connect Observer → Learner → Memory → Trainer
7. **Voice integration** - Test end-to-end voice pipeline
8. **MCP support** - Improve Model Context Protocol integration

## What NOT to Touch

⚠️ **Do NOT modify without explicit approval:**

- `kaggle_train_stack29_v5.ipynb` - Kaggle training notebook
- `colab_train_stack29.ipynb` - Colab training notebook
- Training data generation scripts in `data/`
- Model weights in `base_model_qwen7b/`

These are core training components. Changes here affect the model itself.

## Code Style

- **Python:** Follow PEP 8, use type hints where possible
- **TypeScript:** Use strict mode, add JSDoc comments
- **Shell:** Use `shellcheck` on bash scripts
- **General:** Add docstrings to new functions, include examples

### Pre-commit Checks

```bash
# Run tests before submitting
pytest samples/ -v

# Check code formatting
ruff check src/ samples/ --fix
black src/ samples/
```

##提交PR

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests
pytest samples/ -v

# Commit with clear message
git commit -m "Add: description of what you changed"

# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request
# Fill in the PR template with:
# - What you changed
# - Why it's needed
# - Testing you did
# - Screenshots if applicable
```

## Pull Request Guidelines

1. **Describe the change clearly** - What does this fix or add?
2. **Link related issues** - Use "Fixes #123" if applicable
3. **Include tests** - Add unit tests for new features
4. **Update docs** - If you add a feature, document it
5. **Be patient** - Reviewers may take a few days to respond

## Reporting Issues

When reporting bugs:

```markdown
## Description
Brief description of the issue

## Steps to Reproduce
1. Run `...`
2. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happened

## Environment
- OS: 
- Python version:
- Provider: (ollama/openai/etc)
- Model:
```

## Communication

- **Issues:** GitHub Issues for bugs/features
- **Discussions:** GitHub Discussions for questions
- **Discord:** Link in README

## Recognition

Contributors will be listed in:
- README.md "Acknowledgments" section
- CONTRIBUTORS file (if created)

---

**Questions?** Open a GitHub Discussion or ask in Discord.