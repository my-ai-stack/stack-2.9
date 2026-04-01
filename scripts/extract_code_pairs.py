#!/usr/bin/env python3
"""
Extract code-comment pairs from the src/ directory.
Pairs: function/class code + its documentation comment.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
import argparse

def extract_jsdoc_comments(content: str) -> List[Dict[str, Any]]:
    """Extract JSDoc comments and associated code from JS/TS files."""
    pairs = []

    # Pattern to match JSDoc comment block followed by code
    # Matches: /** ... */ followed by function/class/interface
    pattern = re.compile(
        r'/\*\*\s*(.*?)\s*\*/\s*'  # JSDoc comment
        r'(export\s+)?(async\s+)?(function|const|let|var|class|interface|type)\s+(\w+)',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        comment_lines = match.group(1).strip().split('\n')
        # Clean up comment markers
        comment = []
        for line in comment_lines:
            line = line.strip()
            if line.startswith('* '):
                line = line[2:]
            elif line.startswith('*'):
                line = line[1:]
            comment.append(line.strip())
        comment_text = ' '.join(comment).strip()

        code_start = match.end()
        # Extract the function signature or class definition (up to opening brace or newline)
        code_lines = []
        lines = content[code_start:].split('\n')
        for line in lines[:5]:  # Take first few lines
            code_lines.append(line)
            if line.strip().endswith('{') or line.strip().endswith('>'):
                break
        code = '\n'.join(code_lines).strip()

        if comment_text and code and len(code.split('\n')) >= 2:
            pairs.append({
                "code": code,
                "comment": comment_text,
                "type": match.group(3),  # function/class/interface
                "name": match.group(4)
            })

    return pairs

def extract_python_docstrings(content: str) -> List[Dict[str, Any]]:
    """Extract Python docstrings and associated code."""
    pairs = []

    # Pattern for triple-quoted docstring before function/class
    pattern = re.compile(
        r'''(?P<quote>''' + r'"""' + r'''|\'\'\')\s*(?P<doc>.*?)(?P=quote)\s*'''
        r'(?:@\w+\s+)*def\s+(\w+)|class\s+(\w+)',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        doc = match.group('doc').strip()
        func_name = match.group(3) or match.group(4)
        if func_name:
            # Get the signature line
            signature = content[match.end():].split('\n')[0].strip()
            code = f"def {func_name}{signature}" if 'def' in signature else f"class {func_name}{signature}"

            pairs.append({
                "code": code,
                "comment": doc,
                "type": "function" if 'def' in signature else "class",
                "name": func_name
            })

    return pairs

def extract_inline_comments(content: str, file_ext: str) -> List[Dict[str, Any]]:
    """Extract code block with preceding inline comment."""
    pairs = []

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Check for // comment or # comment
        if line.strip().startswith('//') or line.strip().startswith('#'):
            comment = line.strip()[2:].strip()
            # Look at next few lines for code
            code_lines = []
            j = i + 1
            while j < len(lines) and len(code_lines) < 5:
                next_line = lines[j].rstrip()
                if next_line.strip() and not next_line.strip().startswith('//') and not next_line.strip().startswith('#'):
                    code_lines.append(next_line)
                elif next_line.strip().startswith(('//', '#')):
                    break  # Another comment block
                j += 1

            if comment and code_lines:
                code = '\n'.join(code_lines)
                # Only keep if comment is meaningful (>5 words or contains specific keywords)
                if len(comment.split()) > 3 or any(kw in comment.lower() for kw in ['function', 'return', 'parameter', 'args', 'handle', 'process']):
                    pairs.append({
                        "code": code,
                        "comment": comment,
                        "type": "inline",
                        "name": None
                    })
                i = j  # Skip processed lines
            else:
                i += 1
        else:
            i += 1

    return pairs

def process_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single file and extract code-comment pairs."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

    pairs = []

    # Extract by file type
    if file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
        pairs.extend(extract_jsdoc_comments(content))
    elif file_path.suffix == '.py':
        pairs.extend(extract_python_docstrings(content))

    # Inline comments for all types
    pairs.extend(extract_inline_comments(content, file_path.suffix))

    return pairs

def walk_source_files(src_dir: Path) -> List[Path]:
    """Walk src/ directory and return all relevant source files."""
    extensions = ['.ts', '.tsx', '.js', '.jsx', '.py']
    files = []
    for ext in extensions:
        files.extend(src_dir.rglob(f'*{ext}'))
    return files

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-dir", type=str, default="src")
    parser.add_argument("--output", type=str, default="training-data/code-pairs/extended_pairs.json")
    parser.add_argument("--limit", type=int, default=10000, help="Maximum pairs to extract")
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    output_path = Path(args.output)

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return

    print(f"🔍 Scanning {src_dir} for source files...")
    files = walk_source_files(src_dir)
    print(f"   Found {len(files)} source files")

    all_pairs = []
    for file_path in files:
        pairs = process_file(file_path)
        if pairs:
            all_pairs.extend(pairs)
            print(f"   {file_path.name}: {len(pairs)} pairs", end='\r')

        if len(all_pairs) >= args.limit:
            break

    print(f"\n✨ Extracted {len(all_pairs)} code-comment pairs")

    # Deduplicate (by comment+code hash)
    seen = set()
    unique_pairs = []
    for pair in all_pairs:
        key = (pair['comment'][:100], pair['code'][:100])
        if key not in seen:
            seen.add(key)
            unique_pairs.append(pair)

    print(f"   After deduplication: {len(unique_pairs)} unique pairs")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(unique_pairs, f, indent=2)

    print(f"✅ Saved to: {output_path}")

    # Stats
    types = {}
    for pair in unique_pairs:
        t = pair.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    print("\n📊 By type:")
    for t, cnt in types.items():
        print(f"   {t}: {cnt}")

if __name__ == "__main__":
    main()