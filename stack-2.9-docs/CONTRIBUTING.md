# Contributing to Stack 2.9

Thank you for your interest in contributing to Stack 2.9! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Writing Tests](#writing-tests)
- [Documentation Guidelines](#documentation-guidelines)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

**Our Standards:**

- Be kind and respectful in all interactions
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior:**

- Harassment, discrimination, or intimidation
- Personal attacks or derogatory remarks
- Publishing others' private information without permission
- Other conduct that could reasonably be considered inappropriate

---

## Getting Started

### Fork the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/stack-2.9.git
cd stack-2.9

# Add upstream remote
git remote add upstream https://github.com/openclaw/stack-2.9.git
```

### Stay Updated

```bash
# Fetch latest changes from upstream
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Update your feature branch
git checkout your-feature-branch
git rebase main
```

---

## Development Setup

### Prerequisites

- Python 3.8+ (3.11+ recommended)
- Node.js 18+ (20 LTS recommended)
- Git
- GPU for model-related testing (optional but recommended)

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Install Node.js dependencies (for voice features)
npm install
```

### Verify Installation

```bash
# Run tests
pytest

# Check code formatting
make lint

# Run type checking
mypy stack_cli/
```

### IDE Setup

**VS Code:**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true
  }
}
```

**PyCharm:**

1. Settings → Project → Python Interpreter → Add → Existing Environment
2. Select `.venv/bin/python`
3. Enable Black for formatting in Settings → Python → Formatting → Black

---

## Code Style

### Python

We follow PEP 8 with some modifications:

- Line length: 100 characters (not 79)
- Use type hints where possible
- Docstrings for all public functions and classes

**Style Guide:**

```python
"""
Module docstring describing the module's purpose.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class ExampleClass:
    """Class docstring describing the class.
    
    Attributes:
        name: The name of the example.
        value: The value of the example.
    """
    name: str
    value: int
    
    def __post_init__(self):
        """Validate after initialization."""
        if self.value < 0:
            raise ValueError("Value must be non-negative")
    
    def process(self, data: List[str]) -> Dict[str, int]:
        """Process data and return results.
        
        Args:
            data: List of strings to process.
            
        Returns:
            Dictionary mapping strings to their lengths.
            
        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        return {item: len(item) for item in data}
```

### JavaScript/TypeScript

```typescript
/**
 * Interface for a user configuration.
 */
interface UserConfig {
  /** User's display name */
  name: string;
  /** User's email address */
  email: string;
  /** Whether the user is enabled */
  enabled: boolean;
}

/**
 * Process user configuration and return formatted string.
 * 
 * @param config - The user configuration
 * @returns Formatted configuration string
 */
export function formatConfig(config: UserConfig): string {
  const { name, email, enabled } = config;
  
  if (!enabled) {
    return `${name} (disabled)`;
  }
  
  return `${name} <${email}>`;
}
```

### Shell Scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

# Constant for the application name
readonly APP_NAME="stack-2.9"
readonly LOG_DIR="/var/log/${APP_NAME}"

# Main function
main() {
    log "Starting ${APP_NAME}..."
    # Implementation here
}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Run main
main "$@"
```

---

## Making Changes

### Create a Branch

```bash
# Start from an updated main branch
git checkout main
git pull upstream main

# Create a new feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description

# Or for documentation
git checkout -b docs/improvement-description
```

### Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<description>` | `feature/voice-integration` |
| Bug Fix | `fix/<issue>-<description>` | `fix/123-memory-leak` |
| Documentation | `docs/<description>` | `docs/api-reference` |
| Refactoring | `refactor/<description>` | `refactor/tool-execution` |
| Testing | `test/<description>` | `test/improve-coverage` |

### Making Commits

```bash
# Stage changes
git add path/to/changed/file.py

# Commit with a descriptive message
git commit -m "Add voice cloning support to the tool system

- Added speech_to_text and text_to_speech tools
- Implemented voice_clone tool for custom voice synthesis
- Added voice processing pipeline with Coqui TTS
- Updated documentation with voice examples

Closes: #123"
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**

```
feat(tools): add file search functionality

Implemented fuzzy file search using fzf for quick file discovery.
Added search_files tool that supports:
- Pattern matching with glob
- Fuzzy search with fzf
- File type filtering

Closes: #45
```

---

## Submitting Pull Requests

### Before Submitting

1. **Run Tests:**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stack_cli --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v
```

2. **Run Linters:**

```bash
# All linters
make lint

# Individual linters
black --check stack_cli/
flake8 stack_cli/
mypy stack_cli/
```

3. **Format Code:**

```bash
# Auto-format code
black stack_cli/

# Sort imports
isort stack_cli/
```

### Pull Request Process

1. **Create Pull Request:**

```bash
# Push your branch
git push origin feature/your-feature-name

# Open PR on GitHub or use CLI
gh pr create --title "Add feature" --body "Description"
```

2. **PR Description Template:**

```markdown
## Summary
Brief description of what this PR does.

## Changes Made
- List of specific changes
- Another change

## Motivation
Why is this change needed?

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests passed
- [ ] Manual testing completed

## Screenshots (if applicable)

## Related Issues
Closes #123
```

3. **Review Process:**

- Address review comments promptly
- Keep commits atomic and well-described
- Force push to update PR if needed (after reviewers approve)

### What We Look For

