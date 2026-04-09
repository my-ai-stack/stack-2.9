#!/usr/bin/env python3
"""
Stack 2.9 Local Training Script for Mac (MPS)
Run this on your Mac to train the model locally.
"""

import os
import sys

# Add the training module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stack/training'))

# Set environment for MPS
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

def main():
    print("=" * 60)
    print("Stack 2.9 Local Training (Mac MPS)")
    print("=" * 60)

    # Check MPS availability
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"MPS available: {torch.backends.mps.is_available()}")
        if torch.backends.mps.is_available():
            print(f"MPS built: {torch.backends.mps.is_built()}")
    except Exception as e:
        print(f"⚠️ PyTorch/MPS check error: {e}")

    # Check paths
    base_model = "./base_model_qwen7b"
    data_path = "./data/final/train.jsonl"
    output_dir = "./training_output"
    model_name = "Qwen/Qwen2.5-Coder-7B"

    print(f"\n📁 Checking paths...")
    print(f"   Base model: {base_model} - {'✅ exists' if os.path.exists(base_model) else '❌ not found'}")
    print(f"   Data: {data_path} - {'✅ exists' if os.path.exists(data_path) else '❌ not found'}")

    # Download model if not exists
    if not os.path.exists(base_model):
        print(f"\n⬇️  Downloading model ({model_name})...")
        print("   This takes ~10-15 minutes...")
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        tokenizer.save_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
        model.save_pretrained(base_model)
        print(f"   ✅ Model saved to {base_model}")
    else:
        print(f"   ✅ Model already exists!")

    if not os.path.exists(data_path):
        print("\n❌ Training data not found!")
        print("   Expected: ./data/final/train.jsonl")
        print("   Available data files:")
        for root, dirs, files in os.walk("./data"):
            for f in files:
                if f.endswith(".jsonl"):
                    print(f"   - {os.path.join(root, f)}")
        return

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load and update config
    import yaml

    config_path = "stack/training/train_config_local.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        print(f"⚠️ Config not found at {config_path}, using defaults")
        config = {
            'model': {'name': base_model, 'trust_remote_code': True},
            'data': {'input_path': data_path, 'max_length': 2048},
            'lora': {'r': 16, 'alpha': 32, 'target_modules': ['q_proj', 'k_proj', 'v_proj', 'o_proj']},
            'training': {'num_epochs': 1, 'batch_size': 1, 'learning_rate': 2e-4},
            'output': {'lora_dir': f'{output_dir}/lora', 'merged_dir': f'{output_dir}/merged'},
            'hardware': {'device': 'mps'}
        }

    # Update config with local paths
    config['model']['name'] = base_model
    config['data']['input_path'] = data_path
    config['output']['lora_dir'] = f"{output_dir}/lora"
    config['output']['merged_dir'] = f"{output_dir}/merged"
    config['hardware']['device'] = "mps"

    # Save updated config
    updated_config = f"{output_dir}/train_config.yaml"
    with open(updated_config, 'w') as f:
        yaml.dump(config, f)

    print(f"\n✅ Config saved to: {updated_config}")
    print(f"\n🚀 Starting training...")
    print(f"   Output will be at: {output_dir}/")
    print("=" * 60)

    # Run training
    from train_lora import train_lora
    trainer = train_lora(updated_config)

    print("=" * 60)
    print("✅ TRAINING COMPLETED!")
    print(f"   LoRA adapter: {output_dir}/lora/")
    print(f"   Merged model: {output_dir}/merged/")
    print("=" * 60)


if __name__ == "__main__":
    main()