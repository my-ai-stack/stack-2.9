#!/usr/bin/env python3
"""
Extract Code Patterns from Git History

Scans Git commit history to identify bug fixes and feature additions,
extracting "before → after" patterns for training data generation.

Usage:
    python extract_patterns_from_git.py --repo-path . --output patterns.jsonl
    python extract_patterns_from_git.py --repo-path . --output patterns.jsonl --since-date "2024-01-01"
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


# Keywords that indicate bug fixes or improvements
BUG_FIX_KEYWORDS = [
    "fix", "bug", "hotfix", "patch", "resolve", "correct", "repair",
    "error", "crash", "fail", "issue", "problem", "broken"
]

FEATURE_KEYWORDS = [
    "feat", "feature", "add", "new", "implement", "enhance", "improve",
    "optimize", "refactor", "support", "introduce"
]


def is_text_file(filepath: str) -> bool:
    """Check if a file is likely a text file (not binary)."""
    binary_extensions = {
        '.pyc', '.so', '.dll', '.exe', '.bin', '.dat', '.pickle',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.wav', '.avi', '.mov', '.pdf', '.zip',
        '.tar', '.gz', '.rar', '.7z', '.whl', '.egg',
        '.class', '.jar', '.war', '.ear',
        '.db', '.sqlite', '.sqlite3',
        '.ttf', '.otf', '.woff', '.woff2',
        '.pem', '.key', '.crt', '.cer',
        '.DS_Store', '.gitignore'
    }
    
    ext = Path(filepath).suffix.lower()
    if ext in binary_extensions:
        return False
    
    # Try to read as text
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return False
        return True
    except (OSError, IOError):
        return False


def get_commit_messages(repo_path: str, since_date: Optional[str] = None) -> list[dict]:
    """Get commit information from git log."""
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%H|%s|%an|%ad|%ae", "--date=iso"]
    
    if since_date:
        cmd.extend([f"--since={since_date}"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        commits = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3],
                    'email': parts[4] if len(parts) > 4 else ''
                })
        
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error reading git log: {e}", file=sys.stderr)
        return []


def get_changed_files(repo_path: str, commit_hash: str) -> list[str]:
    """Get list of files changed in a commit."""
    cmd = ["git", "-C", repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                files.append(line.strip())
        return files
    except subprocess.CalledProcessError:
        return []


def get_file_diff(repo_path: str, commit_hash: str, filepath: str) -> tuple[Optional[str], Optional[str]]:
    """Get before and after content of a file in a commit."""
    # Get the file content AFTER the commit
    cmd_after = ["git", "-C", repo_path, "show", f"{commit_hash}:{filepath}"]
    # Get the file content BEFORE the commit (parent)
    cmd_before = ["git", "-C", repo_path, "show", f"{commit_hash}^:{filepath}"]
    
    after_content = None
    before_content = None
    
    try:
        result_after = subprocess.run(cmd_after, capture_output=True, text=True, check=True)
        after_content = result_after.stdout
    except subprocess.CalledProcessError:
        # File might be new (no parent)
        after_content = None
    
    try:
        result_before = subprocess.run(cmd_before, capture_output=True, text=True, check=True)
        before_content = result_before.stdout
    except subprocess.CalledProcessError:
        # File was added in this commit
        before_content = None
    
    return before_content, after_content


def infer_problem_type(message: str) -> str:
    """Infer the problem type from commit message."""
    msg_lower = message.lower()
    
    # Check for bug fix indicators
    for keyword in BUG_FIX_KEYWORDS:
        if keyword in msg_lower:
            return "bug_fix"
    
    # Check for feature indicators
    for keyword in FEATURE_KEYWORDS:
        if keyword in msg_lower:
            return "feature_addition"
    
    return "unknown"


def compute_confidence(message: str, before: Optional[str], after: Optional[str]) -> float:
    """Compute confidence score for the extracted pattern."""
    confidence = 0.5  # Base confidence
    
    # Higher confidence if message contains clear keywords
    msg_lower = message.lower()
    if any(k in msg_lower for k in ["fix", "bug", "hotfix", "patch"]):
        confidence += 0.2
    if any(k in msg_lower for k in ["feat", "feature", "add", "implement"]):
        confidence += 0.15
    
    # Higher confidence if we have both before and after
    if before and after:
        confidence += 0.15
    elif before or after:
        confidence += 0.05
    
    # Higher confidence for substantial changes
    if before and after:
        content_len = max(len(before), len(after))
        if content_len > 100:
            confidence += 0.1
        if content_len > 500:
            confidence += 0.1
    
    return min(confidence, 1.0)


def generate_pattern_id(commit_hash: str, filepath: str) -> str:
    """Generate a unique pattern ID."""
    content = f"{commit_hash}:{filepath}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def extract_patterns(
    repo_path: str,
    output_path: str,
    since_date: Optional[str] = None
) -> int:
    """Extract patterns from git history and write to JSONL file."""
    
    print(f"Scanning repository: {repo_path}")
    
    # Get all commits
    commits = get_commit_messages(repo_path, since_date)
    print(f"Found {len(commits)} commits")
    
    if not commits:
        print("No commits found.", file=sys.stderr)
        return 0
    
    patterns_extracted = 0
    
    # Process each commit with progress bar
    iterator = tqdm(commits, desc="Extracting patterns") if tqdm else commits
    
    with open(output_path, 'w', encoding='utf-8') as outf:
        for commit in iterator:
            commit_hash = commit['hash']
            message = commit['message']
            author = commit['author']
            date = commit['date']
            
            # Infer problem type
            problem_type = infer_problem_type(message)
            
            # Skip if not a bug fix or feature
            if problem_type == "unknown":
                continue
            
            # Get changed files
            changed_files = get_changed_files(repo_path, commit_hash)
            
            for filepath in changed_files:
                # Skip binary files
                full_path = os.path.join(repo_path, filepath)
                if not os.path.exists(full_path):
                    continue
                
                if not is_text_file(filepath):
                    continue
                
                # Get diff
                before_content, after_content = get_file_diff(repo_path, commit_hash, filepath)
                
                # Skip if no meaningful change
                if before_content == after_content:
                    continue
                if not before_content and not after_content:
                    continue
                
                # Compute confidence
                confidence = compute_confidence(message, before_content, after_content)
                
                # Create pattern record
                pattern = {
                    "pattern_id": generate_pattern_id(commit_hash, filepath),
                    "problem_type": problem_type,
                    "before_code": before_content or "",
                    "after_code": after_content or "",
                    "commit_msg": message,
                    "author": author,
                    "date": date,
                    "confidence": round(confidence, 2)
                }
                
                # Write as JSONL
                outf.write(json.dumps(pattern, ensure_ascii=False) + '\n')
                patterns_extracted += 1
    
    print(f"\nExtracted {patterns_extracted} patterns to {output_path}")
    return patterns_extracted


def main():
    parser = argparse.ArgumentParser(
        description="Extract code patterns from Git history for training data"
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        required=True,
        help="Path to the Git repository"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSONL file path"
    )
    parser.add_argument(
        "--since-date",
        type=str,
        default=None,
        help="Only extract commits since this date (YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    
    # Validate repo path
    if not os.path.isdir(os.path.join(args.repo_path, '.git')):
        print(f"Error: {args.repo_path} is not a Git repository", file=sys.stderr)
        sys.exit(1)
    
    # Run extraction
    extract_patterns(args.repo_path, args.output, args.since_date)


if __name__ == "__main__":
    main()