✅ Code that follows our style guidelines  
✅ Tests that cover the new functionality  
✅ Documentation updates (if applicable)  
✅ Clear commit messages  
✅ No breaking changes (or clearly documented)  
✅ Performance implications considered  

---

## Writing Tests

### Test Structure

```python
# tests/test_example.py
"""
Tests for the example module.
"""

import pytest
from unittest.mock import Mock, patch
from stack_cli.example import ExampleClass, process_data


class TestExampleClass:
    """Tests for ExampleClass."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.example = ExampleClass(name="test", value=42)
    
    def test_initialization(self):
        """Test class initialization."""
        assert self.example.name == "test"
        assert self.example.value == 42
    
    def test_negative_value_raises(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ExampleClass(name="test", value=-1)
    
    def test_process_returns_dict(self):
        """Test that process returns expected dictionary."""
        result = self.example.process(["hello", "world"])
        assert isinstance(result, dict)
        assert result["hello"] == 5
        assert result["world"] == 5
    
    def test_process_empty_list_raises(self):
        """Test that processing empty list raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            self.example.process([])


class TestProcessData:
    """Tests for process_data function."""
    
    @patch("stack_cli.example.external_service")
    def test_calls_external_service(self, mock_service):
        """Test that external service is called correctly."""
        mock_service.return_value = {"status": "ok"}
        
        result = process_data(["test"])
        
        mock_service.assert_called_once_with(["test"])
        assert result["status"] == "ok"
```

### Test Categories

| Category | Location | Description |
|----------|----------|-------------|
| Unit Tests | `tests/unit/` | Test individual functions/classes |
| Integration Tests | `tests/integration/` | Test component interactions |
| API Tests | `tests/api/` | Test API endpoints |
| Tool Tests | `tests/tools/` | Test tool implementations |
| Self-Evolution Tests | `tests/self_evolution/` | Test learning system |

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/unit/

# With coverage
pytest --cov=stack_cli --cov-report=term-missing --cov-report=html

# Watch mode (auto-run on changes)
ptw  # pytest-watch

# Specific test
pytest tests/test_example.py::TestExampleClass::test_initialization -v
```

### Test Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_project(temp_dir):
    """Create a sample project structure for testing."""
    project = temp_dir / "project"
    project.mkdir()
    
    # Create sample files
    (project / "main.py").write_text("def main(): pass")
    (project / "test.py").write_text("def test(): pass")
    
    return project


@pytest.fixture
def mock_memory():
    """Mock memory system for isolated testing."""
    from unittest.mock import MagicMock
    
    memory = MagicMock()
    memory.store_memory.return_value = 1
    memory.find_similar.return_value = []
    
    return memory
```

---

## Documentation Guidelines

### Docstring Format

We use Sphinx-style docstrings:

```python
def function_name(param1: str, param2: int, param3: Optional[List] = None) -> Dict:
    """Brief description of the function.
    
    Longer description if needed, explaining what the function does,
    its purpose, and any important details about its behavior.
    
    Args:
        param1: Description of param1.
        param2: Description of param2. Must be positive.
        param3: Optional description. Defaults to None.
        
    Returns:
        Description of the return value. Includes type information.
        
    Raises:
        ValueError: When param2 is negative.
        TypeError: When param1 is not a string.
        
    Example:
        >>> result = function_name("hello", 42)
        >>> print(result)
        {'param1': 'hello', 'param2': 42}
    """
    pass
```

### README Updates

When adding new features, update the README.md:

1. Add feature to the features table
2. Include example usage
3. Update architecture diagram if needed
4. Add benchmark results if applicable

### API Documentation

For API changes, update `API.md`:

```markdown
### Endpoint Name

**Endpoint:** `POST /endpoint`

**Description:** What this endpoint does.

**Request Body:**

```json
{
  "field1": "description",
  "field2": 123
}
```

**Response:**

```json
{
  "result": "description"
}
```
```

---

## Bug Reports

### Before Submitting a Bug Report

- Search existing issues to avoid duplicates
- Try to reproduce the issue with the latest version
- Gather relevant information:
  - Python version
  - Stack 2.9 version
  - Operating system
  - Error message and stack trace
  - Steps to reproduce

### Submitting a Bug Report

Use the GitHub issue tracker with the "bug" label:

```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Run '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.4]
- Stack 2.9: [e.g., 1.0.0]

## Stack Trace
```
Full error traceback here
```

## Additional Context
Any other relevant information.
```

---

## Feature Requests

### Before Submitting a Feature Request

- Search existing issues and PRs
- Consider if the feature aligns with project goals
- Think about implementation approaches

### Submitting a Feature Request

```markdown
## Feature Description
Clear description of the proposed feature.

## Motivation
Why is this feature needed? What problem does it solve?

## Proposed Implementation
How you envision implementing this feature.

## Alternatives Considered
Other approaches you've considered.

## Additional Context
Mockups, diagrams, or other supporting materials.
```

---

## Recognition

Contributors will be recognized in:

- The project's README acknowledgments section
- Release notes for their contributions
- Our community highlights

---

## Questions?

- **GitHub Discussions**: [Q&A Category](https://github.com/openclaw/stack-2.9/discussions)
- **Discord**: Join our community server
- **Email**: support@stack2.9.openclaw.org

---

Thank you for contributing to Stack 2.9! 🎉
