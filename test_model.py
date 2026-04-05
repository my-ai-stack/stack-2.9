#!/usr/bin/env python3
"""
Basic Code Generation Tests for Stack 2.9 Model
Tests common algorithms and data structures.

Usage:
    python test_model.py --model-path /path/to/merged/model
    python test_model.py --model-path /path/to/merged/model --output test_results.json
"""

import argparse
import json
import time
from typing import Any, Dict, List, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_path: str):
    """Load the fine-tuned model and tokenizer."""
    print(f"Loading model from: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    
    return model, tokenizer


def generate_completion(
    model, 
    tokenizer, 
    prompt: str, 
    max_new_tokens: int = 128,
    temperature: float = 0.2,
    num_samples: int = 1
) -> List[str]:
    """Generate code completion(s) for a prompt."""
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=0.95,
        do_sample=True,
        repetition_penalty=1.1,
        num_return_sequences=num_samples,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    
    completions = []
    for output in outputs:
        text = tokenizer.decode(output, skip_special_tokens=True)
        if text.startswith(prompt):
            text = text[len(prompt):]
        completions.append(text.strip())
    
    return completions


def extract_code(completion: str) -> str:
    """Extract code from completion, handling markdown code blocks."""
    # Try ```python blocks first
    if "```python" in completion:
        start = completion.find("```python") + len("```python")
        end = completion.find("```", start)
        if end != -1:
            return completion[start:end].strip()
    
    # Try generic ``` blocks
    if "```" in completion:
        start = completion.find("```") + len("```")
        # Skip language identifier if present
        if completion[start:start+10].strip():
            start = completion.find("\n", start) + 1
        end = completion.find("```", start)
        if end != -1:
            return completion[start:end].strip()
    
    return completion.strip()


def execute_code(code: str, timeout: int = 5) -> Tuple[bool, str, Optional[Any]]:
    """Safely execute code and return (success, error_msg, result)."""
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Execution timed out")
    
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
    
    namespace = {'__builtins__': safe_builtins}
    
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        exec(code, namespace)
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


def check_function_output(code: str, func_name: str, test_cases: List[Dict]) -> Tuple[bool, str]:
    """Test a function with given test cases.
    
    Args:
        code: The generated code
        func_name: Name of function to test
        test_cases: List of dicts with 'input' (tuple), 'expected', 'description'
    
    Returns:
        Tuple of (all_passed, failure_message)
    """
    namespace = {'__builtins__': {
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
    }}
    
    try:
        exec(code, namespace)
    except Exception as e:
        return False, f"Code execution failed: {type(e).__name__}: {e}"
    
    if func_name not in namespace:
        return False, f"Function '{func_name}' not found"
    
    func = namespace[func_name]
    
    for tc in test_cases:
        inputs = tc.get('input', ())
        expected = tc.get('expected')
        desc = tc.get('description', str(inputs))
        
        try:
            if isinstance(inputs, tuple):
                result = func(*inputs)
            else:
                result = func(inputs)
        except Exception as e:
            return False, f"Failed on {desc}: {type(e).__name__}: {e}"
        
        if result != expected:
            return False, f"Failed on {desc}: expected {expected}, got {result}"
    
    return True, ""


# Common algorithm test cases
ALGORITHM_TESTS = [
    {
        "name": "Two Sum",
        "prompt": "def two_sum(nums, target):\n    \"\"\"Return indices of two numbers that add up to target.\"\"\"\n",
        "function": "two_sum",
        "max_tokens": 100,
        "test_cases": [
            {"input": ([2,7,11,15], 9), "expected": [0,1], "description": "Basic"},
            {"input": ([3,2,4], 6), "expected": [1,2], "description": "Middle"},
        ],
        "keywords": ["for", "in", "range", "enumerate"],
    },
    {
        "name": "Reverse String",
        "prompt": "def reverse_string(s):\n    \"\"\"Return the reverse of string s.\"\"\"\n",
        "function": "reverse_string",
        "max_tokens": 50,
        "test_cases": [
            {"input": ("hello",), "expected": "olleh", "description": "Basic"},
            {"input": ("Python",), "expected": "nohtyP", "description": "Mixed case"},
        ],
        "keywords": ["[::-1]", "reversed"],
    },
    {
        "name": "Fibonacci",
        "prompt": "def fibonacci(n):\n    \"\"\"Return first n Fibonacci numbers.\"\"\"\n",
        "function": "fibonacci",
        "max_tokens": 100,
        "test_cases": [
            {"input": (7,), "expected": [0,1,1,2,3,5,8], "description": "n=7"},
            {"input": (1,), "expected": [0], "description": "n=1"},
        ],
        "keywords": ["for", "while", "append", "range"],
    },
    {
        "name": "Factorial",
        "prompt": "def factorial(n):\n    \"\"\"Return n! (factorial).\"\"\"\n",
        "function": "factorial",
        "max_tokens": 60,
        "test_cases": [
            {"input": (5,), "expected": 120, "description": "5!"},
            {"input": (0,), "expected": 1, "description": "0!"},
        ],
        "keywords": ["for", "while", "range", "*"],
    },
    {
        "name": "Is Palindrome",
        "prompt": "def is_palindrome(x):\n    \"\"\"Check if integer x is a palindrome.\"\"\"\n",
        "function": "is_palindrome",
        "max_tokens": 60,
        "test_cases": [
            {"input": (121,), "expected": True, "description": "121"},
            {"input": (-121,), "expected": False, "description": "-121"},
        ],
        "keywords": ["str", "[::-1]"],
    },
    {
        "name": "Binary Search",
        "prompt": "def binary_search(arr, target):\n    \"\"\"Return index of target in sorted array, or -1 if not found.\"\"\"\n",
        "function": "binary_search",
        "max_tokens": 120,
        "test_cases": [
            {"input": ([1,2,3,4,5], 3), "expected": 2, "description": "Found"},
            {"input": ([1,2,3,4,5], 6), "expected": -1, "description": "Not found"},
        ],
        "keywords": ["while", "left", "right", "<=", ">"],
    },
    {
        "name": "Merge Sort",
        "prompt": "def merge_sort(arr):\n    \"\"\"Return sorted copy of array using merge sort.\"\"\"\n",
        "function": "merge_sort",
        "max_tokens": 200,
        "test_cases": [
            {"input": ([3,1,4,1,5,9,2,6],), "expected": [1,1,2,3,4,5,6,9], "description": "Mixed"},
            {"input": ([1,2,3],), "expected": [1,2,3], "description": "Already sorted"},
        ],
        "keywords": ["def merge_sort", "if", "len", "return", "merge"],
    },
    {
        "name": "Quick Sort",
        "prompt": "def quick_sort(arr):\n    \"\"\"Return sorted copy of array using quick sort.\"\"\"\n",
        "function": "quick_sort",
        "max_tokens": 200,
        "test_cases": [
            {"input": ([3,1,4,1,5,9,2,6],), "expected": [1,1,2,3,4,5,6,9], "description": "Mixed"},
        ],
        "keywords": ["def quick_sort", "if", "len", "return"],
    },
    {
        "name": "Maximum Subarray (Kadane's)",
        "prompt": "def max_subarray(nums):\n    \"\"\"Return maximum sum of contiguous subarray.\"\"\"\n",
        "function": "max_subarray",
        "max_tokens": 100,
        "test_cases": [
            {"input": ([-2,1,-3,4,-1,2,1,-5,4],), "expected": 6, "description": "Mixed"},
            {"input": ([1],), "expected": 1, "description": "Single"},
        ],
        "keywords": ["for", "max", "+"],
    },
    {
        "name": "Valid Parentheses",
        "prompt": "def valid_parentheses(s):\n    \"\"\"Check if string has valid bracket matching.\"\"\"\n",
        "function": "valid_parentheses",
        "max_tokens": 100,
        "test_cases": [
            {"input": ("()",), "expected": True, "description": "Simple"},
            {"input": ("([)]",), "expected": False, "description": "Wrong order"},
        ],
        "keywords": ["stack", "if", "for", "in", "pop", "append"],
    },
    {
        "name": "Climbing Stairs",
        "prompt": "def climb_stairs(n):\n    \"\"\"Count ways to climb n stairs (1 or 2 steps at a time).\"\"\"\n",
        "function": "climb_stairs",
        "max_tokens": 80,
        "test_cases": [
            {"input": (5,), "expected": 8, "description": "n=5"},
            {"input": (2,), "expected": 2, "description": "n=2"},
        ],
        "keywords": ["for", "while", "+", "="],
    },
    {
        "name": "List Sum",
        "prompt": "def list_sum(nums):\n    \"\"\"Return sum of all numbers in list.\"\"\"\n",
        "function": "list_sum",
        "max_tokens": 50,
        "test_cases": [
            {"input": ([1,2,3,4],), "expected": 10, "description": "Basic"},
            {"input": ([],), "expected": 0, "description": "Empty"},
        ],
        "keywords": ["for", "in", "+", "sum", "0"],
    },
    {
        "name": "List Average",
        "prompt": "def list_avg(nums):\n    \"\"\"Return average of numbers in list.\"\"\"\n",
        "function": "list_avg",
        "max_tokens": 60,
        "test_cases": [
            {"input": ([1,2,3,4,5],), "expected": 3.0, "description": "Basic"},
            {"input": ([5],), "expected": 5.0, "description": "Single"},
        ],
        "keywords": ["sum", "len", "/", "float"],
    },
    {
        "name": "Find Maximum",
        "prompt": "def find_max(nums):\n    \"\"\"Return maximum value in list.\"\"\"\n",
        "function": "find_max",
        "max_tokens": 60,
        "test_cases": [
            {"input": ([3,1,4,1,5,9],), "expected": 9, "description": "Basic"},
            {"input": ([-1,-5,-3],), "expected": -1, "description": "Negatives"},
        ],
        "keywords": ["for", "in", "max", ">", "<"],
    },
    {
        "name": "Count Zeros",
        "prompt": "def count_zeros(nums):\n    \"\"\"Count zeros in list.\"\"\"\n",
        "function": "count_zeros",
        "max_tokens": 50,
        "test_cases": [
            {"input": ([0,1,0,2,0],), "expected": 3, "description": "Mixed"},
            {"input": ([1,2,3],), "expected": 0, "description": "No zeros"},
        ],
        "keywords": ["for", "in", "count", "==", "+"],
    },
    {
        "name": "Unique Elements",
        "prompt": "def unique_elements(lst):\n    \"\"\"Return list of unique elements preserving order.\"\"\"\n",
        "function": "unique_elements",
        "max_tokens": 80,
        "test_cases": [
            {"input": ([1,2,2,3,1],), "expected": [1,2,3], "description": "With dups"},
            {"input": ([1,2,3],), "expected": [1,2,3], "description": "All unique"},
        ],
        "keywords": ["for", "in", "if", "append", "set"],
    },
]


def run_test(model, tokenizer, test_config: Dict) -> Dict:
    """Run a single test and return results."""
    name = test_config["name"]
    prompt = test_config["prompt"]
    func_name = test_config["function"]
    max_tokens = test_config["max_tokens"]
    test_cases = test_config["test_cases"]
    keywords = test_config.get("keywords", [])
    
    print(f"\n  Test: {name}")
    print(f"  Prompt: {prompt.strip()[:60]}...")
    
    start_time = time.time()
    
    # Generate completion
    completions = generate_completion(model, tokenizer, prompt, max_tokens=max_tokens)
    elapsed = time.time() - start_time
    
    # Extract and check code
    code = extract_code(completions[0])
    
    print(f"  Generated in {elapsed:.2f}s")
    print(f"  Code preview: {code[:100]}...")
    
    # Check syntax and execution
    success, error_msg = check_function_output(code, func_name, test_cases)
    
    # Check keywords
    keywords_found = sum(1 for kw in keywords if kw.lower() in code.lower())
    keyword_ratio = keywords_found / len(keywords) if keywords else 0
    
    result = {
        "name": name,
        "passed": success,
        "keywords_found": keywords_found,
        "keywords_total": len(keywords),
        "keyword_ratio": keyword_ratio,
        "execution_time": elapsed,
        "error": error_msg if not success else None,
        "generated_code": code[:500],  # Truncate for storage
    }
    
    if success:
        print(f"  Result: ✅ PASS")
    else:
        print(f"  Result: ❌ FAIL - {error_msg[:60]}")
    
    return result


def calculate_pass_at_k(results: List[Dict], k: int) -> float:
    """Calculate pass@k across all tests.
    
    For simplicity, a test passes if it passes the functional test.
    """
    if not results or k <= 0:
        return 0.0
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    # Simple pass@k: probability that at least 1 of k samples would pass
    # Assuming independence, this is 1 - (1 - p)^k where p = passed/total
    if k >= total:
        return passed / total if total > 0 else 0.0
    
    # For pass@1, it's just the pass rate
    if k == 1:
        return passed / total if total > 0 else 0.0
    
    # For pass@k where k > 1, estimate based on single sample
    p = passed / total if total > 0 else 0.0
    p_at_least_1 = 1 - (1 - p) ** k
    return p_at_least_1


def print_results(results: List[Dict], k_values: List[int] = [1, 10]):
    """Print test results summary."""
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\n  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass rate: {100*passed/total:.1f}%")
    
    for k in k_values:
        pass_at_k = calculate_pass_at_k(results, k)
        print(f"\n  Pass@{k}: {100*pass_at_k:.1f}%")
    
    print("\n  Individual Results:")
    for r in results:
        status = "✅" if r["passed"] else "❌"
        print(f"    {status} {r['name']} (keywords: {r['keywords_found']}/{r['keywords_total']})")


def save_results(results: List[Dict], output_path: str):
    """Save test results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Test Stack 2.9 model on common algorithm tasks"
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
        default="test_results.json",
        help="Output file for results (default: test_results.json)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=200,
        help="Max new tokens per generation (default: 200)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (default: 0.2)"
    )
    parser.add_argument(
        "--test-names",
        type=str,
        default=None,
        help="Comma-separated test names to run (default: all)"
    )
    parser.add_argument(
        "--k-values",
        type=str,
        default="1,10",
        help="Comma-separated k values for pass@k (default: 1,10)"
    )
    
    args = parser.parse_args()
    
    k_values = [int(k.strip()) for k in args.k_values.split(",")]
    
    print("="*60)
    print("Stack 2.9 Model - Algorithm Tests")
    print("="*60)
    print(f"Model path: {args.model_path}")
    print(f"Output: {args.output}")
    print(f"Max tokens: {args.max_tokens}")
    print(f"Temperature: {args.temperature}")
    
    # Load model
    model, tokenizer = load_model(args.model_path)
    model.eval()
    
    # Select tests to run
    tests_to_run = ALGORITHM_TESTS
    if args.test_names:
        names = [n.strip() for n in args.test_names.split(",")]
        tests_to_run = [t for t in tests_to_run if t["name"] in names]
        print(f"Running tests: {[t['name'] for t in tests_to_run]}")
    
    if not tests_to_run:
        print("No tests to run!")
        return
    
    # Override max_tokens for each test
    for test in tests_to_run:
        if args.max_tokens:
            test["max_tokens"] = args.max_tokens
    
    # Run tests
    print("\n" + "="*60)
    print(f"Running {len(tests_to_run)} Tests")
    print("="*60)
    
    results = []
    total_start = time.time()
    
    for i, test in enumerate(tests_to_run, 1):
        print(f"\n[{i}/{len(tests_to_run)}]")
        result = run_test(model, tokenizer, test)
        results.append(result)
    
    total_time = time.time() - total_start
    
    # Print summary
    print_results(results, k_values)
    print(f"\n  Total time: {total_time:.1f}s")
    
    # Save results
    save_results(results, args.output)


if __name__ == "__main__":
    main()
