#!/usr/bin/env python3
"""
Extract patterns from Git commit histories for Stack 2.9 training.

This script analyzes git repositories to discover successful coding patterns,
common error fixes, tool usage workflows, and team collaboration patterns.
The extracted patterns can be used to enhance the Pattern Memory system.

Usage:
    python extract_patterns_from_git.py --repo /path/to/repo --output training-data/git_patterns.jsonl
    python extract_patterns_from_git.py --repo . --output ./patterns.jsonl --min-commits 10
"""

import os
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import re
from datetime import datetime
import hashlib

class GitPatternExtractor:
    """Extract training patterns from git commit histories."""
    
    def __init__(self, repo_path: str, min_commits: int = 5):
        self.repo_path = Path(repo_path)
        self.min_commits = min_commits
        self.patterns = []
        self.stats = defaultdict(int)
        
    def run_git_command(self, cmd: List[str]) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            return ""
        except subprocess.TimeoutExpired:
            print(f"Git command timed out: {cmd}")
            return ""
    
    def get_branches(self) -> List[str]:
        """Get all branches."""
        output = self.run_git_command(["branch", "-a"])
        branches = [b.strip().replace('* ', '') for b in output.split('\n') if b.strip()]
        return branches
    
    def get_commit_history(self, branch: str = "HEAD", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get detailed commit history with stats."""
        # Use pretty format to get: hash, author, date, subject, body
        fmt = "--pretty=format:%H|%an|%ad|%s|%b"
        cmd = ["log", branch, fmt, "--date=iso"]
        if limit:
            cmd.append(f"-{limit}")
        
        output = self.run_git_command(cmd)
        commits = []
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            parts = line.split('|', 4)
            if len(parts) == 5:
                commit_hash, author, date, subject, body = parts
                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "date": date,
                    "subject": subject,
                    "body": body,
                    "branch": branch
                })
        
        return commits
    
    def get_commit_stats(self, commit_hash: str) -> Dict[str, Any]:
        """Get statistics for a commit: files changed, insertions, deletions."""
        output = self.run_git_command(["show", "--stat", "--oneline", commit_hash])
        
        stats = {
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
            "file_types": Counter()
        }
        
        # Parse the --stat output
        for line in output.split('\n'):
            # Count file changes
            if '|' in line and ('+' in line or '-' in line):
                parts = line.split('|')
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    change_stats = parts[1].strip()
                    
                    stats["files_changed"] += 1
                    
                    # Extract file extension
                    if '.' in filename:
                        ext = filename.split('.')[-1].lower()
                        stats["file_types"][ext] += 1
                    
                    # Count insertions/deletions
                    if '+' in change_stats:
                        try:
                            ins = int(change_stats.split('+')[0].strip().split()[0])
                            stats["insertions"] += ins
                        except:
                            pass
                    if '-' in change_stats:
                        try:
                            dels = change_stats.split('-')[0].strip().split()[-1]
                            stats["deletions"] += int(dels)
                        except:
                            pass
        
        return stats
    
    def get_commit_diff(self, commit_hash: str) -> str:
        """Get the full diff for a commit."""
        return self.run_git_command(["show", commit_hash])
    
    def classify_commit(self, subject: str, body: str, files_changed: List[str]) -> str:
        """Classify the type of commit."""
        subject_lower = subject.lower()
        body_lower = body.lower()
        text = subject_lower + " " + body_lower
        
        # Keywords for classification
        patterns = {
            "bug_fix": ["fix", "bug", "issue", "error", "crash", "regression", "typo"],
            "feature": ["add", "implement", "create", "new", "support", "feature"],
            "refactor": ["refactor", "cleanup", "simplify", "reorganize", "rename"],
            "documentation": ["doc", "readme", "comment", "documentation"],
            "test": ["test", "spec", "fixture", "mock"],
            "security": ["security", "vulnerability", "exploit", "cve", "auth"],
            "performance": ["perf", "performance", "optimize", " faster", "speed"],
            "revert": ["revert"],
            "merge": ["merge"],
            "chore": ["chore", "bump", "update"]
        }
        
        # Check for merge commits
        if len(files_changed) == 0 and "merge" in subject_lower:
            return "merge"
        
        # Score each category
        scores = defaultdict(int)
        for category, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text:
                    scores[category] += 1
        
        # Get the highest scoring category
        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best
        
        return "other"
    
    def extract_code_snippets(self, diff: str, max_snippets: int = 3) -> List[Dict[str, Any]]:
        """Extract code changes from diff."""
        snippets = []
        current_file = None
        current_hunk = []
        in_hunk = False
        
        for line in diff.split('\n'):
            # File header
            if line.startswith('+++ b/') or line.startswith('--- a/'):
                if 'dev/null' not in line and 'index ' not in line:
                    current_file = line.replace('--- a/', '').replace('+++ b/', '').strip()
                continue
            
            # Hunk header
            if line.startswith('@@'):
                if current_file and current_hunk:
                    snippets.append({
                        "file": current_file,
                        "hunk": '\n'.join(current_hunk)
                    })
                current_hunk = []
                in_hunk = True
                continue
            
            # Added/removed lines
            if in_hunk and (line.startswith('+') or line.startswith('-')):
                current_hunk.append(line)
        
        # Don't forget last hunk
        if current_file and current_hunk and len(snippets) < max_snippets:
            snippets.append({
                "file": current_file,
                "hunk": '\n'.join(current_hunk)
            })
        
        return snippets[:max_snippets]
    
    def analyze_tool_patterns(self, diff: str, commit_message: str) -> Optional[Dict[str, Any]]:
        """Detect if this commit involves tool usage patterns (e.g., CLI commands, scripts)."""
        # Look for script/command changes
        tool_indicators = {
            "bash": [".sh", "#!/bin/bash", "#!/usr/bin/env bash"],
            "python": [".py", "#!/usr/bin/env python", "import ", "from "],
            "docker": ["Dockerfile", "docker-compose", "docker build"],
            "git": ["git commit", "git push", "git pull", "git branch"],
            "curl": ["curl ", "wget "],
            "npm": ["npm ", "package.json"],
            "pip": ["pip ", "requirements.txt"],
        }
        
        detected_tools = []
        for tool, patterns in tool_indicators.items():
            for pattern in patterns:
                if pattern.lower() in diff.lower() or pattern.lower() in commit_message.lower():
                    detected_tools.append(tool)
                    break
        
        if detected_tools:
            return {
                "tools": list(set(detected_tools)),
                "is_automation": True
            }
        return None
    
    def extract_pattern_from_commit(self, commit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a pattern from a single commit."""
        stats = self.get_commit_stats(commit["hash"])
        
        # Skip if too few files changed (likely merge commit or trivial)
        if stats["files_changed"] == 0:
            return None
        
        # Get the diff
        diff = self.get_commit_diff(commit["hash"])
        if not diff:
            return None
        
        # Classify the commit
        files_changed = []
        for line in diff.split('\n'):
            if line.startswith('+++ b/') or line.startswith('--- a/'):
                filename = line.replace('--- a/', '').replace('+++ b/', '').strip()
                if 'dev/null' not in filename and 'index ' not in filename:
                    files_changed.append(filename)
        
        commit_type = self.classify_commit(commit["subject"], commit["body"], files_changed)
        
        # Extract code snippets
        code_snippets = self.extract_code_snippets(diff)
        
        # Detect tool patterns
        tool_pattern = self.analyze_tool_patterns(diff, commit["subject"])
        
        # Build pattern entry
        pattern = {
            "type": "git_commit_pattern",
            "commit_hash": commit["hash"][:8],
            "commit_type": commit_type,
            "author": commit["author"],
            "date": commit["date"],
            "subject": commit["subject"],
            "stats": {
                "files_changed": stats["files_changed"],
                "insertions": stats["insertions"],
                "deletions": stats["deletions"],
                "file_types": dict(stats["file_types"])
            },
            "code_snippets": code_snippets,
            "tool_detection": tool_pattern,
            "pattern_id": hashlib.md5(f"{commit['hash']}{commit['subject']}".encode()).hexdigest()[:12]
        }
        
        # Add success indicators (conventional commits, passing tests, etc.)
        pattern["is_successful"] = self._is_successful_commit(commit, diff)
        
        return pattern
    
    def _is_successful_commit(self, commit: Dict[str, Any], diff: str) -> bool:
        """Heuristics to determine if a commit represents a successful change."""
        # Check for revert commits
        if commit["subject"].lower().startswith("revert"):
            return False
        
        # Check for "fix" keywords followed by non-breaking changes
        subject_lower = commit["subject"].lower()
        if any(kw in subject_lower for kw in ["fix", "resolve", "solve"]):
            return True
        
        # Check if it's a refactor that simplifies code (more deletions than additions)
        if "refactor" in subject_lower:
            # We'd need to parse the diff more precisely, but roughly:
            # if deletions > insertions, likely simplification
            pass
        
        # Assume most commits are successful unless they're clearly broken
        # (e.g., "WIP", "TODO", "broken", "temp")
        bad_words = ["wip", "todo", "broken", "temp", "hack", "quick fix"]
        if any(word in subject_lower for word in bad_words):
            return False
        
        return True
    
    def extract_all_patterns(self) -> List[Dict[str, Any]]:
        """Main extraction routine."""
        print(f"🔍 Analyzing repository: {self.repo_path}")
        
        # Check if it's a git repo
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
        
        branches = self.get_branches()
        print(f"   Found {len(branches)} branches")
        
        # Get commits from main/master branch first, then others
        main_branches = [b for b in branches if any(main in b for main in ['main', 'master', 'trunk'])]
        if not main_branches:
            main_branches = branches[:1]  # Just take first branch if no main
        
        all_commits = []
        for branch in main_branches[:3]:  # Limit to 3 branches to avoid overload
            print(f"   Processing branch: {branch}")
            commits = self.get_commit_history(branch, limit=100)  # Limit per branch
            print(f"      Found {len(commits)} commits")
            all_commits.extend(commits)
        
        # Deduplicate by hash
        seen_hashes = set()
        unique_commits = []
        for commit in all_commits:
            if commit["hash"] not in seen_hashes:
                seen_hashes.add(commit["hash"])
                unique_commits.append(commit)
        
        print(f"   Total unique commits: {len(unique_commits)}")
        
        # Extract patterns
        patterns = []
        for commit in unique_commits:
            try:
                pattern = self.extract_pattern_from_commit(commit)
                if pattern:
                    patterns.append(pattern)
                    self.stats[pattern["commit_type"]] += 1
            except Exception as e:
                print(f"   Warning: Failed to extract pattern from commit {commit['hash'][:8]}: {e}")
                continue
        
        print(f"\n✨ Extracted {len(patterns)} patterns")
        print("   By type:")
        for ptype, count in sorted(self.stats.items(), key=lambda x: -x[1]):
            print(f"      {ptype}: {count}")
        
        self.patterns = patterns
        return patterns
    
    def save_patterns(self, output_path: Path):
        """Save patterns to JSONL file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for pattern in self.patterns:
                f.write(json.dumps(pattern) + '\n')
        
        print(f"\n💾 Saved patterns to: {output_path}")
        
        # Also save a summary
        summary_path = output_path.with_name(output_path.stem + '_summary.json')
        summary = {
            "total_patterns": len(self.patterns),
            "by_type": dict(self.stats),
            "extraction_date": datetime.now().isoformat(),
            "repo": str(self.repo_path)
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📊 Saved summary to: {summary_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract patterns from Git commit histories for Stack 2.9 training."
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to git repository (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="training-data/git_patterns.jsonl",
        help="Output file path (JSONL format)"
    )
    parser.add_argument(
        "--min-commits",
        type=int,
        default=5,
        help="Minimum commits per branch to process (default: 5)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of commits to process (for testing)"
    )
    
    args = parser.parse_args()
    
    try:
        extractor = GitPatternExtractor(args.repo, min_commits=args.min_commits)
        
        if args.limit:
            # Override commit limit by modifying the method
            original_get_commit_history = extractor.get_commit_history
            def limited_get_commit_history(branch, limit=None):
                return original_get_commit_history(branch, limit=args.limit)
            extractor.get_commit_history = limited_get_commit_history
        
        patterns = extractor.extract_all_patterns()
        
        if patterns:
            extractor.save_patterns(Path(args.output))
            
            # Show sample pattern
            print("\n📋 Sample pattern:")
            sample = patterns[0]
            print(f"   Type: {sample['commit_type']}")
            print(f"   Subject: {sample['subject']}")
            print(f"   Files: {sample['stats']['files_changed']} changed")
            print(f"   Insertions: {sample['stats']['insertions']}, Deletions: {sample['stats']['deletions']}")
            if sample['tool_detection']:
                print(f"   Tools: {', '.join(sample['tool_detection']['tools'])}")
        else:
            print("\n⚠️  No patterns extracted. Try:")
            print("   - Checking that the repository has commit history")
            print("   - Increasing --limit or --min-commits")
            print("   - Using a repository with more substantial commits")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
