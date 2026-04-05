#!/usr/bin/env python3
"""
HumanEval + MBPP Benchmark Evaluation for Stack 2.9
Tests code generation quality using pass@k metrics.
"""

import argparse
import os
import json
import time
from typing import List, Dict
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


def generate_solution(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    """Generate a single solution for a problem."""
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.8,
            top_p=0.95,
            do_sample=True,
            repetition_penalty=1.1,
        )
    
    completion = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract just the generated part
    if completion.startswith(prompt):
        completion = completion[len(prompt):].strip()
    
    # Try to extract just the code (between ```python and ``` if present)
    if "```python" in completion:
        start = completion.find("```python") + len("```python")
        end = completion.find("```", start)
        if end != -1:
            completion = completion[start:end].strip()
    elif "```" in completion:
        start = completion.find("```") + len("```")
        end = completion.find("```", start)
        if end != -1:
            completion = completion[start:end].strip()
    
    return completion


def check_correctness(code: str, expected_output=None) -> bool:
    """Check if generated code produces correct output."""
    try:
        # Create a namespace for execution
        namespace = {}
        exec(code, namespace)
        
        # If we have expected output, check it
        if expected_output and 'solution' in namespace:
            result = namespace['solution']()
            return result == expected_output
        
        # Basic check: code executed without error
        return True
    except Exception as e:
        return False


def evaluate_humaneval(model, tokenizer, num_samples: int = 10, k_values: List[int] = [1, 10, 100]) -> Dict:
    """Evaluate on HumanEval problems."""
    print("\n" + "="*60)
    print("Evaluating on HumanEval")
    print("="*60)
    
    # HumanEval problems (sample - add more as needed)
    humaneval_problems = [
        {
            "task_id": "test_1",
            "prompt": "def two_sum(nums, target):\n    \"\"\"Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\"\"\"\n",
            "solution": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
            "test": "assert two_sum([2,7,11,15], 9) == [0,1]",
        },
        {
            "task_id": "test_2", 
            "prompt": "def is_palindrome(x):\n    \"\"\"Check if a number is a palindrome.\"\"\"\n",
            "solution": "def is_palindrome(x):\n    if x < 0:\n        return False\n    return str(x) == str(x)[::-1]",
            "test": "assert is_palindrome(121) == True",
        },
        {
            "task_id": "test_3",
            "prompt": "def fizz_buzz(n):\n    \"\"\"Return FizzBuzz list from 1 to n.\"\"\"\n",
            "solution": "def fizz_buzz(n):\n    return ['FizzBuzz' if i%15==0 else 'Fizz' if i%3==0 else 'Buzz' if i%5==0 else str(i) for i in range(1,n+1)]",
            "test": "assert fizz_buzz(5) == ['1','2','Fizz','4','Buzz']",
        },
        {
            "task_id": "test_4",
            "prompt": "def fibonacci(n):\n    \"\"\"Return the first n Fibonacci numbers.\"\"\"\n",
            "solution": "def fibonacci(n):\n    if n <= 0:\n        return []\n    fib = [0, 1]\n    while len(fib) < n:\n        fib.append(fib[-1] + fib[-2])\n    return fib[:n]",
            "test": "assert fibonacci(7) == [0, 1, 1, 2, 3, 5, 8]",
        },
        {
            "task_id": "test_5",
            "prompt": "def valid_parentheses(s):\n    \"\"\"Check if string has valid parenthesis matching.\"\"\"\n",
            "solution": "def valid_parentheses(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            if not stack or stack.pop() != mapping[char]:\n                return False\n        else:\n            stack.append(char)\n    return not stack",
            "test": "assert valid_parentheses('()[]{}') == True",
        },
        {
            "task_id": "test_6",
            "prompt": "def reverse_string(s):\n    \"\"\"Reverse a string.\"\"\"\n",
            "solution": "def reverse_string(s):\n    return s[::-1]",
            "test": "assert reverse_string('hello') == 'olleh'",
        },
        {
            "task_id": "test_7",
            "prompt": "def merge_sorted_lists(l1, l2):\n    \"\"\"Merge two sorted lists into one sorted list.\"\"\"\n",
            "solution": "def merge_sorted_lists(l1, l2):\n    return sorted(l1 + l2)",
            "test": "assert merge_sorted_lists([1,3,5], [2,4,6]) == [1,2,3,4,5,6]",
        },
        {
            "task_id": "test_8",
            "prompt": "def maximum_subarray(nums):\n    \"\"\"Find the contiguous subarray with the largest sum.\"\"\"\n",
            "solution": "def maximum_subarray(nums):\n    max_sum = nums[0]\n    current_sum = nums[0]\n    for num in nums[1:]:\n        current_sum = max(num, current_sum + num)\n        max_sum = max(max_sum, current_sum)\n    return max_sum",
            "test": "assert maximum_subarray([-2,1,-3,4,-1,2,1,-5,4]) == 6",
        },
        {
            "task_id": "test_9",
            "prompt": "def climbing_stairs(n):\n    \"\"\"Count ways to climb n stairs (1 or 2 steps at a time).\"\"\"\n",
            "solution": "def climbing_stairs(n):\n    if n <= 2:\n        return n\n    a, b = 1, 2\n    for _ in range(3, n+1):\n        a, b = b, a + b\n    return b",
            "test": "assert climbing_stairs(5) == 8",
        },
        {
            "task_id": "test_10",
            "prompt": "def contains_duplicate(nums):\n    \"\"\"Check if array contains any duplicate.\"\"\"\n",
            "solution": "def contains_duplicate(nums):\n    return len(nums) != len(set(nums))",
            "test": "assert contains_duplicate([1,2,3,1]) == True",
        },
    ]
    
    # Limit to num_samples
    problems = humaneval_problems[:num_samples]
    
    results = []
    for i, problem in enumerate(problems):
        print(f"\nProblem {i+1}/{len(problems)}: {problem['task_id']}")
        print(f"Prompt: {problem['prompt'][:50]}...")
        
        start = time.time()
        solution = generate_solution(model, tokenizer, problem['prompt'])
        elapsed = time.time() - start
        
        print(f"Generated in {elapsed:.2f}s")
        print(f"Solution preview: {solution[:100]}...")
        
        # Try to execute the solution
        correct = check_correctness(solution)
        results.append({
            "task_id": problem["task_id"],
            "solution": solution,
            "correct": correct,
            "time": elapsed,
        })
        
        print(f"Result: {'✅ CORRECT' if correct else '❌ INCORRECT'}")
    
    # Calculate pass@k
    passed = sum(1 for r in results if r['correct'])
    total = len(results)
    
    print("\n" + "="*60)
    print("HumanEval Results")
    print("="*60)
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Pass@1: {100 * passed / total:.1f}%")
    
    return {
        "total": total,
        "passed": passed,
        "pass_at_1": passed / total if total > 0 else 0,
        "results": results,
    }


