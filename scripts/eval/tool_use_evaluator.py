#!/usr/bin/env python3
"""
Evaluate Stack 2.9 on tool-use test suite.
Supports: local model (transformers) or vLLM API.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import openai
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def load_test_cases(path: str) -> List[Dict]:
    with open(path, 'r') as f:
        return json.load(f)

def predict_with_transformers(model_path: str, prompt: str) -> Dict:
    """Query local model for tool prediction."""
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        torch_dtype=torch.float16
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.2,
        do_sample=False
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Parse tool call from response (simple version - assumes structured format)
    # This is a placeholder - real parser needs to extract JSON tool use
    return {
        "tool": "UnknownTool",
        "params": {},
        "raw_response": response
    }

def predict_with_vllm(api_url: str, prompt: str, model_name: str = "stack-2.9") -> Dict:
    """Query vLLM server."""
    client = openai.OpenAI(
        base_url=api_url,
        api_key="dummy"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.2
    )

    content = response.choices[0].message.content
    # Parse tool call from content
    return {
        "tool": "UnknownTool",
        "params": {},
        "raw_response": content
    }

def evaluate_predictions(
    test_cases: List[Dict],
    predictions: List[Dict],
    tool_catalog: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Compare predictions against ground truth."""
    total = len(test_cases)
    correct_tool = 0
    correct_params = 0
    exact_match = 0

    per_tool = {}

    for tc, pred in zip(test_cases, predictions):
        expected_tool = tc["expected_tool"]
        pred_tool = pred["tool"]

        # Tool accuracy
        tool_correct = pred_tool == expected_tool
        if tool_correct:
            correct_tool += 1

        # Parameter accuracy (simple: exact match of params dict, or partial?)
        expected_params = tc["expected_params"]
        pred_params = pred["params"]
        # For now, check if all expected params are present with same values
        param_correct = all(
            pred_params.get(k) == v for k, v in expected_params.items()
        ) if expected_params else True
        if param_correct:
            correct_params += 1

        # Exact match (tool + all params)
        if tool_correct and param_correct:
            exact_match += 1

        # Track per-tool stats
        if expected_tool not in per_tool:
            per_tool[expected_tool] = {"total": 0, "correct_tool": 0, "correct_params": 0}
        per_tool[expected_tool]["total"] += 1
        if tool_correct:
            per_tool[expected_tool]["correct_tool"] += 1
        if param_correct:
            per_tool[expected_tool]["correct_params"] += 1

    return {
        "total_examples": total,
        "tool_accuracy": correct_tool / total if total > 0 else 0,
        "parameter_accuracy": correct_params / total if total > 0 else 0,
        "exact_match_accuracy": exact_match / total if total > 0 else 0,
        "per_tool_breakdown": per_tool
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-cases", type=str, default="stack-2.9-eval/tool_use/test_cases.json")
    parser.add_argument("--catalog", type=str, default="training-data/tools/catalog.json")
    parser.add_argument("--model-path", type=str, help="HuggingFace model path for transformers")
    parser.add_argument("--vllm-api", type=str, help="vLLM API URL (e.g., http://localhost:8000)")
    parser.add_argument("--output", type=str, default="stack-2.9-eval/tool_use/results.json")
    parser.add_argument("--limit", type=int, help="Limit number of test cases to evaluate")
    args = parser.parse_args()

    test_cases_path = Path(args.test_cases)
    catalog_path = Path(args.catalog)

    if not test_cases_path.exists():
        print(f"❌ Test cases not found: {test_cases_path}")
        print("   Run generate_tool_use_tests.py first")
        return

    test_cases = load_test_cases(test_cases_path)
    if args.limit:
        test_cases = test_cases[:args.limit]

    print(f"🧪 Evaluating {len(test_cases)} tool-use test cases")

    # Load tool catalog
    tool_catalog = None
    if catalog_path.exists():
        with open(catalog_path, 'r') as f:
            tool_catalog = {t["tool"]: t for t in json.load(f)}
        print(f"✅ Loaded tool catalog ({len(tool_catalog)} tools)")

    # Generate predictions
    predictions = []
    for i, tc in enumerate(test_cases):
        prompt = tc["prompt"]

        if args.model_path:
            pred = predict_with_transformers(args.model_path, prompt)
        elif args.vllm_api:
            pred = predict_with_vllm(args.vllm_api, prompt)
        else:
            # Mock predictor (random baseline)
            import random
            tools = list(tool_catalog.keys()) if tool_catalog else ["UnknownTool"]
            pred = {
                "tool": random.choice(tools),
                "params": {},
                "raw_response": "Mock prediction"
            }

        predictions.append(pred)

        if (i+1) % 10 == 0:
            print(f"   Processed {i+1}/{len(test_cases)}...", end='\r')

    print(f"\n📊 Evaluating predictions...")

    # Evaluate
    results = evaluate_predictions(test_cases, predictions, tool_catalog)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Evaluation results:")
    print(f"   Tool accuracy: {results['tool_accuracy']*100:.1f}%")
    print(f"   Param accuracy: {results['parameter_accuracy']*100:.1f}%")
    print(f"   Exact match: {results['exact_match_accuracy']*100:.1f}%")
    print(f"\n   Results saved to: {output_path}")

    # Show per-tool breakdown (top 5 worst)
    if results['per_tool_breakdown']:
        print("\n📉 Worst performing tools:")
        sorted_tools = sorted(
            results['per_tool_breakdown'].items(),
            key=lambda x: x[1]['correct_tool'] / x[1]['total'] if x[1]['total']>0 else 0
        )[:5]
        for tool, stats in sorted_tools:
            acc = stats['correct_tool'] / stats['total'] * 100
            print(f"   {tool}: {acc:.1f}% ({stats['correct_tool']}/{stats['total']})")

if __name__ == "__main__":
    main()