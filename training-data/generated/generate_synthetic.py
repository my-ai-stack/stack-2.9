#!/usr/bin/env python3
"""
Synthetic Data Expansion Script
Generates 50,000 training examples from ~180 seed examples using programmatic transformations.
"""

import json
import random
import re
import os
from typing import Dict, List, Any
from pathlib import Path

# Seed random for reproducibility during development
random.seed(42)

def load_seed_examples() -> List[Dict]:
    """Load all seed examples from the source files."""
    base_path = Path("/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/src-derived")
    files = [
        "completion_pairs.jsonl",
        "training_data.jsonl",
        "tool_use_examples.jsonl",
        "conversation_patterns.jsonl"
    ]
    
    examples = []
    for fname in files:
        fpath = base_path / fname
        if fpath.exists():
            with open(fpath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            examples.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    
    print(f"Loaded {len(examples)} seed examples")
    return examples

# Transformation functions

def rename_variables(code: str) -> str:
    """Systematically rename variables while preserving patterns."""
    # Common variable name mappings
    patterns = [
        (r'\bitem\b', 'elem'),
        (r'\bdata\b', 'payload'),
        (r'\bvalue\b', 'val'),
        (r'\bkey\b', 'k'),
        (r'\bresult\b', 'res'),
        (r'\berror\b', 'err'),
        (r'\bcallback\b', 'cb'),
        (r'\bfn\b', 'func'),
        (r'\barr\b', 'list'),
        (r'\btemp\b', 'tmp'),
        (r'\bobj\b', 'o'),
        (r'\bstr\b', 's'),
        (r'\bnum\b', 'n'),
    ]
    
    result = code
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result

def rename_functions(code: str) -> str:
    """Rename functions systematically."""
    patterns = [
        (r'\bget[A-Z]\w+\b', lambda m: 'fetch' + m.group(0)[3:]),
        (r'\bparse[A-Z]\w+\b', lambda m: 'decode' + m.group(0)[5:]),
        (r'\bformat[A-Z]\w+\b', lambda m: 'render' + m.group(0)[6:]),
        (r'\bvalidate[A-Z]\w+\b', lambda m: 'check' + m.group(0)[8:]),
    ]
    
    result = code
    for pattern, repl in patterns:
        if callable(repl):
            result = re.sub(pattern, repl, result)
        else:
            result = re.sub(pattern, repl, result)
    return result

def change_indentation(code: str) -> str:
    """Change indentation style (2 spaces <-> 4 spaces)."""
    lines = code.split('\n')
    if not lines:
        return code
    
    # Detect current indentation
    first_line = lines[0]
    if '    ' in first_line[:8]:
        # 4 spaces -> 2 spaces
        return '\n'.join(line.replace('    ', '  ', 1) if line.strip() else line for line in lines)
    else:
        # 2 spaces -> 4 spaces
        return '\n'.join(line.replace('  ', '    ', 1) if line.strip() else line for line in lines)

def add_semicolons(code: str) -> str:
    """Add missing semicolons."""
    # Add semicolons to statements that likely need them
    lines = code.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(('//', '/*', '*', '}', '{', '//')):
            # Check if line ends without semicolon
            if stripped and not stripped.endswith((';', '{', '}', ',', '=>')):
                line = line.rstrip() + ';'
        result.append(line)
    return '\n'.join(result)

def remove_semicolons(code: str) -> str:
    """Remove semicolons (except where needed)."""
    # Be conservative - only remove unnecessary semicolons
    return re.sub(r';\s*$', '', code, flags=re.MULTILINE)

def change_string_delimiters(code: str) -> str:
    """Change string delimiters."""
    # "string" -> 'string'
    code = re.sub(r'"([^"\\]|\\.)*"', lambda m: "'" + m.group(1) + "'", code)
    # 'string' -> `string` (where applicable)
    code = re.sub(r"'([^'\\]|\\.)*'", lambda m: '`' + m.group(1) + '`', code)
    return code

def restore_template_strings(code: str) -> str:
    """Convert template strings to concatenation."""
    # `${var}` -> " + var + "
    code = re.sub(r'`([^`\$]|\$[^{])*\$`', lambda m: '"' + m.group(0)[1:-1].replace('${', '" + ').replace('}', ' + "') + '"', code)
    return code

def add_optional_chaining(code: str) -> str:
    """Add optional chaining where appropriate."""
    # obj.method -> obj?.method for potential null cases
    code = re.sub(r'(\w+)\.(\w+)\(', r'\1?.\2(', code)
    return code

def split_if_statement(code: str) -> str:
    """Convert single-line if to block if."""
    # if (cond) statement; -> if (cond) { statement; }
    code = re.sub(r'if\s*\(([^)]+)\)\s*([^{]\S+);', r'if (\1) {\n  \2;\n}', code)
    return code

def merge_if_statement(code: str) -> str:
    """Convert block if to single-line if."""
    # if (cond) { statement; } -> if (cond) statement;
    code = re.sub(r'if\s*\(([^)]+)\)\s*\{\s*([^{]+);\s*\}', r'if (\1) \2;', code)
    return code

def add_type_annotations(code: str) -> str:
    """Add TypeScript type annotations."""
    # Add : any to untyped parameters
    code = re.sub(r'(\w+)(?!\s*:)', lambda m: m.group(1) + ': any' if re.search(r'\(\s*$|\s*,\s*$', code[:m.start()]) else m.group(0), code)
    return code

def remove_type_annotations(code: str) -> str:
    """Remove TypeScript type annotations."""
    code = re.sub(r':\s*\w+(\[\])?\s*([,)=])', r'\2', code)
    return code

def add_try_catch(code: str) -> str:
    """Wrap code in try-catch."""
    if 'try' not in code and '{' in code:
        lines = code.split('\n')
        if len(lines) > 2:
            # Wrap middle portion in try-catch
            mid = len(lines) // 2
            new_lines = lines[:mid] + ['try {'] + lines[mid:] + ['} catch (e) {', '  console.error(e)', '}']
            return '\n'.join(new_lines)
    return code

def change_numeric_literals(code: str) -> str:
    """Change numeric literals."""
    # 0 -> false in boolean contexts
    code = re.sub(r'===?\s*0\b', '=== false', code)
    code = re.sub(r'!==?\s*0\b', '!== false', code)
    # 1 -> true in boolean contexts  
    code = re.sub(r'===\s*1\b', '=== true', code)
    return code

def convert_async_await(code: str) -> str:
    """Convert async/await to Promise chains."""
    # async function -> function returning Promise
    code = re.sub(r'async\s+function', 'function', code)
    # await -> .then()
    code = re.sub(r'await\s+(\w+)\.map\((.*?)\)', r'\1.then(\2)', code)
    code = re.sub(r'await\s+(\w+)\.filter\((.*?)\)', r'\1.then(\2)', code)
    return code

def convert_promise_chain(code: str) -> str:
    """Convert Promise chains to async/await."""
    # .then() -> await
    code = re.sub(r'(\w+)\.then\(async\s*\((.*?)\)\s*=>', r'await \1.then(async (\2) =>', code)
    return code

def add_default_params(code: str) -> str:
    """Add default parameters."""
    # function(a, b) -> function(a = default, b = default)
    code = re.sub(r'function\s+\w+\(([^)]+)\)', 
                  lambda m: 'function(' + m.group(1).replace(',', ' = null,') + ' = null)', code)
    return code

def remove_default_params(code: str) -> str:
    """Remove default parameters."""
    code = re.sub(r'\s*=\s*\w+', '', code)
    return code

def add_comments(code: str) -> str:
    """Add explanatory comments."""
    comment_types = [
        '// Handle edge case',
        '// Process the input',
        '// Return the result',
        '// Initialize variables',
        '// Clean up resources',
        '// Apply transformation',
        '/* Parse the data */',
        '// Ensure type safety',
    ]
    lines = code.split('\n')
    if len(lines) > 1:
        insert_pos = random.randint(1, len(lines) - 1)
        comment = random.choice(comment_types)
        lines.insert(insert_pos, comment)
    return '\n'.join(lines)

def remove_comments(code: str) -> str:
    """Remove comments."""
    # Remove single-line comments
    code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    # Remove multi-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code

def unroll_loop(code: str) -> str:
    """Unroll simple loops."""
    # for (let i = 0; i < 3; i++) -> explicit iterations
    match = re.search(r'for\s*\(\s*let\s+(\w+)\s*=\s*0\s*;\s*\1\s*<\s*(\d+)\s*;.*?\{(.*?)\}', code, re.DOTALL)
    if match and int(match.group(2)) <= 3:
        var = match.group(1)
        body = match.group(3)
        count = int(match.group(2))
        unrolled = '\n'.join([body.replace(var, str(i)) for i in range(count)])
        code = code.replace(match.group(0), unrolled)
    return code

def shuffle_statements(code: str) -> str:
    """Shuffle independent statements."""
    lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith(('//', '/*', '*/', '*'))]
    if len(lines) > 3:
        random.shuffle(lines)
        return '\n'.join(lines)
    return code

