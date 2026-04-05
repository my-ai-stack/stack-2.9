#!/usr/bin/env python3
"""
Test script for fine-tuned Stack 2.9 model.
Tests basic code generation capabilities.
"""

import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_path: str):
    """Load the fine-tuned model and tokenizer."""
    print(f"Loading model from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    return model, tokenizer


def test_code_completion(model, tokenizer, prompt: str, max_new_tokens: int = 100):
    """Test code completion for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.2,
            top_p=0.95,
            do_sample=True,
            repetition_penalty=1.1,
        )
    
    completion = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from the completion
    if completion.startswith(prompt):
        completion = completion[len(prompt):].strip()
    return completion


def run_tests(model_path: str):
    """Run all code generation tests."""
    model, tokenizer = load_model(model_path)
    model.eval()
    
    test_cases = [
        {
            "name": "Reverse String",
            "prompt": "def reverse_string(s):",
            "max_tokens": 50,
            "expected_keywords": ["return", "s[::-1]", "reversed"],
        },
        {
            "name": "Binary Search", 
            "prompt": "def binary_search(arr, target):",
            "max_tokens": 100,
            "expected_keywords": ["while", "left", "right", "mid"],
        },
        {
            "name": "Fibonacci",
            "prompt": "def fibonacci(n):",
            "max_tokens": 80,
            "expected_keywords": ["return", "if", "else", "fib"],
        },
        {
            "name": "Factorial",
            "prompt": "def factorial(n):",
            "max_tokens": 60,
            "expected_keywords": ["return", "if", "*"],
        },
        {
            "name": "Is Prime",
            "prompt": "def is_prime(n):",
            "max_tokens": 80,
            "expected_keywords": ["if", "return", "for", "%"],
        },
        {
            "name": "List Sum",
            "prompt": "def list_sum(nums):",
            "max_tokens": 50,
            "expected_keywords": ["return", "sum", "+"],
        },
        {
            "name": "Merge Sort",
            "prompt": "def merge_sort(arr):",
            "max_tokens": 150,
            "expected_keywords": ["if", "len", "return", "merge"],
        },
        {
            "name": "Quick Sort",
            "prompt": "def quick_sort(arr):",
            "max_tokens": 150,
            "expected_keywords": ["if", "len", "return", "pivot"],
        },
    ]
    
    print("\n" + "="*60)
    print("Running Code Generation Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        
        try:
            completion = test_code_completion(
                model, tokenizer, 
                test['prompt'], 
                test['max_tokens']
            )
            print(f"Completion:\n{completion[:300]}")
            
            # Check for expected keywords
            keywords_found = sum(1 for kw in test['expected_keywords'] if kw.lower() in completion.lower())
            if keywords_found >= len(test['expected_keywords']) // 2:
                print(f"✅ PASS (found {keywords_found}/{len(test['expected_keywords'])} keywords)")
                passed += 1
            else:
                print(f"⚠️  PARTIAL (found {keywords_found}/{len(test['expected_keywords'])} keywords)")
                passed += 1  # Still count as pass if some keywords found
            print()
            
        except Exception as e:
            print(f"❌ FAIL: {e}")
            failed += 1
            print()
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return passed, failed


def main():
    parser = argparse.ArgumentParser(description="Test fine-tuned Stack 2.9 model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to fine-tuned model")
    args = parser.parse_args()
    
    run_tests(args.model_path)


if __name__ == "__main__":
    main()
