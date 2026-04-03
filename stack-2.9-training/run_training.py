#!/usr/bin/env python3
"""
Stack 2.9 Training Pipeline
Complete end-to-end training pipeline: prepare data → train → merge → verify.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List
import argparse
import yaml


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def run_command(cmd: List[str], cwd: Optional[str] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=False  # Show output in real-time
    )
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def check_dataset_exists(config: dict) -> bool:
    """Check if pre-processed dataset exists."""
    data_config = config.get("data", {})
    train_dir = data_config.get("train_dir")
    eval_dir = data_config.get("eval_dir")

    if train_dir and eval_dir:
        train_path = Path(train_dir)
        eval_path = Path(eval_dir)
        # Check for Arrow files
        if train_path.exists() and (train_path / "dataset_info.json").exists():
            if eval_path.exists() and (eval_path / "dataset_info.json").exists():
                return True
    return False


def check_model_available(model_name: str) -> bool:
    """Check if base model is available locally or can be downloaded."""
    # Check if model is cached
    model_cache = Path.home() / ".cache" / "huggingface" / "hub"
    if model_cache.exists():
        # Try to find model in cache
        for cached in model_cache.glob(f"models--{model_name.replace('/', '--')}*"):
            return True

    print(f"Note: Model {model_name} will be downloaded if not cached")
    return False


def prepare_data(config: dict) -> None:
    """Prepare training data."""
    print_header("Step 1: Preparing Dataset")

    data_config = config.get("data", {})
    model_config = config.get("model", {})

    train_files = data_config.get("train_files", [])
    val_file = data_config.get("val_file")
    output_dir = data_config.get("train_dir", "/Users/walidsobhi/.openclaw/workspace/stack-2.9-training/data")
    model_name = model_config.get("name", "Qwen/Qwen2.5-Coder-32B")
    max_length = data_config.get("max_length", 4096)

    # Build command
    cmd = [
        sys.executable,
        "prepare_dataset.py",
        "--output", output_dir,
        "--model", model_name,
        "--max-length", str(max_length),
    ]

    for f in train_files:
        cmd.extend(["--input", f])

    if val_file:
        cmd.extend(["--val-file", val_file])

    # Run
    workspace = Path(__file__).parent
    run_command(cmd, cwd=str(workspace))


def train_model(config: dict, resume_from: Optional[str] = None) -> None:
    """Run LoRA training."""
    print_header("Step 2: Training LoRA")

    workspace = Path(__file__).parent

    # Build command
    cmd = [
        sys.executable,
        "train_lora.py",
        "--config", "train_config.yaml"
    ]

    if resume_from:
        cmd.extend(["--resume", resume_from])

    run_command(cmd, cwd=str(workspace))


def merge_model(config: dict) -> None:
    """Merge LoRA adapter with base model."""
    print_header("Step 3: Merging LoRA Adapter")

    output_config = config.get("output", {})
    merge_config = config.get("merge", {})

    lora_dir = output_config.get("lora_dir")
    merged_dir = merge_config.get("output_dir", output_config.get("merged_dir"))

    if not lora_dir:
        print("❌ No LoRA directory specified in config")
        return

    if not merged_dir:
        print("❌ No merged output directory specified in config")
        return

    # Check if LoRA checkpoint exists
    lora_path = Path(lora_dir)
    if not lora_path.exists():
        print(f"❌ LoRA directory not found: {lora_dir}")
        return

    # Use merge_adapter.py if it exists
    workspace = Path(__file__).parent
    merge_script = workspace / "merge_adapter.py"

    if merge_script.exists():
        # Read and update merge script paths
        with open(merge_script, 'r') as f:
            content = f.read()

        # Update paths in the script
        content = content.replace(
            '"/output/lora"',
            f'"{lora_dir}"'
        )
        content = content.replace(
            '"/output/merged"',
            f'"{merged_dir}"'
        )

        # Write to temp file and run
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            run_command([sys.executable, tmp_path])
        finally:
            os.unlink(tmp_path)
    else:
        print(f"Note: No merge script found at {merge_script}")
        print(f"   To merge manually, run:")
        print(f"   python -c \"from peft import PeftModel; from transformers import AutoModelForCausalLM; "
              f"m = AutoModelForCausalLM.from_pretrained('{config['model']['name']}'); "
              f"p = PeftModel.from_pretrained(m, '{lora_dir}'); p.merge_and_unload().save_pretrained('{merged_dir}')\"")


def verify_model(config: dict) -> None:
    """Verify the trained model works."""
    print_header("Step 4: Verifying Model")

    output_config = config.get("output", {})
    model_config = config.get("model", {})

    # Try merged model first, then LoRA
    merged_dir = output_config.get("merged_dir")
    lora_dir = output_config.get("lora_dir")

    model_path = merged_dir or lora_dir

    if not model_path:
        print("❌ No model output directory found")
        return

    if not Path(model_path).exists():
        print(f"❌ Model directory not found: {model_path}")
        return

    print(f"✅ Model saved to: {model_path}")

    # Quick test - try loading the model
    print("\n🔍 Testing model loading...")
    test_code = f"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "{model_path}"
model_name = "{model_config.get('name', 'Qwen/Qwen2.5-Coder-32B')}"

try:
    # Try loading merged model
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    print(f"✅ Model loaded successfully!")
    print(f"   Parameters: {{model.num_parameters():,}}")
except Exception as e:
    print(f"⚠️  Could not load merged model: {{e}}")
    print("   This is normal if using LoRA adapter - use with PeftModel to load")
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def load_config(config_path: str) -> dict:
    """Load training configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 Training Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="train_config.yaml",
        help="Path to training config file"
    )
    parser.add_argument(
        "--skip-data-prep",
        action="store_true",
        help="Skip dataset preparation (use existing prepared data)"
    )
    parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Skip LoRA merging step"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip model verification"
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Resume training from checkpoint"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=["prepare", "train", "merge", "verify", "all"],
        default=["all"],
        help="Which steps to run"
    )

    args = parser.parse_args()

    # Load config
    workspace = Path(__file__).parent
    config_path = workspace / args.config

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))

    print_header("Stack 2.9 Training Pipeline")
    print(f"Config: {config_path}")
    print(f"Model: {config.get('model', {}).get('name', 'Unknown')}")

    # Determine steps to run
    steps = args.steps
    if "all" in steps:
        steps = ["prepare", "train", "merge", "verify"]

    # Run steps
    try:
        if "prepare" in steps:
            if args.skip_data_prep:
                print("\n⏭️  Skipping data preparation (--skip-data-prep)")
            else:
                if check_dataset_exists(config):
                    print("\n⏭️  Skipping data preparation (datasets already exist)")
                    response = input("Re-prepare? [y/N]: ")
                    if response.lower() != 'y':
                        pass
                    else:
                        prepare_data(config)
                else:
                    prepare_data(config)

        if "train" in steps:
            train_model(config, args.resume)

        if "merge" in steps:
            if args.skip_merge:
                print("\n⏭️  Skipping merge (--skip-merge)")
            elif config.get("merge", {}).get("enabled", True):
                merge_model(config)
            else:
                print("\n⏭️  Skipping merge (disabled in config)")

        if "verify" in steps:
            if args.skip_verify:
                print("\n⏭️  Skipping verification (--skip-verify)")
            else:
                verify_model(config)

        print_header("Pipeline Complete!")
        print("🎉 Training pipeline finished successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()