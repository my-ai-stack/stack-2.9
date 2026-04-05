#!/usr/bin/env python3
"""
HumanEval + MBPP Benchmark Evaluation for Stack 2.9
Tests code generation quality using pass@k metrics.

Usage:
    python evaluate_model.py --model-path /path/to/merged/model --num-samples 10
    python evaluate_model.py --model-path /path/to/merged/model --output results.json
"""

import argparse
import os
import json
import time
import traceback
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import itertools
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_path: str, max_memory: Optional[Dict] = None):
    """Load the fine-tuned model and tokenizer."""
    print(f"Loading model from: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    kwargs = {
        "torch_dtype": torch.float16,
        "device_map": "auto",
        "low_cpu_mem_usage": True,
        "trust_remote_code": True,
    }
    
    if max_memory:
        kwargs["max_memory"] = max_memory
    
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    return model, tokenizer


def generate_solution(
    model, 
    tokenizer, 
    prompt: str, 
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 0.95,
    num_return_sequences: int = 1
) -> List[str]:
    """Generate solutions for a prompt.
    
    Returns a list of generated completions.
    """
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        repetition_penalty=1.1,
        num_return_sequences=num_return_sequences,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    
    completions = []
    for output in outputs:
        text = tokenizer.decode(output, skip_special_tokens=True)
        # Remove the prompt from the completion
        if text.startswith(prompt):
            text = text[len(prompt):]
        completions.append(text.strip())
    
    return completions


def extract_code(completion: str) -> str:
    """Extract code from completion, handling markdown code blocks."""
    # Try to extract from ```python blocks
    if "```python" in completion:
        start = completion.find("```python") + len("```python")
        end = completion.find("```", start)
        if end != -1:
            return completion[start:end].strip()
    
    # Try ``` blocks (generic)
    if "```" in completion:
        start = completion.find("```") + len("```")
        end = completion.find("```", start)
        if end != -1:
            return completion[start:end].strip()
    
    # If no code blocks, return as-is but clean up
    return completion.strip()


def execute_code(code: str, timeout: int = 5) -> Tuple[bool, str, Optional[any]]:
    """Safely execute code and return (success, error_msg, result).
    
    Uses restricted builtins and timeout for safety.
    """
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Execution timed out")
    
    # Restricted globals for safe execution
    safe_builtins = {
        'print': print,
        'len': len,
        'range': range,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'any': any,
        'all': all,
        'isinstance': isinstance,
        'type': type,
        'round': round,
        'pow': pow,
        'divmod': divmod,
        'ord': ord,
        'chr': chr,
        'hex': hex,
        'bin': bin,
        'id': id,
    }
    
    namespace = {
        '__builtins__': safe_builtins,
    }
    
    try:
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        exec(code, namespace)
        
        # Cancel alarm
        signal.alarm(0)
        
        return True, "", namespace.get('result')
    
    except TimeoutError as e:
        signal.alarm(0)
        return False, f"Timeout after {timeout}s", None
    except SyntaxError as e:
        signal.alarm(0)
        return False, f"Syntax error: {e}", None
    except Exception as e:
        signal.alarm(0)
        return False, f"{type(e).__name__}: {e}", None


def check_correctness(code: str, test_cases: List[Dict]) -> Tuple[bool, str]:
    """Check if generated code passes test cases.
    
    Args:
        code: The generated code to test
        test_cases: List of dicts with 'input' and 'expected' keys
        
    Returns:
        Tuple of (all_passed, failure_message)
    """
    import types
    
    # Create a new namespace for execution
    namespace = {}
    safe_builtins = {
        'print': print,
        'len': len,
        'range': range,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'any': any,
        'all': all,
        'isinstance': isinstance,
        'type': type,
        'round': round,
        'pow': pow,
    }
    namespace['__builtins__'] = safe_builtins
    
    try:
        exec(code, namespace)
    except Exception as e:
        return False, f"Execution failed: {type(e).__name__}: {e}"
    
    for tc in test_cases:
        func_name = tc.get('function', 'solution')
        inputs = tc.get('input', ())
        expected = tc.get('expected')
        description = tc.get('description', '')
        
        if func_name not in namespace:
            return False, f"Function '{func_name}' not found in code"
        
        func = namespace[func_name]
        
        try:
            if isinstance(inputs, tuple):
                result = func(*inputs)
            else:
                result = func(inputs)
        except Exception as e:
            return False, f"Failed on {description or str(inputs)}: {type(e).__name__}: {e}"
        
        if result != expected:
            return False, f"Failed on {description or str(inputs)}: expected {expected}, got {result}"
    
    return True, ""


