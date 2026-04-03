#!/usr/bin/env python3
"""
Inference Examples for Stack 2.9
Demonstrates model capabilities across diverse coding tasks.

Run: python inference_examples.py --provider ollama --model qwen2.5-coder:32b
"""

from typing import Dict, Any, List
import argparse
import sys
from pathlib import Path

# Import the model client (assuming running from project root)
sys.path.insert(0, str(Path(__file__).parent / "stack-2.9-eval"))
try:
    from model_client import create_model_client, ChatMessage
except ImportError:
    print("Warning: Could not import model_client. Running in documentation mode.")
    create_model_client = None
    ChatMessage = None


class InferenceExamples:
    """Collection of diverse inference examples."""

    def __init__(self, client=None):
        self.client = client
        self.results = []

    def run_example(self, name: str, prompt: str, messages: List[Dict] = None, **kwargs):
        """Run a single example and record results."""
        print(f"\n{'='*60}")
        print(f"Example: {name}")
        print(f"{'='*60}")
        print(f"Prompt/Input:\n{prompt if prompt else 'Chat messages'}")
        print(f"\n{'─'*40}")

        if self.client:
            try:
                if messages:
                    # Chat mode
                    chat_messages = [ChatMessage(**m) for m in messages]
                    result = self.client.chat(chat_messages, **kwargs)
                else:
                    # Completion mode
                    result = self.client.generate(prompt, **kwargs)

                print(f"Response:\n{result.text}")
                print(f"\n📊 Stats: {result.tokens} tokens, {result.duration:.2f}s")

                self.results.append({
                    "name": name,
                    "prompt": prompt,
                    "response": result.text,
                    "tokens": result.tokens,
                    "duration": result.duration
                })
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("[Example would be executed here with a valid model client]")
            print(f"Expected response: Code generation or tool use for this task")

    def all_examples(self):
        """Run all example demonstrations."""
        # 1. Simple Code Generation
        self.run_example(
            "1. Simple Function",
            "Write a Python function to calculate the factorial of a number using recursion."
        )

        # 2. Algorithmic Problem
        self.run_example(
            "2. Data Structure",
            "Implement a LRU (Least Recently Used) cache in Python with O(1) operations."
        )

        # 3. Code Explanation
        self.run_example(
            "3. Code Explanation",
            """Explain the following code:

```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
```"""
        )

        # 4. Debugging Assistance
        self.run_example(
            "4. Debugging",
            """Find and fix the bug in this code:

```python
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(len(lst)):
            if i != j and lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return duplicates
```"""
        )

        # 5. Code Refactoring
        self.run_example(
            "5. Refactoring",
            """Refactor this code to be more Pythonic and efficient:

```python
result = []
for i in range(10):
    if i % 2 == 0:
        result.append(i * i)
```"""
        )

        # 6. API Integration
        self.run_example(
            "6. API Use",
            "Write a Python function that fetches data from a REST API with error handling and retries."
        )

        # 7. File Operations with Tool Use (pattern demonstration)
        self.run_example(
            "7. File Operations",
            """Using OpenClaw tools, read a file named 'config.json' from the current directory,
parse it as JSON, and then write a new file 'config_backup.json' with the same content
but with an added field 'backup_date' set to today's date."""
        )

        # 8. Multi-step Workflow
        self.run_example(
            "8. Multi-step Workflow",
            """Task: Initialize a new Python project with proper structure.
Steps:
1. Create project directory 'myproject'
2. Inside it, create src/, tests/, docs/ directories
3. Create a requirements.txt file with common packages
4. Create a README.md with project title and description
5. Create a basic Python module in src/ with a main function
6. Create a simple test in tests/

Provide the shell commands or tool calls to accomplish this."""
        )

        # 9. Complex System Design
        self.run_example(
            "9. System Design",
            """Design a simple task queue system in Python with the following components:
- Task representation (with priority, dependencies, retry logic)
- Queue management (add, remove, prioritize)
- Worker pool that executes tasks concurrently
- Result tracking and error handling

Provide a high-level architecture and key code snippets."""
        )

        # 10. Web Development
        self.run_example(
            "10. Web Framework",
            "Create a simple Flask (or FastAPI) application with:
- GET endpoint that returns JSON with a welcome message
- POST endpoint that accepts user data and stores in memory
- Error handling for invalid input
- CORS middleware if using FastAPI"
        )

        # 11. Code Translation
        self.run_example(
            "11. Code Translation",
            """Convert this JavaScript function to Python:

```javascript
function filterUsers(users, minAge, activeOnly) {
  return users.filter(user => {
    if (activeOnly && !user.active) return false;
    if (user.age >= minAge) return true;
    return false;
  });
}
```"""
        )

        # 12. Testing
        self.run_example(
            "12. Unit Tests",
            """Write pytest unit tests for this function:

```python
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```"""
        )

        # 13. Data Processing
        self.run_example(
            "13. Data Analysis",
            """Given a CSV file 'sales.csv' with columns: date, product, quantity, price
Write a Python script to:
- Read the CSV
- Add a 'revenue' column (quantity * price)
- Group by product and sum revenue
- Output top 10 products by revenue to 'top_products.csv'"""
        )

        # 14. Concurrency
        self.run_example(
            "14. Async Programming",
            "Write an async Python function that concurrently fetches data from multiple URLs and returns results in order."
        )

        # 15. Pattern Memory Retrieval (self-evolution concept)
        self.run_example(
            "15. Pattern Learning",
            """Based on learned patterns for 'recursive tree traversal', implement a function
to compute the maximum depth of a binary tree. Use a递归 approach similar to previous
successful solutions for tree problems."""
        )

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print summary of results."""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total Examples: {len(self.results)}")
        if self.results:
            total_tokens = sum(r['tokens'] for r in self.results if r['tokens'])
            total_duration = sum(r['duration'] for r in self.results if r['duration'])
            print(f"Total Tokens: {total_tokens}")
            print(f"Total Duration: {total_duration:.2f}s")
            if total_tokens > 0:
                tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0
                print(f"Average Throughput: {tokens_per_sec:.1f} tokens/sec")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Run inference examples with Stack 2.9")
    parser.add_argument("--provider", default="ollama",
                        choices=["ollama", "openai", "anthropic", "openrouter", "together"],
                        help="Model provider")
    parser.add_argument("--model", type=str,
                        help="Model name (defaults to provider's default)")
    parser.add_argument("--api-key", type=str,
                        help="API key (or set environment variable)")
    parser.add_argument("--temperature", type=float, default=0.2,
                        help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="Maximum tokens to generate")
    parser.add_argument("--list-only", action="store_true",
                        help="List examples without running")

    args = parser.parse_args()

    # Create client if not list-only
    client = None
    if not args.list_only:
        if create_model_client:
            try:
                client = create_model_client(
                    provider=args.provider,
                    model=args.model,
                    api_key=args.api_key
                )
                print(f"✓ Using model: {client.get_model_name()}")
                print(f"✓ Provider: {args.provider}")
            except Exception as e:
                print(f"Failed to create client: {e}")
                print("Running in documentation mode...")
                client = None
        else:
            print("Model client not available. Running in documentation mode...")

    # Run examples
    examples = InferenceExamples(client)
    examples.all_examples()


if __name__ == "__main__":
    main()
