# Stack 2.9 Roadmap

> Last updated: April 2026

## Current Status

### What's Working ✅

- **Basic code generation** - The model can generate Python, JavaScript, and other code based on prompts
- **CLI interface** - Working command-line interface (`stack.py`, `src/cli/`)
- **Multi-provider support** - Ollama, OpenAI, Anthropic, OpenRouter, Together AI integrations
- **46 built-in tools** - File operations, git, shell, web search, memory, task planning
- **Pattern Memory infrastructure** - Observer, Learner, Memory components implemented
- **Training pipeline** - LoRA fine-tuning scripts, data preparation, model merging
- **Deployment options** - Docker, RunPod, Vast.ai, Kubernetes, HuggingFace Spaces
- **128K context window** - Extended from base model's 32K

### What's Broken or Missing ⚠️

- **Tool calling not trained** - Model doesn't reliably use tools; needs fine-tuning on tool patterns
- **Benchmark scores unverifiable** - Previous claims removed after audit found only 20/164 HumanEval problems tested
- **Self-evolution not functional** - Observer/Learner components exist but not connected to training pipeline
- **Voice integration incomplete** - Coqui XTTS integration present but not tested
- **Evaluation infrastructure in progress** - New proper evaluation framework built but not run on full benchmarks

### What Needs Testing 🔧

- Full HumanEval (164 problems) evaluation
- Full MBPP (500 problems) evaluation
- Tool-calling accuracy with real tasks
- Pattern Memory retrieval and effectiveness
- Voice input/output pipeline
- Multi-provider compatibility

### What Needs Documentation 📚

- Tool definitions and schemas
- API reference (internal/ARCHITECTURE.md exists but needs updating)
- Pattern Memory usage guide
- Deployment troubleshooting
- Evaluation methodology

---

## Timeline with Milestones

### Short-Term (1-2 Weeks)

| Milestone | Description | Status |
|-----------|-------------|--------|
| **S1.1** | Run full HumanEval (164 problems) with proper inference | Not started |
| **S1.2** | Run full MBPP (500 problems) with proper inference | Not started |
| **S1.3** | Document all 46 tool definitions in `docs/TOOLS.md` | In progress |
| **S1.4** | Fix evaluation scripts to use real model inference | Needed |
| **S1.5** | Create minimal reproducible test for tool calling | Not started |

**Owner:** Community contribution welcome

### Medium-Term (1-3 Months)

| Milestone | Description | Status |
|-----------|-------------|--------|
| **M2.1** | Fine-tune model on tool-calling patterns (RTMP data) | Not started |
| **M2.2** | Implement and test self-evolution loop (Observer → Learner → Memory → Trainer) | Not started |
| **M2.3** | Run full benchmark evaluation and publish verified scores | Not started |
| **M2.4** | Add MCP server support for external tool integration | Partial |
| **M2.5** | Voice integration end-to-end testing | Not started |
| **M2.6** | Implement pattern extraction from production usage | Not started |

**Owner:** Requires training compute budget or community contribution

### Long-Term (6+ Months)

| Milestone | Description | Status |
|-----------|-------------|--------|
| **L3.1** | RLHF training for improved tool selection | Future |
| **L3.2** | Team sync infrastructure (PostgreSQL + FastAPI) | Designed, not implemented |
| **L3.3** | Federated learning for privacy-preserving updates | Future |
| **L3.4** | Multi-modal support (images → code) | Future |
| **L3.5** | Real-time voice-to-voice conversation | Future |

**Owner:** Long-term vision, needs significant resources

---

## How to Contribute

### By Priority

1. **Run evaluations** - Help us verify benchmark scores by running `python stack_2_9_eval/run_proper_evaluation.py`
2. **Test tool calling** - Try the model with various tools and report what works/doesn't
3. **Documentation** - Improve docs, especially tool definitions and API reference
4. **Bug reports** - Open issues with reproduction steps
5. **Code contributions** - See CONTRIBUTING.md for guidelines

### Contribution Areas

| Area | Skill Needed | Priority |
|------|--------------|----------|
| Evaluation | Python, ML benchmarking | High |
| Tool calling tests | Python, CLI usage | High |
| Documentation | Technical writing | Medium |
| Training scripts | PyTorch, PEFT | Medium |
| Deployment | Docker, K8s, Cloud | Low |
| Pattern Memory | Vector databases, ML | Low |

### Quick Wins for Contributors

- Run `python stack.py -c "List files in current directory"` and report if tools work
- Review `stack/eval/results/` and verify evaluation logs
- Check `docs/TOOLS.md` accuracy against actual tool implementations
- Test with different providers (`--provider ollama|openai|anthropic`)

---

## Technical Notes

### Known Limitations

1. **Tool calling is not trained** - The base model has tool capabilities but Stack 2.9 hasn't been fine-tuned to use them reliably
2. **Pattern Memory is read-only** - The system stores patterns but doesn't automatically retrain on them yet
3. **Evaluation uses stub data** - Some eval scripts return pre-canned answers instead of running model
4. **Voice integration untested** - Code exists but hasn't been validated end-to-end

### Next Training Run Requirements

To fix tool calling, the next training run needs:

- Dataset: `data/rtmp-tools/combined_tools.jsonl` (already generated)
- Compute: ~1 hour on A100 for LoRA fine-tuning
- Configuration: Target tool_call logits, use `tool_use_examples.jsonl`

---

## Contact

- **Issues:** https://github.com/my-ai-stack/stack-2.9/issues
- **Discussions:** https://github.com/my-ai-stack/stack-2.9/discussions
- **Discord:** (link in README)

---

*This roadmap is a living document. Updates based on community feedback and project progress.*