def calculate_pass_at_k(num_correct: int, num_samples: int, k: int) -> float:
    """Calculate pass@k metric.
    
    Uses the estimator: 1 - C(n-c+k-1, k) / C(n+k-1, k)
    where n = num_samples, c = num_correct, k = k
    
    For small samples, this is more accurate than simple c/n.
    """
    import math
    
    if num_samples < k:
        return 0.0
    
    if num_samples == 0:
        return 0.0
    
    # Bootstrap-style calculation
    # "At least one of k samples is correct" probability
    try:
        # Exact formula: 1 - (C(n-c, k) / C(n, k))
        # But we use the complementary for numerical stability
        correct = num_correct
        n = num_samples
        fail = n - correct
        
        if fail >= k:
            return 0.0
        
        # Calculate probability that at least one succeeds
        # P(at least 1 success) = 1 - P(all k fail)
        # P(all k fail) = C(fail, k) / C(n, k)
        
        numerator = 1.0
        denominator = 1.0
        
        for i in range(k):
            numerator *= (fail - i)
            denominator *= (n - i)
        
        p_all_fail = numerator / denominator
        p_at_least_1_success = 1 - p_all_fail
        
        return p_at_least_1_success
    except:
        # Fallback to simple ratio
        return num_correct / num_samples


def evaluate_problems(
    model, 
    tokenizer, 
    problems: List[Dict],
    k_values: List[int] = [1, 10],
    num_samples_per_problem: int = 10,
    max_new_tokens: int = 256,
) -> Dict:
    """Evaluate model on a set of problems with pass@k metrics.
    
    Args:
        model: The language model
        tokenizer: The tokenizer
        problems: List of problem dicts with 'task_id', 'prompt', 'test_cases'
        k_values: List of k values for pass@k calculation
        num_samples_per_problem: Number of samples to generate per problem
        max_new_tokens: Max tokens to generate
        
    Returns:
        Dictionary with evaluation results
    """
    all_results = []
    total_correct_per_k = {k: 0 for k in k_values}
    total_problems = len(problems)
    
    for idx, problem in enumerate(problems):
        task_id = problem['task_id']
        prompt = problem['prompt']
        test_cases = problem.get('test_cases', [])
        
        print(f"\n[{idx+1}/{total_problems}] Processing: {task_id}")
        
        # Generate multiple samples
        start_time = time.time()
        completions = generate_solution(
            model, tokenizer, prompt,
            max_new_tokens=max_new_tokens,
            num_return_sequences=num_samples_per_problem
        )
        elapsed = time.time() - start_time
        
        print(f"  Generated {len(completions)} samples in {elapsed:.2f}s")
        
        # Check each completion
        correct_flags = []
        for i, completion in enumerate(completions):
            code = extract_code(completion)
            
            # For pass@10, we consider the completion correct if it passes tests
            # For pass@1, we only consider the first sample
            passed, msg = check_correctness(code, test_cases)
            correct_flags.append(passed)
            
            if i == 0:  # Show first result detail
                print(f"  Sample 1: {'✅' if passed else '❌'} {msg[:60] if msg else 'OK'}")
        
        # Calculate pass@k for this problem
        num_correct = sum(correct_flags)
        
        problem_results = {
            "task_id": task_id,
            "prompt": prompt,
            "num_samples": len(completions),
            "num_correct": num_correct,
            "pass@k": {},
        }
        
        for k in k_values:
            if k <= num_samples_per_problem:
                # How many of the first k samples are correct?
                correct_in_k = sum(correct_flags[:min(k, len(correct_flags))])
                if k == 1:
                    # pass@1 = whether first sample is correct
                    pass_at_k = 1.0 if correct_flags[0] else 0.0
                else:
                    # pass@k = probability that at least one of k is correct
                    pass_at_k = calculate_pass_at_k(correct_in_k, k, k)
                
                problem_results["pass@k"][f"pass@{k}"] = pass_at_k
                total_correct_per_k[k] += correct_in_k
        
        all_results.append(problem_results)
        
        # Progress update
        if k_values[0] == 1:
            current_pass1 = total_correct_per_k.get(1, 0) / (idx + 1)
            print(f"  Running Pass@1: {100*current_pass1:.1f}%")
    
    # Aggregate results
    summary = {
        "total_problems": total_problems,
        "total_samples_per_problem": num_samples_per_problem,
    }
    
    for k in k_values:
        if k <= num_samples_per_problem:
            # Overall pass@k
            total_correct_for_k = 0
            total_possible_for_k = 0
            
            for r in all_results:
                if f"pass@{k}" in r["pass@k"]:
                    # For pass@1, it's binary
                    if k == 1:
                        total_correct_for_k += r["num_correct"] > 0
                    else:
                        # For pass@10, count how many problems have at least 1 correct in first k
                        correct_in_k = sum(correct_flags[:min(k, len(correct_flags))])
                        total_correct_for_k += 1 if correct_in_k > 0 else 0
                    total_possible_for_k += 1
            
            summary[f"pass@{k}"] = total_correct_for_k / total_possible_for_k if total_possible_for_k > 0 else 0
            summary[f"pass@{k}_exact"] = total_correct_for_k
            summary[f"total@{k}"] = total_possible_for_k
    
    return {
        "summary": summary,
        "details": all_results,
    }


