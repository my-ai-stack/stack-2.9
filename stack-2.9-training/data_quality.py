#!/usr/bin/env python3
"""
Stack 2.9 Data Quality Module
Quality scoring, filtering, and deduplication for training data.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality metrics for a training example."""
    overall: float
    length_score: float
    code_quality: float
    structure_score: float
    issues: List[str]


class DataQualityAnalyzer:
    """Analyzes and filters training data quality."""

    def __init__(
        self,
        min_response_length: int = 20,
        max_length: int = 128000,
        min_code_ratio: float = 0.1,
        require_valid_schema: bool = True
    ):
        self.min_response_length = min_response_length
        self.max_length = max_length
        self.min_code_ratio = min_code_ratio
        self.require_valid_schema = require_valid_schema

    def analyze_example(self, example: Dict[str, Any]) -> QualityScore:
        """Analyze a single training example and return quality metrics."""
        issues = []

        # Extract content from various formats
        content = self._extract_content(example)
        response = self._extract_response(example)

        # Length scoring
        length_score = self._score_length(response)
        if length_score < 0.3:
            issues.append("Response too short")

        # Code quality scoring
        code_quality = self._score_code_quality(response)
        if code_quality < 0.2:
            issues.append("Low code quality")

        # Structure scoring
        structure_score = self._score_structure(example)
        if structure_score < 0.3:
            issues.append("Poor structure")

        # Calculate overall score
        overall = (length_score * 0.3 + code_quality * 0.4 + structure_score * 0.3)

        return QualityScore(
            overall=overall,
            length_score=length_score,
            code_quality=code_quality,
            structure_score=structure_score,
            issues=issues
        )

    def _extract_content(self, example: Dict[str, Any]) -> str:
        """Extract full content from example."""
        if "messages" in example:
            return " ".join(msg.get("content", "") for msg in example["messages"])
        elif "instruction" in example:
            return example.get("instruction", "") + " " + example.get("response", "")
        elif "prompt" in example:
            return example.get("prompt", "") + " " + example.get("completion", "")
        elif "input" in example:
            return example.get("input", "") + " " + example.get("output", "")
        return json.dumps(example)

    def _extract_response(self, example: Dict[str, Any]) -> str:
        """Extract response content from example."""
        if "messages" in example:
            for msg in example["messages"]:
                if msg.get("role") == "assistant":
                    return msg.get("content", "")
        elif "response" in example:
            return example["response"]
        elif "completion" in example:
            return example["completion"]
        elif "output" in example:
            return example["output"]
        return ""

    def _score_length(self, response: str) -> float:
        """Score based on response length."""
        if not response:
            return 0.0

        length = len(response)

        if length < self.min_response_length:
            return 0.0
        elif length > self.max_length:
            return 0.2

        # Optimal range: 100-10000 chars
        if 100 <= length <= 10000:
            return 1.0
        elif length < 100:
            return 0.3
        else:
            # Linearly decay from 10000 to max_length
            return max(0.5, 1.0 - (length - 10000) / (self.max_length - 10000))

    def _score_code_quality(self, response: str) -> float:
        """Score code quality based on patterns."""
        if not response:
            return 0.0

        score = 0.5  # Base score

        # Check for code blocks
        code_blocks = len(re.findall(r'```[\s\S]*?```', response))
        if code_blocks > 0:
            score += 0.2

        # Check for common programming patterns
        patterns = [
            r'def\s+\w+\s*\(',  # Function definitions
            r'class\s+\w+',     # Class definitions
            r'if\s+',           # Conditionals
            r'for\s+',          # Loops
            r'return\s+',       # Returns
            r'import\s+\w+',    # Imports
            r'from\s+\w+\s+import',  # Named imports
        ]

        pattern_count = sum(1 for p in patterns if re.search(p, response))
        score += min(0.2, pattern_count * 0.05)

        # Penalize placeholder content
        placeholder_patterns = [
            r'\bTODO\b',
            r'\bFIXME\b',
            r'\bXXX\b',
            r'^\s*$',  # Empty lines
        ]

        placeholder_count = sum(len(re.findall(p, response, re.MULTILINE)) for p in placeholder_patterns)
        if placeholder_count > 5:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _score_structure(self, example: Dict[str, Any]) -> float:
        """Score based on data structure validity."""
        score = 0.5  # Base score

        # Check for required fields
        if "messages" in example:
            roles = {msg.get("role") for msg in example.get("messages", [])}
            if "user" in roles and "assistant" in roles:
                score += 0.3
            if "system" in roles:
                score += 0.1
        elif "instruction" in example and "response" in example:
            score += 0.4
        elif "prompt" in example and "completion" in example:
            score += 0.4

        # Check tool usage validity
        if "messages" in example:
            for msg in example["messages"]:
                if msg.get("role") == "assistant" and "tool_calls" in msg:
                    # Validate tool call structure
                    if self._validate_tool_calls(msg["tool_calls"]):
                        score += 0.1

        return min(1.0, score)

    def _validate_tool_calls(self, tool_calls: List[Dict]) -> bool:
        """Validate tool call structure."""
        if not isinstance(tool_calls, list):
            return False

        for call in tool_calls:
            if not isinstance(call, dict):
                return False
            if "function" not in call:
                return False
            if "name" not in call.get("function", {}):
                return False

        return True