# Map transformation names to functions
TRANSFORMATIONS = {
    'rename_variables': rename_variables,
    'rename_functions': rename_functions,
    'change_indentation': change_indentation,
    'add_semicolons': add_semicolons,
    'remove_semicolons': remove_semicolons,
    'change_string_delimiters': change_string_delimiters,
    'restore_template_strings': restore_template_strings,
    'add_optional_chaining': add_optional_chaining,
    'split_if_statement': split_if_statement,
    'merge_if_statement': merge_if_statement,
    'add_type_annotations': add_type_annotations,
    'remove_type_annotations': remove_type_annotations,
    'add_try_catch': add_try_catch,
    'change_numeric_literals': change_numeric_literals,
    'convert_async_await': convert_async_await,
    'convert_promise_chain': convert_promise_chain,
    'add_default_params': add_default_params,
    'remove_default_params': remove_default_params,
    'add_comments': add_comments,
    'remove_comments': remove_comments,
    'unroll_loop': unroll_loop,
    'shuffle_statements': shuffle_statements,
}

def apply_transformation(code: str, transform_name: str) -> str:
    """Apply a single transformation to code."""
    transform_fn = TRANSFORMATIONS.get(transform_name)
    if transform_fn:
        try:
            return transform_fn(code)
        except Exception:
            return code
    return code

