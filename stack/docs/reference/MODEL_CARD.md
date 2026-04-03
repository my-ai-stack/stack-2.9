# Model Card: Stack 2.9

## Model Description

**Stack 2.9** is a fine-tuned AI coding assistant based on **Qwen2.5-Coder-32B**, enhanced with **Pattern Memory and Retrieval** capabilities. Unlike standard code models, Stack 2.9 learns from its interactions by storing successful problem-solution patterns and retrieving relevant precedents for new coding tasks. This allows the model to improve through accumulated experience, becoming more effective over time.

### Key Features

- **🧠 Pattern Memory System**: Stores and retrieves successful coding patterns, error recovery strategies, and tool-use workflows
- **💻 Advanced Code Generation**: Fine-tuned for Python, JavaScript, TypeScript, and 50+ languages
- **🔧 Tool Use Proficiency**: Native support for 37 OpenClaw tools including file operations, search, shell commands, and git
- **📊 128K Context Window**: Handles large codebases and multi-file reasoning
- **🌐 Multi-Provider Support**: Works with Ollama, OpenAI, Anthropic, OpenRouter, and Together AI

### Model Architecture

- **Base Model**: Qwen2.5-Coder-32B (32 billion parameters)
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **LoRA Configuration**:
  - Rank (r): 64
  - Alpha: 128
  - Dropout: 0.05
  - Target Modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **Quantization**: 4-bit AWQ optional for efficient deployment
- **Context Length**: 131,072 tokens

## Training Data Sources

Stack 2.9's fine-tuning uses a diverse, multi-source dataset curated for coding and tool-use scenarios:

### 1. Pattern Memory Data
- Source: Extracted from successful Stack 2.9 interaction logs
- Content: Code solutions with feedback, error recovery patterns, tool call sequences
- Size: ~5,000-10,000 examples (growing with usage)
- Format: JSONL with problem type, solution, success flag, execution metrics

### 2. Synthetic Examples
- Source: Template-based generation covering all 37 OpenClaw tools
- Content: Tool usage scenarios, parameter variations, multi-step workflows
- Size: 20,000+ generated examples
- Creation: Automated variation of base templates with synonyms, noise, and complexity scaling

### 3. Public Datasets
- **OpenAssistant (oasst1)**: Coding-related conversations (~5,000 examples)
- **CodeAct**: Executable code actions (~10,000 examples)
- **CodeContests**: Competition problems with solutions (~3,000 examples)
- **StarCoder Data**: Permissively licensed code (~2,000 examples)

### 4. Code-Comment Pairs
- Source: TypeScript/JavaScript files from src/ directory
- Content: Functions with JSDoc, classes with descriptions, algorithms with inline comments
- Size: 10,000+ code-documentation pairs
- Purpose: Learn code-documentation alignment and natural explanations

### 5. Advanced Patterns
- Complex multi-tool workflows
- Error handling and recovery
- Context management across files
- Voice command integration (future)

**Total Training Examples**: ~50,000-65,000 (scaling plan targets 50K+)

### Data Quality Filtering

All data undergoes:
- Deduplication via content hashing
- Minimum length thresholds (code: 3+ lines, comment: 10+ words)
- Validation against tool schemas
- Success rate filtering (patterns with >70% success kept)
- License compatibility check (permissive licenses only)

## Training Procedure

### Overview

Stack 2.9 is created through a two-stage process:

1. **Base Model**: Qwen2.5-Coder-32B (pretrained on large code corpus)
2. **Fine-tuning**: LoRA on coding + tool-use dataset (3 epochs)
3. **Optional Quantization**: 4-bit AWQ for efficient deployment

### Training Infrastructure

```bash
cd stack-2.9-training
./run_training.sh
```

The pipeline consists of:

1. **Data Preparation** (`prepare_data.py`)
   - Loads JSONL examples
   - Applies chat template for Qwen2.5
   - Tokenization with max_length=131072
   - Train/eval split (90/10)
   - Saves to HuggingFace datasets format

2. **LoRA Training** (`train_lora.py`)
   - Uses HuggingFace PEFT library
   - 4-bit quantization via bitsandbytes
   - Gradient checkpointing enabled
   - Optimizer: AdamW (default from transformers)
   - Learning rate schedule: warmup 100 steps, then linear decay

3. **Model Merging** (`merge_adapter.py`)
   - Combines LoRA weights with base model
   - Exports to HuggingFace format
   - Optional AWQ quantization

### Training Hyperparameters

| Parameter | Value |
|-----------|-------|
| Base Model | Qwen/Qwen2.5-Coder-32B |
| Epochs | 3 |
| Batch Size | 1 (per GPU) |
| Gradient Accumulation | 16 |
| Effective Batch Size | 16 |
| Learning Rate | 1.0 × 10⁻⁴ |
| Warmup Steps | 100 |
| Weight Decay | 0.01 |
| Max Gradient Norm | 1.0 |
| Max Sequence Length | 131,072 tokens |
| LoRA Rank (r) | 64 |
| LoRA Alpha | 128 |
| LoRA Dropout | 0.05 |
| Target Modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Quantization | 4-bit (bitsandbytes) |
| Mixed Precision | FP16 |
| Gradient Checkpointing | Yes |
| Optimizer | AdamW (default) |