def deduplicate(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Remove duplicate examples based on content hash.

    Returns:
        Tuple of (unique_data, duplicates_removed)
    """
    seen_hashes = set()
    unique_data = []

    for example in data:
        # Create hash from the formatted content
        content = json.dumps(example, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_data.append(example)

    duplicates_removed = len(data) - len(unique_data)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate examples")

    return unique_data, duplicates_removed


def filter_by_quality(
    data: List[Dict[str, Any]],
    min_score: float = 0.4,
    analyzer: Optional[DataQualityAnalyzer] = None
) -> Tuple[List[Dict[str, Any]], List[QualityScore]]:
    """
    Filter training data by quality score.

    Returns:
        Tuple of (filtered_data, all_scores)
    """
    if analyzer is None:
        analyzer = DataQualityAnalyzer()

    filtered_data = []
    all_scores = []

    for example in data:
        score = analyzer.analyze_example(example)
        all_scores.append(score)

        if score.overall >= min_score:
            filtered_data.append(example)

    filtered_count = len(data) - len(filtered_data)
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} low-quality examples")

    return filtered_data, all_scores


def filter_by_completeness(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out incomplete examples."""
    filtered = []

    for example in data:
        # Check messages format
        if "messages" in example:
            messages = example.get("messages", [])
            has_user = any(m.get("role") == "user" for m in messages)
            has_assistant = any(m.get("role") == "assistant" for m in messages)

            if not has_user or not has_assistant:
                continue

            # Check for empty content
            has_content = any(
                m.get("content") and len(m.get("content", "").strip()) > 0
                for m in messages
            )
            if not has_content:
                continue

        # Check instruction/response format
        elif "instruction" in example and "response" in example:
            if not example.get("instruction", "").strip():
                continue
            if not example.get("response", "").strip():
                continue

        # Check prompt/completion format
        elif "prompt" in example and "completion" in example:
            if not example.get("prompt", "").strip():
                continue
            if not example.get("completion", "").strip():
                continue

        # Check input/output format
        elif "input" in example and "output" in example:
            if not example.get("input", "").strip():
                continue
            if not example.get("output", "").strip():
                continue

        else:
            # Unknown format - skip
            continue

        filtered.append(example)

    return filtered


def filter_code_pairs(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter code pair data to remove entries with missing essential fields."""
    filtered = []

    for entry in data:
        # Skip entries missing essential fields
        if not entry.get("code"):
            continue
        if not entry.get("fullBody"):
            continue

        # Skip entries with placeholder content
        code = entry.get("code", "")
        if "{ ... }" in code or code.strip() == "":
            continue

        filtered.append(entry)

    return filtered


def filter_tool_catalog(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter tool catalog to add missing metadata."""
    filtered = []

    for tool in data:
        # Add default description if missing
        if not tool.get("description"):
            tool["description"] = f"Tool for {tool.get('tool', 'unknown operation')}"

        # Add empty input schema if missing
        if not tool.get("inputSchema"):
            tool["inputSchema"] = {"type": "object", "properties": {}}

        filtered.append(tool)

    return filtered


def process_pipeline(
    input_files: List[Path],
    output_path: Path,
    min_quality_score: float = 0.4
) -> Dict[str, Any]:
    """
    Run full data quality pipeline on multiple input files.

    Args:
        input_files: List of input JSONL files
        output_path: Path to save cleaned data
        min_quality_score: Minimum quality score to keep

    Returns:
        Statistics dictionary
    """
    all_data = []

    # Load all data
    for file_path in input_files:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        logger.info(f"Loading {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    all_data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON: {e}")

    logger.info(f"Loaded {len(all_data)} total examples")

    # Filter by completeness
    all_data = filter_by_completeness(all_data)
    logger.info(f"After completeness filter: {len(all_data)}")

    # Deduplicate
    all_data, dup_count = deduplicate(all_data)
    logger.info(f"After deduplication: {len(all_data)}")

    # Filter by quality
    analyzer = DataQualityAnalyzer()
    all_data, scores = filter_by_quality(all_data, min_quality_score, analyzer)
    logger.info(f"After quality filter: {len(all_data)}")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # Calculate statistics
    avg_score = sum(s.overall for s in scores) / len(scores) if scores else 0

    return {
        "total_input": len(all_data),
        "duplicates_removed": dup_count,
        "final_count": len(all_data),
        "avg_quality_score": avg_score,
        "output_file": str(output_path)
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stack 2.9 Data Quality Analysis")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input JSONL file")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output JSONL file")
    parser.add_argument("--min-score", type=float, default=0.4, help="Minimum quality score")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    result = process_pipeline([input_path], output_path, args.min_score)

    print(f"\n✓ Processing complete!")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Examples: {result['final_count']}")
    print(f"  Avg quality: {result['avg_quality_score']:.2f}")