# Pattern Memory Evolution

The Pattern Memory Moat is a system for capturing, storing, and sharing code patterns across teams. It transforms individual learning into collective intelligence.

## Table of Contents

1. [Auto-Extraction](#auto-extraction)
2. [Team Sync](#team-sync)
3. [Weight Fusion](#weight-fusion)
4. [API Reference](#api-reference)

---

## Auto-Extraction

Extract patterns automatically from your Git history. The system analyzes commit messages, identifies bug fixes and features, and stores the before/after code changes.

### How It Works

The `extract_patterns_from_git.py` script:

1. **Scans Git History**: Reads through commit messages and diffs
2. **Identifies Patterns**: Uses keywords to classify commits as bug fixes or features
3. **Extracts Context**: Captures before/after code with metadata
4. **Stores in JSONL**: Outputs structured data suitable for training

### Usage

```bash
# Extract patterns from all commits
python scripts/extract_patterns_from_git.py \
    --repo-path /path/to/repo \
    --output patterns.jsonl

# Only recent commits
python scripts/extract_patterns_from_git.py \
    --repo-path /path/to/repo \
    --output patterns.jsonl \
    --since-date "2024-01-01"
```

### Output Format

Each line in the JSONL output:

```json
{
  "pattern_id": "a1b2c3d4e5f6g7h8",
  "problem_type": "bug_fix",
  "before_code": "def buggy_function():\n    return None + 1",
  "after_code": "def fixed_function():\n    return 1",
  "commit_msg": "fix: handle None case in function",
  "author": "developer@example.com",
  "date": "2024-03-15 10:30:00",
  "confidence": 0.85
}
```

### Problem Types

- `bug_fix`: Commits that resolve issues (keywords: fix, bug, hotfix, patch, resolve)
- `feature_addition`: Commits that add new functionality (keywords: feat, add, implement, enhance)
- `unknown`: Other commits (typically skipped)

### Confidence Scoring

The confidence score (0.0-1.0) reflects pattern quality:

- Base: 0.5
- +0.2 for clear bug fix keywords
- +0.15 for clear feature keywords
- +0.15 for having both before and after code
- +0.1 for substantial changes (>100 chars)
- +0.1 for large changes (>500 chars)

---

## Team Sync

Share and sync patterns across your team using a shared PostgreSQL database.

### PostgreSQL Schema

```sql
CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_type VARCHAR(50) NOT NULL,
    solution_hash VARCHAR(64) NOT NULL,
    code_before TEXT NOT NULL,
    code_after TEXT NOT NULL,
    success_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT unique_solution UNIQUE (solution_hash),
    INDEX idx_problem_type (problem_type),
    INDEX idx_success_count (success_count DESC)
);

CREATE TABLE pattern_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID REFERENCES patterns(id),
    user_id VARCHAR(255) NOT NULL,
    helpful BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE adapter_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_name VARCHAR(100) NOT NULL,
    adapter_path VARCHAR(500) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);
```

### FastAPI Endpoints

#### GET /patterns

List patterns with filtering and pagination.

```bash
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8000/patterns?problem_type=bug_fix&limit=20"
```

Response:
```json
{
  "patterns": [...],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

#### POST /patterns

Add a new pattern.

```bash
curl -X POST -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"problem_type": "bug_fix", "code_before": "...", "code_after": "..."}' \
     "http://localhost:8000/patterns"
```

#### POST /patterns/{id}/feedback

Submit feedback on a pattern.

```bash
curl -X POST -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"helpful": true}' \
     "http://localhost:8000/patterns/123e4567-e89b-12d3-a456-426614174000/feedback"
```

### Authentication

API key authentication via `X-API-Key` header:

```python
# Server-side middleware
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return await call_next(request)
```

### Conflict Resolution

When multiple team members contribute similar patterns:

1. **Pattern Similarity Detection**: Hash-based deduplication
2. **Merge Strategy**: Patterns with similar `solution_hash` are merged
3. **Success Rate Tracking**: `success_count` increases with positive feedback
4. **Priority**: Patterns with higher `success_count` rank higher in queries

---

## Weight Fusion

Combine LoRA adapters from multiple users using weighted averaging based on success rates.

### Algorithm

```
merged_weight = Σ(adapter_i.weight * adapter_i.success_rate) / Σ(success_rate)
```

This ensures adapters that have shown better results contribute more to the final merged adapter.

### Merge Script Usage

```bash
# Basic merge with manual weights
python scripts/merge_lora_adapters.py \
    --adapters user1_adapter.safetensors user2_adapter.safetensors \
    --weights 0.6 0.4 \
    --output merged_adapter.safetensors

# Merge using success rates (auto-computes proportional weights)
python scripts/merge_lora_adapters.py \
    --adapters alice_adapter.safetensors bob_adapter.safetensors \
    --success-rates 0.85 0.65 \
    --output team_adapter.safetensors

# Equal weights (default)
python scripts/merge_lora_adapters.py \
    --adapters adapter1.safetensors adapter2.safetensors \
    --output merged.safetensors
```

### Versioning

Each merge creates a version record:

```json
{
  "version_name": "v2.1-team-merge",
  "adapter_path": "/adapters/merged_v2.1.safetensors",
  "created_by": "alice@example.com",
  "created_at": "2024-03-15T10:30:00Z",
  "parent_versions": ["v2.0", "user-alice-v3", "user-bob-v2"]
}
```

### Rollback

To revert to a previous merged adapter:

```bash
# List available versions
ls -la adapters/versions/

# Restore previous version
cp adapters/versions/v2.0.safetensors adapters/merged.safetensors
```

Or via API:

```bash
curl -X POST -H "X-API-Key: your-api-key" \
     -d '{"version_id": "123e4567-e89b-12d3-a456-426614174000"}' \
     "http://localhost:8000/adapters/rollback"
```

---

## API Reference

### Patterns API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patterns` | List patterns |
| GET | `/patterns/{id}` | Get pattern by ID |
| POST | `/patterns` | Create pattern |
| POST | `/patterns/{id}/feedback` | Submit feedback |
| DELETE | `/patterns/{id}` | Delete pattern |

### Adapter API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/adapters` | List adapter versions |
| POST | `/adapters/merge` | Merge multiple adapters |
| POST | `/adapters/{id}/activate` | Set as active adapter |
| POST | `/adapters/rollback` | Rollback to previous version |

### Health Check

```bash
curl "http://localhost:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

---

## Example Workflow

### 1. Extract Patterns from Project

```bash
# Extract patterns from your codebase
python scripts/extract_patterns_from_git.py \
    --repo-path ./my-project \
    --output patterns.jsonl \
    --since-date "2024-01-01"
```

### 2. Upload to Team Database

```python
import requests

with open('patterns.jsonl') as f:
    for line in f:
        pattern = json.loads(line)
        requests.post(
            "http://team-patterns.example.com/patterns",
            headers={"X-API-Key": "your-key"},
            json=pattern
        )
```

### 3. Merge Team Patterns

```bash
# Merge adapters from team members
python scripts/merge_lora_adapters.py \
    --adapters alice_adapter.safetensors bob_adapter.safetensors carol_adapter.safetensors \
    --success-rates 0.90 0.75 0.85 \
    --output team_merged.safetensors
```

### 4. Activate for Team Use

The merged adapter with the highest success rate becomes the new team baseline.

---

## Files Reference

| File | Description |
|------|-------------|
| `scripts/extract_patterns_from_git.py` | Git history pattern extractor |
| `scripts/merge_lora_adapters.py` | LoRA adapter merger |
| `docs/pattern-moat.md` | This documentation |