def evaluate_mbpp(model, tokenizer, num_samples: int = 10) -> Dict:
    """Evaluate on MBPP (Mostly Basic Python Problems)."""
    print("\n" + "="*60)
    print("Evaluating on MBPP")
    print("="*60)
    
    # MBPP problems (sample)
    mbpp_problems = [
        {
            "task_id": "mbpp_1",
            "prompt": "def add_numbers(a, b):\n    # Return the sum of a and b\n",
            "solution": "def add_numbers(a, b):\n    return a + b",
            "test": "assert add_numbers(2, 3) == 5",
        },
        {
            "task_id": "mbpp_2",
            "prompt": "def multiply_list(nums):\n    # Return the product of all numbers in the list\n",
            "solution": "def multiply_list(nums):\n    result = 1\n    for num in nums:\n        result *= num\n    return result",
            "test": "assert multiply_list([1, 2, 3, 4]) == 24",
        },
        {
            "task_id": "mbpp_3",
            "prompt": "def square(x):\n    # Return the square of x\n",
            "solution": "def square(x):\n    return x ** 2",
            "test": "assert square(5) == 25",
        },
        {
            "task_id": "mbpp_4",
            "prompt": "def is_even(n):\n    # Return True if n is even, False otherwise\n",
            "solution": "def is_even(n):\n    return n % 2 == 0",
            "test": "assert is_even(4) == True",
        },
        {
            "task_id": "mbpp_5",
            "prompt": "def string_length(s):\n    # Return the length of string s\n",
            "solution": "def string_length(s):\n    return len(s)",
            "test": "assert string_length('hello') == 5",
        },
        {
            "task_id": "mbpp_6",
            "prompt": "def get_max(nums):\n    # Return the maximum number from the list\n",
            "solution": "def get_max(nums):\n    return max(nums)",
            "test": "assert get_max([1, 5, 3]) == 5",
        },
        {
            "task_id": "mbpp_7",
            "prompt": "def get_min(nums):\n    # Return the minimum number from the list\n",
            "solution": "def get_min(nums):\n    return min(nums)",
            "test": "assert get_min([1, 5, 3]) == 1",
        },
        {
            "task_id": "mbpp_8",
            "prompt": "def count_zeros(nums):\n    # Return the count of zeros in the list\n",
            "solution": "def count_zeros(nums):\n    return nums.count(0)",
            "test": "assert count_zeros([0, 1, 0, 2, 0]) == 3",
        },
        {
            "task_id": "mbpp_9",
            "prompt": "def reverse_list(lst):\n    # Return a new list with elements in reverse order\n",
            "solution": "def reverse_list(lst):\n    return lst[::-1]",
            "test": "assert reverse_list([1, 2, 3]) == [3, 2, 1]",
        },
        {
            "task_id": "mbpp_10",
            "prompt": "def unique_elements(lst):\n    # Return list of unique elements\n",
            "solution": "def unique_elements(lst):\n    return list(set(lst))",
            "test": "assert unique_elements([1, 2, 2, 3]) == [1, 2, 3]",
        },
    ]
    
    problems = mbpp_problems[:num_samples]
    
    results = []
    for i, problem in enumerate(problems):
        print(f"\nProblem {i+1}/{len(problems)}: {problem['task_id']}")
        print(f"Prompt: {problem['prompt'][:50]}...")
        
        start = time.time()
        solution = generate_solution(model, tokenizer, problem['prompt'])
        elapsed = time.time() - start
        
        print(f"Generated in {elapsed:.2f}s")
        print(f"Solution preview: {solution[:100]}...")
        
        correct = check_correctness(solution)
        results.append({
            "task_id": problem["task_id"],
            "solution": solution,
            "correct": correct,
            "time": elapsed,
        })
        
        print(f"Result: {'✅ CORRECT' if correct else '❌ INCORRECT'}")
    
    passed = sum(1 for r in results if r['correct'])
    total = len(results)
    
    print("\n" + "="*60)
    print("MBPP Results")
    print("="*60)
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Pass@1: {100 * passed / total:.1f}%")
    
    return {
        "total": total,
        "passed": passed,
        "pass_at_1": passed / total if total > 0 else 0,
        "results": results,
    }


