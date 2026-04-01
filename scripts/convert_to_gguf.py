#!/usr/bin/env python3
"""
GGUF Conversion Script for Stack 2.9 Model

Converts the fine-tuned Stack 2.9 model to GGUF format for Ollama.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def find_llama_cpp():
    """Find llama.cpp directory in common locations."""
    # Check common locations relative to this script
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent

    possible_paths = [
        workspace_root / "llama.cpp",
        workspace_root / "extensions" / "llama.cpp",
        Path.home() / "llama.cpp",
        Path("/usr/local/llama.cpp"),
    ]

    for path in possible_paths:
        if path.exists() and (path / "convert.py").exists():
            return path

    return None


def run_command(cmd, check=True):
    """Run a shell command and stream output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)

    if check and result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        sys.exit(1)

    return result


def convert_model(model_path, output_path, quantize_type="q4_0", llama_cpp_path=None):
    """
    Convert a HuggingFace model to GGUF format using llama.cpp's convert.py.

    Args:
        model_path: Path to the input model (HuggingFace format)
        output_path: Path where the GGUF file should be saved
        quantize_type: Quantization type (e.g., q4_0, q5_0, q8_0)
        llama_cpp_path: Path to llama.cpp directory (auto-detected if None)
    """
    model_path = Path(model_path).resolve()
    output_path = Path(output_path).resolve()

    # Validate input model exists
    if not model_path.exists():
        print(f"Error: Model directory not found: {model_path}")
        sys.exit(1)

    # Find llama.cpp if not provided
    if llama_cpp_path is None:
        llama_cpp_path = find_llama_cpp()
        if llama_cpp_path is None:
            print("Error: llama.cpp not found!")
            print("\nPlease install llama.cpp and ensure convert.py is available.")
            print("You can clone it with:")
            print("  git clone https://github.com/ggerganov/llama.cpp.git")
            print("\nOr specify the path manually:")
            print("  python convert_to_gguf.py --llama-cpp /path/to/llama.cpp")
            sys.exit(1)

    llama_cpp_path = Path(llama_cpp_path).resolve()
    convert_script = llama_cpp_path / "convert.py"

    if not convert_script.exists():
        print(f"Error: convert.py not found at {convert_script}")
        sys.exit(1)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Convert to intermediate GGUF (unquantized)
    print(f"\n=== Step 1: Converting to GGUF ===")
    temp_gguf = output_path.parent / f"{output_path.stem}_temp.gguf"

    convert_cmd = [
        sys.executable,
        str(convert_script),
        str(model_path),
        "--outfile", str(temp_gguf),
        "--outtype", "f16",  # Intermediate full precision
    ]

    run_command(convert_cmd)

    if not temp_gguf.exists():
        print(f"Error: Conversion failed, {temp_gguf} not created")
        sys.exit(1)

    # Step 2: Quantize the GGUF file (if not full precision)
    if quantize_type != "f16":
        print(f"\n=== Step 2: Applying quantization ({quantize_type}) ===")

        # llama.cpp quantize tool
        quantize_tool = llama_cpp_path / "quantize"

        # Try different possible names for quantize
        if not quantize_tool.exists():
            quantize_tool = llama_cpp_path / "build" / "bin" / "quantize"
            if not quantize_tool.exists():
                quantize_tool = llama_cpp_path / "build" / "quantize"

        if not quantize_tool.exists():
            print("Warning: quantize tool not found. Skipping quantization step.")
            print("You may need to build llama.cpp first:")
            print(f"  cd {llama_cpp_path} && make quantize")
            print("Using unquantized model as fallback.")
            final_gguf = temp_gguf
        else:
            run_command([
                str(quantize_tool),
                str(temp_gguf),
                str(output_path),
                quantize_type
            ])
            temp_gguf.unlink()  # Remove temp file
            final_gguf = output_path
    else:
        final_gguf = temp_gguf
        if final_gguf != output_path:
            temp_gguf.rename(output_path)

    # Step 3: Validate the GGUF file
    print(f"\n=== Step 3: Validating GGUF file ===")

    if not final_gguf.exists():
        print(f"Error: Final GGUF file not found: {final_gguf}")
        sys.exit(1)

    file_size = final_gguf.stat().st_size / (1024**3)
    print(f"✓ GGUF file created: {final_gguf}")
    print(f"  Size: {file_size:.2f} GB")
    print(f"  Quantization: {quantize_type}")

    # Step 4: Print Ollama import command
    print(f"\n=== Ollama Import Command ===")
    print(f"ollama import {output_path} --alias stack-2.9:7b")
    print("\nAfter importing, you can run the model with:")
    print(f"  ollama run stack-2.9:7b")

    print("\n✅ Conversion complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Stack 2.9 model to GGUF format for Ollama"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="./output/stack-2.9-7b-merged",
        help="Path to the merged model directory (default: ./output/stack-2.9-7b-merged)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./ollama_model/stack-2.9-7b.gguf",
        help="Output GGUF file path (default: ./ollama_model/stack-2.9-7b.gguf)"
    )
    parser.add_argument(
        "--qtype",
        type=str,
        default="q4_0",
        choices=["f16", "q4_0", "q5_0", "q8_0", "q2_K", "q3_K_S", "q3_K_M", "q3_K_L", "q4_K_S", "q4_K_M", "q5_K_S", "q5_K_M", "q6_K"],
        help="Quantization type (default: q4_0)"
    )
    parser.add_argument(
        "--llama-cpp",
        type=str,
        default=None,
        help="Path to llama.cpp directory (auto-detected if not provided)"
    )

    args = parser.parse_args()

    # Resolve paths relative to workspace root
    workspace_root = Path(__file__).parent.parent
    model_path = (workspace_root / args.model_dir).resolve()
    output_path = (workspace_root / args.output).resolve()

    print("=== GGUF Conversion for Stack 2.9 ===\n")
    print(f"Input model: {model_path}")
    print(f"Output: {output_path}")
    print(f"Quantization: {args.qtype}\n")

    convert_model(
        model_path=model_path,
        output_path=output_path,
        quantize_type=args.qtype,
        llama_cpp_path=args.llama_cpp
    )


if __name__ == "__main__":
    main()