def get_humaneval_problems() -> List[Dict]:
    """Return HumanEval benchmark problems."""
    return [
        {
            "task_id": "humaneval/1",
            "prompt": '''def two_sum(nums, target):
    """Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
    You may assume that each input would have exactly one solution, and you may not use the same element twice.
    """''',
            "test_cases": [
                {"function": "two_sum", "input": ([2,7,11,15], 9), "expected": [0,1], "description": "Basic case"},
                {"function": "two_sum", "input": ([3,2,4], 6), "expected": [1,2], "description": "Middle elements"},
                {"function": "two_sum", "input": ([3,3], 6), "expected": [0,1], "description": "Duplicate values"},
            ],
        },
        {
            "task_id": "humaneval/2",
            "prompt": '''def is_palindrome(x):
    """Check if an integer is a palindrome. An integer is a palindrome when it reads the same backward as forward."''',
            "test_cases": [
                {"function": "is_palindrome", "input": 121, "expected": True, "description": "Positive palindrome"},
                {"function": "is_palindrome", "input": -121, "expected": False, "description": "Negative number"},
                {"function": "is_palindrome", "input": 10, "expected": False, "description": "Ends with 0"},
            ],
        },
        {
            "task_id": "humaneval/3",
            "prompt": '''def fizz_buzz(n):
    """Given number n, return a list of strings from 1 to n. For multiples of 3 add 'Fizz', for multiples of 5 add 'Buzz', for both add 'FizzBuzz'."''',
            "test_cases": [
                {"function": "fizz_buzz", "input": 3, "expected": ["1", "2", "Fizz"], "description": "n=3"},
                {"function": "fizz_buzz", "input": 5, "expected": ["1", "2", "Fizz", "4", "Buzz"], "description": "n=5"},
                {"function": "fizz_buzz", "input": 15, "expected": ["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"], "description": "n=15"},
            ],
        },
        {
            "task_id": "humaneval/4",
            "prompt": '''def fibonacci(n):
    """Return the first n Fibonacci numbers starting from 0 and 1. So fibonacci(7) returns [0, 1, 1, 2, 3, 5, 8]."''',
            "test_cases": [
                {"function": "fibonacci", "input": 1, "expected": [0], "description": "n=1"},
                {"function": "fibonacci", "input": 7, "expected": [0, 1, 1, 2, 3, 5, 8], "description": "n=7"},
                {"function": "fibonacci", "input": 10, "expected": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34], "description": "n=10"},
            ],
        },
        {
            "task_id": "humaneval/5",
            "prompt": '''def valid_parentheses(s):
    """Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. An input string is valid if: Open brackets must be closed by the same type of brackets, and Open brackets must be closed in the correct order."''',
            "test_cases": [
                {"function": "valid_parentheses", "input": "()", "expected": True, "description": "Simple pair"},
                {"function": "valid_parentheses", "input": "()[]{}", "expected": True, "description": "Multiple types"},
                {"function": "valid_parentheses", "input": "(]", "expected": False, "description": "Mismatched"},
                {"function": "valid_parentheses", "input": "([)]", "expected": False, "description": "Wrong order"},
            ],
        },
        {
            "task_id": "humaneval/6",
            "prompt": '''def reverse_string(s):
    """Return the reverse of string s."''',
            "test_cases": [
                {"function": "reverse_string", "input": "hello", "expected": "olleh", "description": "Basic"},
                {"function": "reverse_string", "input": "Hannah", "expected": "hannaH", "description": "Palindrome name"},
            ],
        },
        {
            "task_id": "humaneval/7",
            "prompt": '''def merge_sorted_lists(l1, l2):
    """Merge two sorted lists into one sorted list."''',
            "test_cases": [
                {"function": "merge_sorted_lists", "input": ([1,3,5], [2,4,6]), "expected": [1,2,3,4,5,6], "description": "Interleaved"},
                {"function": "merge_sorted_lists", "input": ([1,2,3], [4,5,6]), "expected": [1,2,3,4,5,6], "description": "Sequential"},
            ],
        },
        {
            "task_id": "humaneval/8",
            "prompt": '''def maximum_subarray(nums):
    """Find the contiguous subarray which has the largest sum and return its sum."''',
            "test_cases": [
                {"function": "maximum_subarray", "input": [-2,1,-3,4,-1,2,1,-5,4], "expected": 6, "description": "Mixed"},
                {"function": "maximum_subarray", "input": [1], "expected": 1, "description": "Single element"},
                {"function": "maximum_subarray", "input": [5,4,-1,7,8], "expected": 23, "description": "Mostly positive"},
            ],
        },
        {
            "task_id": "humaneval/9",
            "prompt": '''def climbing_stairs(n):
    """You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?"''',
            "test_cases": [
                {"function": "climbing_stairs", "input": 2, "expected": 2, "description": "n=2"},
                {"function": "climbing_stairs", "input": 3, "expected": 3, "description": "n=3"},
                {"function": "climbing_stairs", "input": 5, "expected": 8, "description": "n=5"},
            ],
        },
        {
            "task_id": "humaneval/10",
            "prompt": '''def contains_duplicate(nums):
    """Given an integer array nums, return True if any value appears at least twice in the array, and False if every element is distinct."''',
            "test_cases": [
                {"function": "contains_duplicate", "input": [1,2,3,1], "expected": True, "description": "Has duplicate"},
                {"function": "contains_duplicate", "input": [1,2,3,4], "expected": False, "description": "All unique"},
            ],
        },
        {
            "task_id": "humaneval/11",
            "prompt": '''def roman_to_int(s):
    """Convert a Roman numeral to an integer."''',
            "test_cases": [
                {"function": "roman_to_int", "input": "III", "expected": 3, "description": "Simple"},
                {"function": "roman_to_int", "input": "IV", "expected": 4, "description": "Subtractive"},
                {"function": "roman_to_int", "input": "MCMXCIV", "expected": 1994, "description": "Complex"},
            ],
        },
        {
            "task_id": "humaneval/12",
            "prompt": '''def longest_common_prefix(strs):
    """Write a function to find the longest common prefix string amongst an array of strings."''',
            "test_cases": [
                {"function": "longest_common_prefix", "input": ["flower","flow","flight"], "expected": "fl", "description": "Basic"},
                {"function": "longest_common_prefix", "input": ["dog","racecar","car"], "expected": "", "description": "No prefix"},
            ],
        },
    ]