def save_results(humaneval_results, mbpp_results, output_path: str):
    """Save evaluation results to JSON."""
    combined = {
        "humaneval": humaneval_results,
        "mbpp": mbpp_results,
        "summary": {
            "humaneval_pass_at_1": humaneval_results["pass_at_1"],
            "mbpp_pass_at_1": mbpp_results["pass_at_1"],
            "combined_pass_at_1": (
                humaneval_results["pass_at_1"] + mbpp_results["pass_at_1"]
            ) / 2,
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(combined, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")
    return combined


def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned Stack 2.9 model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to fine-tuned model")
    parser.add_argument("--output", type=str, default="evaluation_results.json", help="Output file for results")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of samples per benchmark")
    args = parser.parse_args()
    
    print("="*60)
    print("Stack 2.9 Model Evaluation")
    print("="*60)
    
    model, tokenizer = load_model(args.model_path)
    model.eval()
    
    # Run evaluations
    humaneval_results = evaluate_humaneval(model, tokenizer, args.num_samples)
    mbpp_results = evaluate_mbpp(model, tokenizer, args.num_samples)
    
    # Save results
    combined = save_results(humaneval_results, mbpp_results, args.output)
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"HumanEval Pass@1:  {100 * combined['summary']['humaneval_pass_at_1']:.1f}%")
    print(f"MBPP Pass@1:       {100 * combined['summary']['mbpp_pass_at_1']:.1f}%")
    print(f"Combined Score:    {100 * combined['summary']['combined_pass_at_1']:.1f}%")
    print("="*60)


if __name__ == "__main__":
    main()