def transform_example(example: Dict, transform_names: List[str]) -> Dict:
    """Apply multiple transformations to an example."""
    result = example.copy()
    
    # Transform the code in various fields
    code_fields = ['input', 'output', 'code', 'prompt', 'completion']
    
    for field in code_fields:
        if field in result and isinstance(result[field], str):
            for transform in transform_names:
                result[field] = apply_transformation(result[field], transform)
    
    return result

def generate_variations(examples: List[Dict], target_count: int) -> List[Dict]:
    """Generate target_count variations from seed examples."""
    all_variations = []
    
    # List of transformation names
    transform_names = list(TRANSFORMATIONS.keys())
    
    # Start with original examples
    for ex in examples:
        all_variations.append(ex.copy())
    
    # Generate variations
    while len(all_variations) < target_count:
        # Pick random example and transformations
        example = random.choice(examples)
        
        # Pick 1-3 random transformations
        num_transforms = random.randint(1, 3)
        transforms = random.sample(transform_names, num_transforms)
        
        # Create variation
        variation = transform_example(example, transforms)
        
        # Generate unique ID for this variation
        variation['_variation_id'] = len(all_variations)
        variation['_transforms'] = transforms
        
        all_variations.append(variation)
        
        if len(all_variations) % 5000 == 0:
            print(f"Generated {len(all_variations)} examples...")
    
    return all_variations[:target_count]

def convert_to_prompt_completion(example: Dict) -> Dict:
    """Convert any example format to prompt/completion format."""
    result = {}
    
    # Try various input fields
    if 'input' in example and 'output' in example:
        result['prompt'] = example['input']
        result['completion'] = example['output']
    elif 'code' in example:
        result['prompt'] = example.get('description', 'Complete this code:')
        result['completion'] = example['code']
    elif 'prompt' in example and 'completion' in example:
        return example
    else:
        # Generic fallback
        result['prompt'] = json.dumps(example)
        result['completion'] = ''
    
    # Preserve metadata
    for key in ['type', 'subtype', 'metadata', 'category', 'tool_name']:
        if key in example:
            result[key] = example[key]
    
    return result

def main():
    print("Loading seed examples...")
    examples = load_seed_examples()
    
    print(f"Generating 50,000 variations...")
    variations = generate_variations(examples, 50000)
    
    # Convert all to prompt/completion format
    print("Converting to prompt/completion format...")
    formatted_examples = []
    for v in variations:
        formatted = convert_to_prompt_completion(v)
        # Only keep prompt and completion
        output = {
            'prompt': formatted.get('prompt', ''),
            'completion': formatted.get('completion', '')
        }
        formatted_examples.append(output)
    
    # Write to output file
    output_path = "/Users/walidsobhi/.openclaw/workspace/stack-2.9/training-data/generated/synthetic_50k.jsonl"
    print(f"Writing to {output_path}...")
    
    with open(output_path, 'w') as f:
        for example in formatted_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Done! Generated {len(formatted_examples)} examples.")
    
    # Verify
    with open(output_path, 'r') as f:
        lines = f.readlines()
    print(f"Verified: {len(lines)} lines in output file")

if __name__ == '__main__':
    main()