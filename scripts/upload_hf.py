#!/usr/bin/env python3
"""
HuggingFace Model Uploader for Stack 2.9
Uploads fine-tuned model to HuggingFace Hub with proper model card and tags.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, create_repo, upload_folder
    from huggingface_hub.utils import RepoNotFoundError
except ImportError:
    print("Error: huggingface_hub not installed. Install with: pip install huggingface_hub")
    sys.exit(1)


def load_model_card(template_path: str, placeholders: dict) -> str:
    """Load model card template and replace placeholders."""
    with open(template_path, 'r') as f:
        content = f.read()
    
    for key, value in placeholders.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))
    
    return content


def get_model_files(model_path: str) -> list:
    """Get list of model files to upload."""
    path = Path(model_path)
    if not path.exists():
        print(f"Warning: Model path {model_path} does not exist. Creating empty upload.")
        return []
    
    files = []
    for f in path.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(path)))
    
    return files


def main():
    parser = argparse.ArgumentParser(description="Upload Stack 2.9 model to HuggingFace Hub")
    parser.add_argument("--model", type=str, required=True, 
                        help="Path to the merged model directory")
    parser.add_argument("--repo-id", type=str, required=True,
                        help="HuggingFace repo ID (e.g., username/stack-2.9-7b)")
    parser.add_argument("--token", type=str, default=None,
                        help="HuggingFace token (or set HF_TOKEN env var)")
    parser.add_argument("--private", action="store_true",
                        help="Create private repository")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be uploaded without uploading")
    
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN not set. Set HF_TOKEN environment variable or use --token")
        sys.exit(1)
    
    api = HfApi(token=token)
    
    # Get model card content
    script_dir = Path(__file__).parent
    readme_path = script_dir / "README_HF.md"
    
    if not readme_path.exists():
        print(f"Warning: README_HF.md not found at {readme_path}")
        readme_content = "# Stack 2.9 Model\n\nFine-tuned coding assistant model."
    else:
        # Placeholder values - update these with actual metrics
        placeholders = {
            "base_model": "Qwen2.5-Coder-7B",
            "training_examples": "50,000",
            "lora_rank": "16",
            "lora_alpha": "32",
            "humaneval_score": "TBD",
            "mbpp_score": "TBD",
            "max_context_length": "32K",
        }
        readme_content = load_model_card(str(readme_path), placeholders)
    
    # Create repo if it doesn't exist
    repo_id = args.repo_id
    try:
        create_repo(repo_id, token=token, private=args.private, repo_type="model", exist_ok=True)
        print(f"Repository '{repo_id}' created or already exists.")
    except Exception as e:
        print(f"Error creating repository: {e}")
        sys.exit(1)
    
    # Write model card locally for upload
    model_path = Path(args.model)
    model_card_path = model_path / "README.md"
    
    if model_path.exists():
        with open(model_card_path, 'w') as f:
            f.write(readme_content)
        print(f"Created model card at {model_card_path}")
    
    if args.dry_run:
        print("\n=== DRY RUN - Files that would be uploaded ===")
        files = get_model_files(args.model)
        for f in files[:20]:  # Show first 20
            print(f"  {f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more files")
        print(f"\nTotal: {len(files)} files")
        print(f"\nModel card:\n{readme_content[:500]}...")
        return
    
    # Upload the model
    print(f"\nUploading model from {args.model} to {repo_id}...")
    
    try:
        # Upload entire folder
        operation = api.upload_folder(
            folder_path=args.model,
            repo_id=repo_id,
            repo_type="model",
            commit_message="Upload Stack 2.9 fine-tuned model"
        )
        print(f"\n✅ Successfully uploaded to https://huggingface.co/{repo_id}")
        print(f"Operation: {operation}")
    except Exception as e:
        print(f"Error uploading: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()