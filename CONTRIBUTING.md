# Contributing to Stack 2.9

Thank you for your interest in contributing! Stack 2.9 is an open-source project aimed at creating a fully open, voice-enabled coding assistant.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Community](#community)

## Code of Conduct

This project adheres to the [OpenClaw Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/stack-2.9.git
   cd stack-2.9
   ```
3. **Install dependencies**:
   ```bash
   make install
   ```
4. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/amazing-feature
   ```

## How to Contribute

There are many ways to contribute:

### 🐛 Bug Reports
- Use GitHub Issues
- Include: what happened, expected behavior, steps to reproduce, environment details

### ✨ Feature Requests
- Open an issue to discuss proposed changes before starting work
- Explain the use case and why the feature would be valuable

### 📖 Documentation
- Fix typos, clarify instructions
- Add examples, tutorials, API reference improvements

### 🧪 Testing & Evaluation
- Help expand the evaluation suite (add benchmarks)
- Run benchmarks on your hardware and share results
- Create test cases for tools

### 🎤 Voice Data
- Contribute voice samples (with consent) to improve TTS quality
- Help with speech-to-text model evaluation

### 🛠️ Code Contributions
- Improve training data quality/quantity
- Add new tools to the OpenClaw toolset
- Optimize inference performance
- Add IDE integrations (VS Code, JetBrains extensions)

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Docker & Docker Compose
- Git
- GNU Make

### Local Development

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Run tests**:
   ```bash
   make test
   ```

4. **Start local services**:
   ```bash
   make deploy-local
   ```

5. **Test the API**:
   ```bash
   curl http://localhost:8000/health
   ```

### Working on Specific Components

- **Training pipeline**: work in `stack-2.9-training/`
- **Deployment scripts**: work in `stack-2.9-deploy/`
- **Voice integration**: work in `stack-2.9-voice/`
- **Documentation**: work in `stack-2.9-docs/` or root README.md

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features or bug fixes
3. **Ensure CI passes** (we'll add GitHub Actions soon)
4. **Create a Pull Request** with:
   - Clear title and description
   - Reference any related issues
   - Screenshots for UI changes
   - Note any breaking changes

5. **Code Review**:
   - Keep PRs focused (one change at a time)
   - Respond to review feedback
   - Squash commits before merging

### PR Template

```markdown
## What does this PR do?

[Describe the change]

## Why is this needed?

[Explain the motivation]

## What changed?

- [ ] Added new files
- [ ] Modified existing files
- [ ] Deleted files
- [ ] Updated documentation

## Testing

[How did you test this?]

## Screenshots (if applicable)

[Add screenshots]

## Checklist

- [ ] I've read the [Contributing Guide](CONTRIBUTING.md)
- [ ] I've updated the documentation
- [ ] I've added tests for new functionality
- [ ] All tests pass locally
- [ ] I've formatted code (prettier/eslint/black)
```

## Style Guidelines

### Python
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Type hints required for function signatures
- Docstrings: Google style

```python
def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: Position in the Fibonacci sequence (0-indexed)

    Returns:
        The nth Fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    # implementation...
```

### TypeScript/JavaScript
- Use [Prettier](https://prettier.io/) formatting
- Follow the existing code style in `src/`
- ESLint rules from `.eslintrc.js`

### Commit Messages
- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- Example: `feat(training): add LoRA rank configuration option`

## Testing

### Running Tests
```bash
make test
```

### Adding Tests
- Place tests in `__tests__/` directories or `*_test.py` files
- Use pytest for Python, Jest for Node.js
- Aim for reasonable coverage, especially for critical paths

### Test Categories
- **Unit tests**: Individual functions/classes
- **Integration tests**: Multi-component workflows
- **Benchmark tests**: Performance measurements (in `stack-2.9-eval/`)

## Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs/feature requests
- **Discord**: Coming soon!

## Recognition

Contributors will be listed in:
- `README.md` (top contributors)
- `CREDITS.md` (if applicable)
- Release notes

## Legal

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Questions?

Feel free to open an issue or reach out to the maintainers.

---

Happy contributing! 🚀