### Hardware Requirements

| Configuration | Minimum | Recommended |
|---------------|---------|-------------|
| GPU VRAM | 32GB (single GPU) | 48GB+ (single) or 2×24GB |
| System RAM | 64GB | 128GB+ |
| Storage | 100GB SSD | 500GB NVMe |
| Training Time | 12-24 hours | 6-12 hours |

**Note**: Training can be distributed across multiple GPUs using DeepSpeed or FSDP (configuration not provided but possible with transformers).

### Monitoring and Logging

- **WandB Integration**: Optional tracking (`report_to: "wandb"`)
- **Logging Steps**: Every 10 steps
- **Evaluation Steps**: Every 100 steps
- **Checkpointing**: Every 500 steps, keep last 3 checkpoints

## Intended Use

### Primary Use Cases

✅ **Allowed**:
- AI-assisted coding and code completion
- Code explanation and documentation generation
- Debugging and error analysis
- Tool-use automation in OpenClaw environments
- Educational purposes and learning to code
- Research on pattern-based AI improvement

### Out-of-Scope Use Cases

❌ **Not Recommended**:
- High-stakes production code without human review (risk of bugs)
- Security-critical applications (model may generate vulnerabilities)
- Medical, legal, or financial decision-making
- Generating harmful, malicious, or unethical code
- Automated deployment without testing (CI/CD gates required)
- Large-scale redistribution without compliance checks

### Target Users

- Software developers seeking AI assistance
- Researchers studying tool-augmented language models
- Educators teaching programming concepts
- Hobbyists exploring AI coding tools

## Limitations

### Technical Limitations

1. **Context Window**: 128K tokens can handle large files but may have performance degradation at max length
2. **Tool Dependencies**: Requires OpenClaw framework for full tool functionality; tool calls outside that context need adaptation
3. **Quantization Trade-offs**: 4-bit models may have slightly reduced accuracy vs. full precision
4. **Training Data Biases**: Dataset focuses primarily on Python and web development; may be less capable in niche domains (embedded systems, specialized scientific computing)
5. **Pattern Memory Freshness**: Patterns are learned from interactions; initial deployments have limited pattern library

### Performance Caveats

- **Hallucinations**: May generate plausible-looking but incorrect code; always verify with tests/linting
- **Security**: Can suggest code with vulnerabilities; security review mandatory for production use
- **Licensing**: Generated code may inadvertently reproduce copyrighted snippets; use license compatibility checks
- **Tool Reliability**: Tool execution depends on host environment; errors can cascade

### Not a Replacement

Stack 2.9 is **not**:
- A fully autonomous software engineer (requires human oversight)
- A substitute for unit testing, integration testing, or code review
- Guaranteed to produce production-ready code
- Certified for safety-critical applications

## Evaluation

Benchmark evaluation is currently in progress. Results will be published upon completion.

See `BENCHMARKS.md` and `EVALUATION.md` for the evaluation plan and status.

**Expected Baselines** (based on Qwen2.5-Coder-32B):
- HumanEval: ~70-72% Pass@1
- MBPP: ~75-77% Pass@1
- Tool Use: ~85-92% task completion (custom benchmark)

## License

**Stack 2.9** (this fine-tuned model and associated code) is licensed under the **MIT License**.

See [LICENSE](LICENSE) file for full text.

### License Dependencies

- **Base Model**: Qwen2.5-Coder-32B - Apache License 2.0 (Alibaba)
- **Training Code**: HuggingFace Transformers, PEFT, bitsandbytes - Apache 2.0 / BSD
- **Evaluation Code**: Custom implementations - MIT
- **Aggregate Work**: MIT + Apache 2.0 compatible

**Redistribution**: You may use, modify, and distribute this model under MIT terms, provided you comply with the Apache 2.0 license for the base Qwen model components. The MIT license supersedes for modifications/adaptations you make.

## Citation

If you use Stack 2.9 in your research or applications, please cite:

```bibtex
@misc{stack29_2025,
  title={Stack 2.9: Pattern Memory AI Coding Assistant},
  author={Walid Sobhi and OpenClaw Team},
  year={2026},
  publisher={GitHub},
  url={https://github.com/my-ai-stack/stack-2.9}
}
```

## Contact & Support

- **GitHub Repository**: https://github.com/my-ai-stack/stack-2.9
- **Issues**: https://github.com/my-ai-stack/stack-2.9/issues
- **Documentation**: https://github.com/my-ai-stack/stack-2.9/docs
- **Discord Community**: [Join our server](link-to-be-added)

---

**Last Updated**: 2025-04-02
**Version**: 2.9.0 (training in progress)
**Model Card Authors**: OpenClaw Research Team