def get_mbpp_problems() -> List[Dict]:
    """Return MBPP (Mostly Basic Python Problems) benchmark problems."""
    return [
        {
            "task_id": "mbpp/1",
            "prompt": '''def add_numbers(a, b):
    # Return the sum of a and b
    pass''',
            "test_cases": [
                {"function": "add_numbers", "input": (2, 3), "expected": 5, "description": "Basic add"},
                {"function": "add_numbers", "input": (-1, 1), "expected": 0, "description": "Opposite signs"},
            ],
        },
        {
            "task_id": "mbpp/2",
            "prompt": '''def multiply_list(nums):
    # Return the product of all numbers in the list
    pass''',
            "test_cases": [
                {"function": "multiply_list", "input": ([1, 2, 3, 4],), "expected": 24, "description": "Basic"},
                {"function": "multiply_list", "input": ([5,],), "expected": 5, "description": "Single element"},
                {"function": "multiply_list", "input": ([],), "expected": 1, "description": "Empty (identity)"},
            ],
        },
        {
            "task_id": "mbpp/3",
            "prompt": '''def square(x):
    # Return the square of x
    pass''',
            "test_cases": [
                {"function": "square", "input": (5,), "expected": 25, "description": "Basic"},
                {"function": "square", "input": (-3,), "expected": 9, "description": "Negative"},
                {"function": "square", "input": (0,), "expected": 0, "description": "Zero"},
            ],
        },
        {
            "task_id": "mbpp/4",
            "prompt": '''def is_even(n):
    # Return True if n is even, False otherwise
    pass''',
            "test_cases": [
                {"function": "is_even", "input": (4,), "expected": True, "description": "Even number"},
                {"function": "is_even", "input": (7,), "expected": False, "description": "Odd number"},
                {"function": "is_even", "input": (0,), "expected": True, "description": "Zero is even"},
            ],
        },
        {
            "task_id": "mbpp/5",
            "prompt": '''def string_length(s):
    # Return the length of string s
    pass''',
            "test_cases": [
                {"function": "string_length", "input": ("hello",), "expected": 5, "description": "Basic"},
                {"function": "string_length", "input": ("",), "expected": 0, "description": "Empty string"},
            ],
        },
        {
            "task_id": "mbpp/6",
            "prompt": '''def get_max(nums):
    # Return the maximum number from the list
    pass''',
            "test_cases": [
                {"function": "get_max", "input": ([1, 5, 3],), "expected": 5, "description": "Basic"},
                {"function": "get_max", "input": ([-1, -5, -3],), "expected": -1, "description": "Negative numbers"},
            ],
        },
        {
            "task_id": "mbpp/7",
            "prompt": '''def get_min(nums):
    # Return the minimum number from the list
    pass''',
            "test_cases": [
                {"function": "get_min", "input": ([1, 5, 3],), "expected": 1, "description": "Basic"},
                {"function": "get_min", "input": ([-1, -5, -3],), "expected": -5, "description": "Negative numbers"},
            ],
        },
        {
            "task_id": "mbpp/8",
            "prompt": '''def count_zeros(nums):
    # Return the count of zeros in the list
    pass''',
            "test_cases": [
                {"function": "count_zeros", "input": ([0, 1, 0, 2, 0],), "expected": 3, "description": "Mixed"},
                {"function": "count_zeros", "input": ([1, 2, 3],), "expected": 0, "description": "No zeros"},
            ],
        },
        {
            "task_id": "mbpp/9",
            "prompt": '''def reverse_list(lst):
    # Return a new list with elements in reverse order
    pass''',
            "test_cases": [
                {"function": "reverse_list", "input": ([1, 2, 3],), "expected": [3, 2, 1], "description": "Basic"},
                {"function": "reverse_list", "input": ([],), "expected": [], "description": "Empty"},
            ],
        },
        {
            "task_id": "mbpp/10",
            "prompt": '''def unique_elements(lst):
    # Return list of unique elements (preserving order)
    pass''',
            "test_cases": [
                {"function": "unique_elements", "input": ([1, 2, 2, 3],), "expected": [1, 2, 3], "description": "With duplicates"},
                {"function": "unique_elements", "input": ([1, 2, 3],), "expected": [1, 2, 3], "description": "All unique"},
            ],
        },
        {
            "task_id": "mbpp/11",
            "prompt": '''def factorial(n):
    # Return n! (factorial of n)
    pass''',
            "test_cases": [
                {"function": "factorial", "input": (5,), "expected": 120, "description": "Basic"},
                {"function": "factorial", "input": (0,), "expected": 1, "description": "Zero factorial"},
                {"function": "factorial", "input": (1,), "expected": 1, "description": "One factorial"},
            ],
        },
        {
            "task_id": "mbpp/12",
            "prompt": '''def is_prime(n):
    # Return True if n is prime, False otherwise
    pass''',
            "test_cases": [
                {"function": "is_prime", "input": (7,), "expected": True, "description": "Prime"},
                {"function": "is_prime", "input": (4,), "expected": False, "description": "Not prime"},
                {"function": "is_prime", "input": (1,), "expected": False, "description": "One is not prime"},
            ],
        },
    ]


