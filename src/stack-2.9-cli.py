#!/usr/bin/env python3
"""
Stack 2.9 - Terminal User Interface
Interactive CLI for chatting, evaluating, and training Stack 2.9
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

# Add eval and training to path - go up from src/ to project root, then into stack/
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "stack" / "eval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "stack" / "training"))
sys.path.insert(0, str(Path(__file__).parent.parent / "stack" / "eval" / "benchmarks"))

from model_client import create_model_client, ChatMessage
from benchmarks.mbpp import MBPP
from benchmarks.human_eval import HumanEval
from benchmarks.gsm8k import GSM8K
from pattern_miner import PatternMiner
from data_quality import DataQualityAnalyzer


@dataclass
class ChatMessage:
    """Chat message for display."""
    role: str
    content: str
    timestamp: str = ""


class Stack29TUI:
    """Terminal User Interface for Stack 2.9"""

    def __init__(self):
        self.client = None
        self.provider = os.environ.get("MODEL_PROVIDER", "ollama")
        self.model = os.environ.get("MODEL_NAME", "")
        self.chat_history: List[ChatMessage] = []
        self.pattern_miner = PatternMiner()

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print the header."""
        self.clear_screen()
        print("=" * 60)
        print("🤖 Stack 2.9 - Self-Evolving AI Coding Assistant")
        print("=" * 60)
        print(f"Provider: {self.provider} | Model: {self.model or 'default'}")
        print("-" * 60)

    def print_menu(self, options: List[str], title: str = "Menu"):
        """Print a menu with options."""
        print(f"\n📋 {title}")
        print("-" * 40)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print("-" * 40)

    def get_input(self, prompt: str = "> ") -> str:
        """Get user input."""
        return input(prompt).strip()

    def configure_provider(self):
        """Configure model provider."""
        self.print_header()
        print("\n🔧 Provider Configuration")
        print("-" * 40)
        print("Available providers:")
        print("  1. Ollama (local - recommended)")
        print("  2. OpenAI (API)")
        print("  3. Anthropic (API)")

        choice = self.get_input("Select provider (1-3): ")
        model_name = ""

        if choice == "1":
            self.provider = "ollama"
            model_name = self.get_input("Model name (default: qwen2.5-coder:32b): ")
            self.model = model_name or "qwen2.5-coder:32b"
        elif choice == "2":
            self.provider = "openai"
            model_name = self.get_input("Model name (default: gpt-4o): ")
            self.model = model_name or "gpt-4o"
            api_key = self.get_input("OpenAI API key: ")
            os.environ["OPENAI_API_KEY"] = api_key
        elif choice == "3":
            self.provider = "anthropic"
            model_name = self.get_input("Model name (default: claude-sonnet-4-20250514): ")
            self.model = model_name or "claude-sonnet-4-20250514"
            api_key = self.get_input("Anthropic API key: ")
            os.environ["ANTHROPIC_API_KEY"] = api_key
        else:
            print("Invalid choice!")
            return

        # Save to environment
        os.environ["MODEL_PROVIDER"] = self.provider
        os.environ["MODEL_NAME"] = self.model

        print(f"\n✓ Configured: {self.provider} / {self.model}")

    def init_client(self):
        """Initialize the model client."""
        try:
            self.client = create_model_client(self.provider, self.model)
            print(f"✓ Connected to {self.client.get_model_name()}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False

    def chat_mode(self):
        """Interactive chat mode."""
        self.print_header()
        print("\n💬 Chat Mode")
        print("Type 'exit' to return to menu, 'clear' to clear history")
        print("-" * 40)

        # Initialize client if needed
        if not self.client:
            if not self.init_client():
                return

        # System prompt
        system_msg = ChatMessage(
            role="system",
            content="You are Stack 2.9, a self-evolving AI coding assistant that learns from conversations.",
            timestamp="system"
        )
        messages = [system_msg]

        # Add relevant patterns to context
        patterns = self.pattern_miner.get_relevant_patterns(limit=3)
        if patterns:
            pattern_context = self.pattern_miner.generate_pattern_prompt(patterns)
            messages.append(ChatMessage(
                role="system",
                content=pattern_context,
                timestamp="system"
            ))

        while True:
            user_input = self.get_input("\n👤 You: ")
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                break
            if user_input.lower() == "clear":
                messages = [system_msg]
                self.print_header()
                print("\n💬 Chat Mode (cleared)")
                print("-" * 40)
                continue

            # Add user message
            messages.append(ChatMessage(role="user", content=user_input))

            # Generate response
            try:
                print("🤖 Stack: ", end="", flush=True)
                result = self.client.chat(
                    [ChatMessage(role=m.role, content=m.content) for m in messages],
                    temperature=0.7,
                    max_tokens=2048
                )
                print(result.text)

                # Add assistant response
                messages.append(ChatMessage(role="assistant", content=result.text))

                # Store feedback option
                print("\n[Options: s=store success, f=store failure, c=continue] ", end="")
                feedback = self.get_input()
                if feedback.lower() == "s":
                    # Store as successful pattern
                    self.pattern_miner.store_feedback(
                        problem_type="chat",
                        solution=result.text,
                        success=True
                    )
                    print("✓ Stored as successful pattern")
                elif feedback.lower() == "f":
                    self.pattern_miner.store_feedback(
                        problem_type="chat",
                        solution=user_input,
                        success=False,
                        error_message=result.text
                    )
                    print("✓ Stored as feedback for learning")

            except Exception as e:
                print(f"Error: {e}")

    def run_benchmark(self, benchmark_name: str):
        """Run a specific benchmark."""
        self.print_header()
        print(f"\n📊 Running {benchmark_name} Benchmark")
        print("-" * 40)

        # Initialize client if needed
        if not self.client:
            if not self.init_client():
                return

        if benchmark_name == "MBPP":
            benchmark = MBPP(
                model_provider=self.provider,
                model_name=self.model
            )
        elif benchmark_name == "HumanEval":
            benchmark = HumanEval(
                model_provider=self.provider,
                model_name=self.model
            )
        elif benchmark_name == "GSM8K":
            benchmark = GSM8K(
                model_provider=self.provider,
                model_name=self.model
            )
        else:
            print(f"Unknown benchmark: {benchmark_name}")
            return

        # Run evaluation
        results = benchmark.evaluate()

        # Display results
        print("\n" + "=" * 40)
        print(f"📊 {benchmark_name} Results")
        print("=" * 40)
        print(f"  Pass@1: {results['pass_at_1']}/{results['total_cases']}")
        print(f"  Accuracy: {results['accuracy']*100:.1f}%")
        print(f"  Model: {results['model']}")

        # Store feedback
        if results['accuracy'] > 0.5:
            self.pattern_miner.store_feedback(
                problem_type=benchmark_name.lower(),
                solution=f"accuracy={results['accuracy']}",
                success=True
            )

        self.get_input("\nPress Enter to continue...")

    def evaluate_menu(self):
        """Evaluation menu."""
        while True:
            self.print_header()
            self.print_menu([
                "Run MBPP Benchmark (Python coding)",
                "Run HumanEval Benchmark (Code generation)",
                "Run GSM8K Benchmark (Math reasoning)",
                "Run All Benchmarks",
                "Back to Main Menu"
            ], "Evaluation")

            choice = self.get_input("Select: ")

            if choice == "1":
                self.run_benchmark("MBPP")
            elif choice == "2":
                self.run_benchmark("HumanEval")
            elif choice == "3":
                self.run_benchmark("GSM8K")
            elif choice == "4":
                self.run_benchmark("MBPP")
                self.run_benchmark("HumanEval")
                self.run_benchmark("GSM8K")
            elif choice == "5":
                break

    def patterns_menu(self):
        """Pattern management menu."""
        while True:
            self.print_header()
            self.print_menu([
                "View Statistics",
                "List Patterns",
                "Generate Synthetic Data",
                "Back to Main Menu"
            ], "Pattern Mining")

            choice = self.get_input("Select: ")

            if choice == "1":
                stats = self.pattern_miner.get_statistics()
                print("\n📈 Pattern Statistics")
                print("-" * 40)
                print(f"  Total Feedback: {stats['total_feedback']}")
                print(f"  Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
                print(f"  Total Patterns: {stats['total_patterns']}")
                print(f"  Patterns by Type: {stats['patterns_by_type']}")
                self.get_input("\nPress Enter...")

            elif choice == "2":
                patterns = self.pattern_miner.get_relevant_patterns(limit=10)
                print("\n📝 Relevant Patterns")
                print("-" * 40)
                for p in patterns:
                    print(f"  [{p.pattern_type}] {p.code_snippet[:50]}...")
                    print(f"    Success Rate: {p.success_rate:.1%}")
                self.get_input("\nPress Enter...")

            elif choice == "3":
                n = self.get_input("Number of examples to generate: ")
                try:
                    n = int(n) if n else 50
                    from pattern_miner import create_synthetic_feedback
                    create_synthetic_feedback(Path("/tmp/synthetic.json"), n)
                    print(f"✓ Generated {n} synthetic examples")
                except Exception as e:
                    print(f"Error: {e}")
                self.get_input("\nPress Enter...")

            elif choice == "4":
                break

    def settings_menu(self):
        """Settings menu."""
        while True:
            self.print_header()
            self.print_menu([
                "Configure Model Provider",
                "View Current Settings",
                "Environment Variables",
                "Back to Main Menu"
            ], "Settings")

            choice = self.get_input("Select: ")

            if choice == "1":
                self.configure_provider()
                self.get_input("\nPress Enter...")
            elif choice == "2":
                print("\n⚙️ Current Settings")
                print("-" * 40)
                print(f"  Provider: {self.provider}")
                print(f"  Model: {self.model}")
                print(f"  Patterns Stored: {len(self.pattern_miner.patterns)}")
                self.get_input("\nPress Enter...")
            elif choice == "3":
                print("\n🔐 Environment Variables")
                print("-" * 40)
                print(f"  MODEL_PROVIDER: {os.environ.get('MODEL_PROVIDER', 'not set')}")
                print(f"  MODEL_NAME: {os.environ.get('MODEL_NAME', 'not set')}")
                print(f"  OPENAI_API_KEY: {'*' * 8 if os.environ.get('OPENAI_API_KEY') else 'not set'}")
                print(f"  ANTHROPIC_API_KEY: {'*' * 8 if os.environ.get('ANTHROPIC_API_KEY') else 'not set'}")
                self.get_input("\nPress Enter...")
            elif choice == "4":
                break

    def main_menu(self):
        """Main menu loop."""
        while True:
            self.print_header()
            self.print_menu([
                "💬 Chat with Stack 2.9",
                "📊 Run Evaluation",
                "🔍 Manage Patterns",
                "⚙️ Settings",
                "❌ Exit"
            ], "Main Menu")

            choice = self.get_input("Select: ")

            if choice == "1":
                self.chat_mode()
            elif choice == "2":
                self.evaluate_menu()
            elif choice == "3":
                self.patterns_menu()
            elif choice == "4":
                self.settings_menu()
            elif choice == "5":
                print("\n👋 Goodbye! Stack 2.9 will remember your patterns.")
                break

    def run(self):
        """Run the TUI."""
        # Initialize with defaults
        self.configure_provider()
        self.main_menu()


def main():
    """Main entry point."""
    tui = Stack29TUI()
    tui.run()


if __name__ == "__main__":
    main()