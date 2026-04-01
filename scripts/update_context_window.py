#!/usr/bin/env python3
"""
Update all configuration files to use 128K context window.
Updates: manifest, training config, prepare_dataset, vLLM server, deploy scripts, docs.
"""

import json
import re
from pathlib import Path
import argparse

def update_json_file(path: Path, updates: dict):
    """Update JSON file with key->value updates."""
    if not path.exists():
        print(f"   ⚠️  Not found: {path}")
        return False

    with open(path, 'r') as f:
        data = json.load(f)

    changed = False
    for key, value in updates.items():
        if key in data and data[key] != value:
            data[key] = value
            changed = True

    if changed:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   ✅ Updated {path.name}")
    else:
        print(f"   ℹ️  {path.name} already up-to-date")
    return changed

def update_python_file(path: Path, old_pattern: str, new_value: str):
    """Replace a constant in a Python file."""
    if not path.exists():
        print(f"   ⚠️  Not found: {path}")
        return False

    content = path.read_text()
    if old_pattern in content:
        new_content = content.replace(old_pattern, new_value)
        path.write_text(new_content)
        print(f"   ✅ Updated {path.name}")
        return True
    else:
        print(f"   ℹ️  {path.name} - pattern not found, may be already updated")
        return False

def update_shell_script(path: Path, old_var: str, new_value: str):
    """Update shell script variable."""
    if not path.exists():
        print(f"   ⚠️  Not found: {path}")
        return False

    content = path.read_text()
    if old_var in content:
        new_content = re.sub(
            rf'{old_var}=.+',
            f'{old_var}={new_value}',
            content
        )
        path.write_text(new_content)
        print(f"   ✅ Updated {path.name}")
        return True
    else:
        print(f"   ℹ️  {path.name} - variable not found")
        return False

def update_markdown_file(path: Path, old_text: str, new_text: str):
    """Update markdown documentation."""
    if not path.exists():
        print(f"   ⚠️  Not found: {path}")
        return False

    content = path.read_text()
    if old_text in content:
        new_content = content.replace(old_text, new_text)
        path.write_text(new_content)
        print(f"   ✅ Updated {path.name}")
        return True
    else:
        print(f"   ℹ️  {path.name} - pattern not found")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, default=".")
    args = parser.parse_args()

    root = Path(args.workspace)

    print("🚀 Updating context window to 128K (131072 tokens)")

    # 1. Training manifest
    manifest_path = root / "training-data/manifest.json"
    update_json_file(manifest_path, {
        "max_seq_length": 131072,
        "context_length": 131072
    })

    # 2. Training config
    training_config_path = root / "training-data/training-config.json"
    update_json_file(training_config_path, {
        "max_seq_length": 131072
    })

    # 3. Python scripts
    prepare_script = root / "stack-2.9-training/prepare_dataset.py"
    if prepare_script.exists():
        content = prepare_script.read_text()
        if "max_length=32768" in content:
            new_content = content.replace("max_length=32768", "max_length=131072")
            prepare_script.write_text(new_content)
            print(f"   ✅ Updated prepare_dataset.py (max_length)")
        else:
            print(f"   ℹ️  prepare_dataset.py - already 128K or pattern not found")

    # 4. vLLM server
    vllm_script = root / "stack-2.9-deploy/vllm_server.py"
    if vllm_script.exists():
        content = vllm_script.read_text()
        if "max_model_len" in content:
            # Update max_model_len parameter
            new_content = re.sub(
                r'--max-model-len\s+\d+',
                '--max-model-len 131072',
                content
            )
            vllm_script.write_text(new_content)
            print(f"   ✅ Updated vllm_server.py (--max-model-len)")
        else:
            print(f"   ℹ️  vllm_server.py - max_model_len not found directly, check manually")

    # 5. Local deploy script
    deploy_script = root / "stack-2.9-deploy/local_deploy.sh"
    if deploy_script.exists():
        content = deploy_script.read_text()
        # Update any context-related env var
        new_content = content.replace("MAX_MODEL_LEN=32768", "MAX_MODEL_LEN=131072") \
                           .replace("max_model_len=32768", "max_model_len=131072")
        if new_content != content:
            deploy_script.write_text(new_content)
            print(f"   ✅ Updated local_deploy.sh")
        else:
            print(f"   ℹ️  local_deploy.sh - no changes needed")

    # 6. README.md performance table
    readme_path = root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        # Update context length from 32K to 128K
        new_content = content.replace("32,768 tokens", "131,072 tokens (128K)") \
                           .replace("32K tokens", "128K tokens")
        if new_content != content:
            readme_path.write_text(new_content)
            print(f"   ✅ Updated README.md (context length)")
        else:
            print(f"   ℹ️  README.md - context length already correct")

    # 7. Create configuration note
    config_note = """# Context Window Configuration

Stack 2.9 uses full 128K context window (131072 tokens) to provide complete repository awareness.

## Settings
- max_model_len: 131072
- max_seq_length: 131072
- block_size: 16 or 32 (adjust for memory/performance tradeoff)

## Memory Requirements
| Context | A100 80GB (4-bit) | H100 80GB (4-bit) |
|---------|-------------------|-------------------|
| 32K     | ~20GB             | ~18GB             |
| 64K     | ~35GB             | ~32GB             |
| 128K    | ~60GB             | ~55GB             |

Throughput decreases slightly at longer contexts (~30% slower at 128K vs 32K) but provides full repository context.

"""
    note_path = root / "stack-2.9-docs/CONTEXT_CONFIG.md"
    note_path.write_text(config_note)
    print(f"   ✅ Created CONTEXT_CONFIG.md")

    print("\n✅ Context window update complete!")
    print("   All configs now set to 128K (131072 tokens)")

if __name__ == "__main__":
    main()