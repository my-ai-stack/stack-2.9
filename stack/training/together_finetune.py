"""
Together AI Fine-tuning Script for Stack 2.9

Free fine-tuning on Together AI platform.
https://docs.together.ai/docs/fine-tuning
"""

import os
import json
import requests
from typing import Optional

TOGETHER_API = "https://api.together.xyz/v1"

class TogetherFineTuner:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY required")

    def upload_dataset(self, file_path: str) -> str:
        """Upload training data to Together AI"""
        url = f"{TOGETHER_API}/files"

        with open(file_path, 'rb') as f:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": f}
            )

        if response.status_code == 200:
            return response.json()['id']
        raise Exception(f"Upload failed: {response.text}")

    def create_finetune_job(
        self,
        model: str,
        training_file: str,
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 1e-5,
    ) -> dict:
        """
        Create fine-tuning job on Together AI

        Free tier: Up to 7B models, limited training minutes
        """
        url = f"{TOGETHER_API}/fine_tuning/jobs"

        payload = {
            "model": model,  # e.g., "Qwen/Qwen2.5-Coder-7B"
            "training_file": training_file,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "lora": True,  # Enable LoRA for efficiency
            "lora_r": 64,
            "lora_alpha": 128,
        }

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        if response.status_code == 200:
            return response.json()
        raise Exception(f"Job creation failed: {response.text}")

    def get_job_status(self, job_id: str) -> dict:
        """Check fine-tuning job status"""
        url = f"{TOGETHER_API}/fine_tuning/jobs/{job_id}"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        return response.json()

    def list_fine_tuned_models(self) -> list:
        """List your fine-tuned models"""
        url = f"{TOGETHER_API}/fine_tuning/models"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        return response.json().get('models', [])


# Recommended models for free tier
FREE_TIER_MODELS = {
    "7b": "Qwen/Qwen2.5-Coder-7B",
    "3b": "Qwen/Qwen2.5-Coder-3B",
    "1.5b": "Qwen/Qwen2.5-Coder-1.5B",
}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fine-tune on Together AI")
    parser.add_argument("--api-key", type=str, help="Together AI API key")
    parser.add_argument("--model", default="7b", choices=["7b", "3b", "1.5b"],
                        help="Model size")
    parser.add_argument("--data", required=True, help="Training data file (JSONL)")
    parser.add_argument("--epochs", type=int, default=3)

    args = parser.parse_args()

    tuner = TogetherFineTuner(args.api_key)

    # Upload data
    print("Uploading dataset...")
    file_id = tuner.upload_dataset(args.data)
    print(f"Uploaded: {file_id}")

    # Start job
    model_name = FREE_TIER_MODELS[args.model]
    print(f"Starting fine-tune on {model_name}...")

    job = tuner.create_finetune_job(
        model=model_name,
        training_file=file_id,
        epochs=args.epochs,
    )

    print(f"Job created: {job['id']}")
    print(f"Status: {job['status']}")


if __name__ == "__main__":
    main()