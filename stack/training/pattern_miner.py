#!/usr/bin/env python3
"""
Stack 2.9 Pattern Miner
Extracts patterns from successful solutions and feedback for self-evolution.
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A learned pattern from solutions."""
    id: str
    pattern_type: str  # "code_structure", "algorithm", "error_recovery", etc.
    description: str
    code_snippet: str
    success_count: int
    failure_count: int
    success_rate: float
    tags: List[str]
    created_at: str
    last_used: str


@dataclass
class Feedback:
    """Feedback from a solution attempt."""
    id: str
    problem_type: str
    solution: str
    success: bool
    error_message: Optional[str]
    execution_time: float
    timestamp: str
    model_version: Optional[str] = None


class PatternMiner:
    """Extracts patterns from code solutions."""

    # Pattern type keywords
    PATTERN_TYPES = {
        "recursion": [r"def\s+(\w+)\s*\([^)]*\):\s*.*\1\(", r"return\s+(\w+)\s*\([^)]*\)\s*\1\("],
        "iteration": [r"for\s+", r"while\s+"],
        "list_comprehension": [r"\[.*for.*in.*\]"],
        "dictionary": [r"\{\w+:", r"dict\(", r"defaultdict\("],
        "set_operations": [r"set\(", r"\&\s*", r"\|\s*", r"\-\s*"],
        "sorting": [r"sorted\(", r"\.sort\("],
        "searching": [r"\.index\(", r"\.find\(", r"in\s+"],
        "file_io": [r"open\(", r"read\(", r"write\("],
        "error_handling": [r"try:", r"except", r"finally:"],
        "class_definition": [r"class\s+\w+", r"def\s+__init__"],
        "function_composition": [r"\.map\(", r"\.filter\(", r"\.reduce\("],
    }

    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path(__file__).parent / "patterns"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.patterns_file = self.storage_dir / "patterns.json"
        self.feedback_file = self.storage_dir / "feedback.json"

        self.patterns = self._load_patterns()
        self.feedback = self._load_feedback()

    def _load_patterns(self) -> List[Pattern]:
        """Load stored patterns."""
        if not self.patterns_file.exists():
            return []

        with open(self.patterns_file, 'r') as f:
            data = json.load(f)
            return [Pattern(**p) for p in data]

    def _load_feedback(self) -> List[Feedback]:
        """Load stored feedback."""
        if not self.feedback_file.exists():
            return []

        with open(self.feedback_file, 'r') as f:
            data = json.load(f)
            return [Feedback(**fb) for fb in data]

    def _save_patterns(self):
        """Save patterns to storage."""
        with open(self.patterns_file, 'w') as f:
            json.dump([asdict(p) for p in self.patterns], f, indent=2)

    def _save_feedback(self):
        """Save feedback to storage."""
        with open(self.feedback_file, 'w') as f:
            json.dump([asdict(fb) for fb in self.feedback], f, indent=2)

    def store_feedback(
        self,
        problem_type: str,
        solution: str,
        success: bool,
        error_message: Optional[str] = None,
        execution_time: float = 0.0,
        model_version: Optional[str] = None
    ) -> Feedback:
        """Store feedback from a solution attempt."""
        fb = Feedback(
            id=hashlib.sha256(f"{datetime.now().isoformat()}{solution}".encode()).hexdigest()[:16],
            problem_type=problem_type,
            solution=solution,
            success=success,
            error_message=error_message,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            model_version=model_version
        )

        self.feedback.append(fb)
        self._save_feedback()

        # Extract patterns if successful
        if success:
            self._extract_patterns_from_solution(solution, problem_type)

        return fb

    def _extract_patterns_from_solution(self, solution: str, problem_type: str):
        """Extract patterns from a successful solution."""
        # Identify pattern types
        for ptype, regexes in self.PATTERN_TYPES.items():
            for regex in regexes:
                if re.search(regex, solution):
                    self._add_pattern(ptype, solution, problem_type)
                    break

        # Extract code structure patterns
        self._extract_structure_patterns(solution, problem_type)

    def _extract_structure_patterns(self, code: str, problem_type: str):
        """Extract structural patterns from code."""
        # Find function definitions
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        if functions:
            self._add_pattern(
                "function_definition",
                f"def {functions[0]}(...)",
                problem_type,
                tags=["function", functions[0]]
            )

        # Find class definitions
        classes = re.findall(r'class\s+(\w+)', code)
        for cls in classes:
            self._add_pattern(
                "class_definition",
                f"class {cls}",
                problem_type,
                tags=["class", cls]
            )

    def _add_pattern(
        self,
        pattern_type: str,
        snippet: str,
        problem_type: str,
        tags: Optional[List[str]] = None
    ):
        """Add or update a pattern."""
        # Check if pattern already exists
        existing = None
        for p in self.patterns:
            if p.pattern_type == pattern_type and p.code_snippet == snippet:
                existing = p
                break

        if existing:
            # Update existing pattern
            existing.success_count += 1
            existing.success_rate = existing.success_count / (existing.success_count + existing.failure_count)
            existing.last_used = datetime.now().isoformat()
        else:
            # Create new pattern
            pattern = Pattern(
                id=hashlib.sha256(f"{pattern_type}{snippet}".encode()).hexdigest()[:16],
                pattern_type=pattern_type,
                description=f"Pattern for {problem_type}",
                code_snippet=snippet,
                success_count=1,
                failure_count=0,
                success_rate=1.0,
                tags=tags or [problem_type],
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat()
            )
            self.patterns.append(pattern)

        self._save_patterns()

    def mark_pattern_failure(self, pattern_id: str):
        """Mark a pattern as failed."""
        for p in self.patterns:
            if p.id == pattern_id:
                p.failure_count += 1
                p.success_rate = p.success_count / (p.success_count + p.failure_count)
                break

        self._save_patterns()

    def get_relevant_patterns(
        self,
        problem_type: str = None,
        min_success_rate: float = 0.5,
        limit: int = 10
    ) -> List[Pattern]:
        """Get relevant patterns for a problem type."""
        relevant = []

        for p in self.patterns:
            # Filter by success rate
            if p.success_rate < min_success_rate:
                continue

            # Filter by problem type if specified
            if problem_type and problem_type not in p.tags:
                continue

            relevant.append(p)

        # Sort by success rate and usage
        relevant.sort(key=lambda p: (p.success_rate, p.success_count), reverse=True)

        return relevant[:limit]

    def generate_pattern_prompt(self, patterns: List[Pattern]) -> str:
        """Generate a prompt with relevant patterns."""
        if not patterns:
            return ""

        prompt = "Here are some patterns that worked well for similar problems:\n\n"

        for i, p in enumerate(patterns, 1):
            prompt += f"{i}. [{p.pattern_type}] {p.description}\n"
            prompt += f"   Code: {p.code_snippet}\n"
            prompt += f"   Success rate: {p.success_rate:.1%}\n\n"

        return prompt

    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern mining statistics."""
        if not self.feedback:
            return {"total_feedback": 0, "total_patterns": 0}

        success_count = sum(1 for fb in self.feedback if fb.success)
        failure_count = len(self.feedback) - success_count

        # Group by problem type
        by_type = defaultdict(lambda: {"success": 0, "failure": 0})
        for fb in self.feedback:
            by_type[fb.problem_type]["success" if fb.success else "failure"] += 1

        # Pattern statistics
        pattern_types = defaultdict(int)
        for p in self.patterns:
            pattern_types[p.pattern_type] += 1

        return {
            "total_feedback": len(self.feedback),
            "successful_solutions": success_count,
            "failed_solutions": failure_count,
            "success_rate": success_count / len(self.feedback) if self.feedback else 0,
            "total_patterns": len(self.patterns),
            "patterns_by_type": dict(pattern_types),
            "by_problem_type": dict(by_type)
        }


def create_synthetic_feedback(
    output_file: Path,
    num_examples: int = 100
) -> int:
    """Create synthetic feedback data for testing."""
    import random

    problems = [
        "list_operations", "string_manipulation", "recursion",
        "sorting", "searching", "file_io", "error_handling"
    ]

    success_solutions = {
        "list_operations": [
            "return [x for x in lst if x > 0]",
            "return sum(lst)",
            "return max(lst) if lst else None",
        ],
        "string_manipulation": [
            "return s[::-1]",
            "return s.upper()",
            "return ''.join(sorted(s))",
        ],
        "recursion": [
            "if n <= 1: return 1\nreturn n * fact(n-1)",
            "if not head: return None\nreturn head.val + sum_list(head.next)",
        ],
        "sorting": [
            "return sorted(lst)",
            "lst.sort()\nreturn lst",
        ],
        "searching": [
            "return any(x == target for x in lst)",
            "for i, x in enumerate(lst):\n    if x == target: return i\nreturn -1",
        ],
    }

    miner = PatternMiner()

    for _ in range(num_examples):
        problem = random.choice(problems)
        solution = random.choice(success_solutions.get(problem, ["# solution"]))
        success = random.random() > 0.2  # 80% success rate

        miner.store_feedback(
            problem_type=problem,
            solution=solution,
            success=success,
            error_message=None if success else "Test failed",
            execution_time=random.uniform(0.1, 2.0)
        )

    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump([asdict(fb) for fb in miner.feedback], f, indent=2)

    return num_examples


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stack 2.9 Pattern Miner")
    parser.add_argument("--store", action="store_true",
                        help="Store a feedback example")
    parser.add_argument("--problem-type", type=str, help="Problem type")
    parser.add_argument("--solution", type=str, help="Solution code")
    parser.add_argument("--success", type=lambda x: x.lower() == "true",
                        default=True, help="Success flag")
    parser.add_argument("--list-patterns", action="store_true",
                        help="List relevant patterns")
    parser.add_argument("--stats", action="store_true",
                        help="Show statistics")
    parser.add_argument("--generate-synthetic", type=int, metavar="N",
                        help="Generate N synthetic examples")

    args = parser.parse_args()

    miner = PatternMiner()

    if args.store:
        if not args.problem_type or not args.solution:
            print("Error: --problem-type and --solution required")
            exit(1)

        fb = miner.store_feedback(
            problem_type=args.problem_type,
            solution=args.solution,
            success=args.success
        )
        print(f"Stored feedback: {fb.id}")

    elif args.list_patterns:
        patterns = miner.get_relevant_patterns(args.problem_type)
        print(f"\nRelevant patterns ({len(patterns)}):")
        for p in patterns:
            print(f"  [{p.pattern_type}] {p.code_snippet} (rate: {p.success_rate:.1%})")

    elif args.stats:
        stats = miner.get_statistics()
        print("\nPattern Mining Statistics:")
        print(f"  Total feedback: {stats['total_feedback']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Total patterns: {stats['total_patterns']}")
        print(f"  Patterns by type: {stats['patterns_by_type']}")

    elif args.generate_synthetic:
        count = create_synthetic_feedback(
            Path("/tmp/synthetic_feedback.json"),
            args.generate_synthetic
        )
        print(f"Generated {count} synthetic examples")

    else:
        print("Pattern Miner")
        print("Use --help for options")