def save_results(results: Dict, output_path: str):
    """Save evaluation results to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_path}")


def print_summary(results: Dict, benchmark_name: str):
    """Print a summary of evaluation results."""
    print(f"\n{'='*60}")
    print(f"{benchmark_name} Results")
    print('='*60)
    
    summary = results.get("summary", {})
    total = summary.get("total_problems", 0)
    
    for key, value in summary.items():
        if key.startswith("pass@"):
            print(f"  {key}: {100*value:.2f}%")
        elif key.endswith("_exact") or key.endswith("_total") or key == "total_problems" or key == "total_samples_per_problem":
            print(f"  {key}: {value}")
    
    print(f"\n  Total problems evaluated: {total}")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Stack 2.9 model on HumanEval and MBPP benchmarks"
    )
    parser.add_argument(
        "--model-path", 
        type=str, 
        required=True, 
        help="Path to the merged model directory"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="evaluation_results.json", 
        help="Output file for results (default: evaluation_results.json)"
    )
    parser.add_argument(
        "--num-samples", 
        type=int, 
        default=10, 
        help="Number of samples per problem for pass@k (default: 10)"
    )
    parser.add_argument(
        "--max-new-tokens", 
        type=int, 
        default=256, 
        help="Maximum new tokens to generate (default: 256)"
    )
    parser.add_argument(
        "--k-values", 
        type=str, 
        default="1,10", 
        help="Comma-separated k values for pass@k (default: 1,10)"
    )
    parser.add_argument(
        "--benchmark", 
        type=str, 
        choices=["humaneval", "mbpp", "both"], 
        default="both", 
        help="Which benchmark to run (default: both)"
    )
    parser.add_argument(
        "--num-problems", 
        type=int, 
        default=None, 
        help="Limit number of problems per benchmark (default: all)"
    )
    
    args = parser.parse_args()
    
    # Parse k values
    k_values = [int(k.strip()) for k in args.k_values.split(",")]
    
    print("="*60)
    print("Stack 2.9 Model Evaluation")
    print("="*60)
    print(f"Model path: {args.model_path}")
    print(f"Output: {args.output}")
    print(f"Num samples per problem: {args.num_samples}")
    print(f"Pass@k values: {k_values}")
    print(f"Benchmark: {args.benchmark}")
    
    # Load model
    model, tokenizer = load_model(args.model_path)
    model.eval()
    
    all_results = {}
    total_start = time.time()
    
    # Run HumanEval
    if args.benchmark in ["humaneval", "both"]:
        print("\n" + "="*60)
        print("Running HumanEval Benchmark")
        print("="*60)
        
        problems = get_humaneval_problems()
        if args.num_problems:
            problems = problems[:args.num_problems]
        
        results = evaluate_problems(
            model, tokenizer, 
            problems, 
            k_values=k_values,
            num_samples_per_problem=args.num_samples,
            max_new_tokens=args.max_new_tokens,
        )
        all_results["humaneval"] = results
        print_summary(results, "HumanEval")
    
    # Run MBPP
    if args.benchmark in ["mbpp", "both"]:
        print("\n" + "="*60)
        print("Running MBPP Benchmark")
        print("="*60)
        
        problems = get_mbpp_problems()
        if args.num_problems:
            problems = problems[:args.num_problems]
        
        results = evaluate_problems(
            model, tokenizer, 
            problems, 
            k_values=k_values,
            num_samples_per_problem=args.num_samples,
            max_new_tokens=args.max_new_tokens,
        )
        all_results["mbpp"] = results
        print_summary(results, "MBPP")
    
    total_time = time.time() - total_start
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    for bench_name in ["humaneval", "mbpp"]:
        if bench_name in all_results:
            summary = all_results[bench_name]["summary"]
            for k in k_values:
                key = f"pass@{k}"
                if key in summary:
                    print(f"  {bench_name.upper()} {key}: {100*summary[key]:.2f}%")
    
    print(f"\n  Total evaluation time: {total_time:.1f}s")
    print("="*60)
    
    # Add metadata to results
    all_results["metadata"] = {
        "model_path": args.model_path,
        "num_samples": args.num_samples,
        "k_values": k_values,
        "total_time_seconds": total_time,
    }
    
    # Save results
    save_results(all_results, args.output)


if __name__ == "__main__":
    main()
