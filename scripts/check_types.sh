#!/usr/bin/env bash
# Run mypy type checking on the codebase
set -e

echo "🔍 Running mypy type checks..."

# Run mypy on key Python files
mypy \
    --python-version 3.8 \
    --warn-return-any \
    --warn-unused-configs \
    --ignore-missing-imports \
    --strict-optional \
    --warn-redundant-casts \
    --warn-unused-ignores \
    --show-error-codes \
    --show-column-numbers \
    test_model.py \
    evaluate_model.py \
    inference_api.py \
    merge_simple.py \
    train_local.py \
    train_simple_nobnb.py \
    src/ \
    stack/ \
    || {
        echo "❌ mypy found type errors"
        exit 1
    }

echo "✅ mypy type check passed"
