#!/usr/bin/env python3
"""
Validate JSONL training data quality.
Checks:
- Required fields present
- tool_calls format valid
- No empty/invalid entries
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter


# Required top-level fields
REQUIRED_FIELDS = ["messages", "tools"]

# Required message fields
REQUIRED_MSG_FIELDS = ["role", "content"]

# Valid roles
VALID_ROLES = {"system", "user", "assistant", "tool"}

# Required message structure for tool conversations
MUST_HAVE_ROLES = ["user", "assistant"]


class ValidationError:
    def __init__(self, line_num: int, field: str, message: str, severity: str = "error"):
        self.line_num = line_num
        self.field = field
        self.message = message
        self.severity = severity  # error, warning, info
    
    def __repr__(self):
        return f"[{self.severity.upper()}] Line {self.line_num}: {self.field} - {self.message}"


class DataValidator:
    def __init__(self, strict: bool = False):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.stats = {
            "total_lines": 0,
            "valid_lines": 0,
            "lines_with_tools": 0,
            "tool_names": Counter(),
            "message_roles": Counter(),
        }
        self.strict = strict
    
    def validate_field_exists(self, data: Dict, field: str, line_num: int) -> bool:
        """Check if a required field exists."""
        if field not in data:
            self.errors.append(ValidationError(
                line_num, field, f"Missing required field: '{field}'"
            ))
            return False
        return True
    
    def validate_message_structure(self, msg: Dict, line_num: int, msg_idx: int) -> bool:
        """Validate a single message structure."""
        valid = True
        
        # Check required fields
        for field in REQUIRED_MSG_FIELDS:
            if field not in msg:
                self.errors.append(ValidationError(
                    line_num, f"messages[{msg_idx}]",
                    f"Missing required field: '{field}'"
                ))
                valid = False
        
        # Validate role
        role = msg.get("role")
        if role and role not in VALID_ROLES:
            self.errors.append(ValidationError(
                line_num, f"messages[{msg_idx}].role",
                f"Invalid role: '{role}'. Must be one of: {VALID_ROLES}"
            ))
            valid = False
        
        # Validate tool_calls structure
        if msg.get("tool_calls"):
            valid &= self._validate_tool_calls(msg["tool_calls"], line_num, msg_idx)
        
        # Validate tool result structure
        if role == "tool":
            if "tool_call_id" not in msg and "tool_call_id" not in str(msg):
                self.warnings.append(ValidationError(
                    line_num, f"messages[{msg_idx}]",
                    "Tool message missing tool_call_id",
                    severity="warning"
                ))
        
        return valid
    
    def _validate_tool_calls(self, tool_calls: Any, line_num: int, msg_idx: int) -> bool:
        """Validate tool_calls structure."""
        if not isinstance(tool_calls, list):
            self.errors.append(ValidationError(
                line_num, f"messages[{msg_idx}].tool_calls",
                f"tool_calls must be a list, got {type(tool_calls).__name__}"
            ))
            return False
        
        valid = True
        for tc_idx, tc in enumerate(tool_calls):
            if not isinstance(tc, dict):
                self.errors.append(ValidationError(
                    line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}]",
                    f"tool_call must be an object, got {type(tc).__name__}"
                ))
                valid = False
                continue
            
            # Check required tool_call fields
            if "function" not in tc:
                self.errors.append(ValidationError(
                    line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}]",
                    "Missing 'function' field in tool_call"
                ))
                valid = False
                continue
            
            func = tc.get("function", {})
            if not isinstance(func, dict):
                self.errors.append(ValidationError(
                    line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}].function",
                    f"function must be an object, got {type(func).__name__}"
                ))
                valid = False
                continue
            
            # Validate function.name
            if "name" not in func:
                self.errors.append(ValidationError(
                    line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}].function",
                    "Missing 'name' field in function"
                ))
                valid = False
            
            # Validate function.arguments
            if "arguments" in func:
                args = func["arguments"]
                if isinstance(args, str):
                    try:
                        json.loads(args)
                    except json.JSONDecodeError as e:
                        self.errors.append(ValidationError(
                            line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}].function.arguments",
                            f"Invalid JSON: {e}"
                        ))
                        valid = False
                elif not isinstance(args, (dict, list)):
                    self.errors.append(ValidationError(
                        line_num, f"messages[{msg_idx}].tool_calls[{tc_idx}].function.arguments",
                        f"arguments must be JSON string or object, got {type(args).__name__}"
                    ))
                    valid = False
        
        return valid
    
    def validate_example(self, data: Dict, line_num: int) -> bool:
        """Validate a single training example."""
        valid = True
        
        # Check required fields
        for field in REQUIRED_FIELDS:
            if not self.validate_field_exists(data, field, line_num):
                valid = False
        
        if not valid and self.strict:
            return False
        
        # Validate messages array
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            self.errors.append(ValidationError(
                line_num, "messages",
                f"messages must be an array, got {type(messages).__name__}"
            ))
            return False
        
        if len(messages) == 0:
            self.errors.append(ValidationError(
                line_num, "messages",
                "messages array is empty"
            ))
            valid = False
        
        # Validate each message
        has_user = False
        has_assistant = False
        for idx, msg in enumerate(messages):
            if self.validate_message_structure(msg, line_num, idx):
                role = msg.get("role")
                self.stats["message_roles"][role] += 1
                if role == "user":
                    has_user = True
                elif role == "assistant":
                    has_assistant = True
        
        # Warn if missing essential roles
        if not has_user:
            self.warnings.append(ValidationError(
                line_num, "messages",
                "No user message found",
                severity="warning"
            ))
        if not has_assistant:
            self.warnings.append(ValidationError(
                line_num, "messages",
                "No assistant message found",
                severity="warning"
            ))
        
        # Extract tool names for stats
        for msg in messages:
            if msg.get("tool_calls"):
                self.stats["lines_with_tools"] += 1
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    name = func.get("name", "unknown")
                    self.stats["tool_names"][name] += 1
                break
        
        return valid
    
    def validate_file(self, filepath: Path) -> Tuple[int, int]:
        """Validate an entire JSONL file."""
        print(f"Validating: {filepath}")
        print("-" * 50)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                self.stats["total_lines"] += 1
                
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    self.errors.append(ValidationError(
                        line_num, "JSON",
                        f"Invalid JSON: {e}"
                    ))
                    continue
                
                if self.validate_example(data, line_num):
                    self.stats["valid_lines"] += 1
        
        return len(self.errors), len(self.warnings)
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 50)
        print("VALIDATION REPORT")
        print("=" * 50)
        
        print(f"\n📊 Statistics:")
        print(f"   Total lines: {self.stats['total_lines']}")
        print(f"   Valid lines: {self.stats['valid_lines']}")
        print(f"   Valid率: {self.stats['valid_lines']/max(1,self.stats['total_lines'])*100:.1f}%")
        print(f"   Lines with tools: {self.stats['lines_with_tools']}")
        
        if self.stats["tool_names"]:
            print(f"\n🔧 Top tool names:")
            for name, count in self.stats["tool_names"].most_common(10):
                print(f"   - {name}: {count}")
        
        if self.stats["message_roles"]:
            print(f"\n💬 Message roles:")
            for role, count in self.stats["message_roles"].most_common():
                print(f"   - {role}: {count}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for err in self.errors[:20]:  # Show first 20
                print(f"   {err}")
            if len(self.errors) > 20:
                print(f"   ... and {len(self.errors) - 20} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warn in self.warnings[:10]:  # Show first 10
                print(f"   {warn}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more")
        
        if not self.errors and not self.warnings:
            print("\n✅ All checks passed!")
        
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Validate training data JSONL files")
    parser.add_argument("files", nargs="*", 
                        help="JSONL files to validate (default: training-data/*.jsonl)")
    parser.add_argument("--input", type=str,
                        default="training-data/tool_examples.jsonl",
                        help="Input JSONL file")
    parser.add_argument("--strict", action="store_true",
                        help="Fail on any missing required field")
    parser.add_argument("--ignore-warnings", action="store_true",
                        help="Only show errors, not warnings")
    
    args = parser.parse_args()
    
    # Determine files to validate
    files = []
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        input_path = Path(args.input)
        if input_path.exists():
            files = [input_path]
        else:
            # Try glob pattern
            data_dir = input_path.parent
            files = list(data_dir.glob("*.jsonl"))
    
    if not files:
        print("Error: No files to validate")
        return 1
    
    all_passed = True
    for filepath in files:
        validator = DataValidator(strict=args.strict)
        error_count, warn_count = validator.validate_file(filepath)
        
        if not args.ignore_warnings:
            passed = validator.print_report()
        else:
            passed = error_count == 0
            if error_count > 0:
                print(f"\n❌ {filepath}: {error_count} errors found")
        
        if not passed:
            all_passed = False
        print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
