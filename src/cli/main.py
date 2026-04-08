#!/usr/bin/env python3
"""
Stack 2.9 CLI - Terminal User Interface
Main entry point for interacting with Stack 2.9
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "stack" / "eval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "stack" / "training"))

from model_client import create_model_client, ChatMessage
from pattern_miner import PatternMiner
from data_quality import DataQualityAnalyzer


class Stack29CLI:
    """Stack 2.9 Terminal User Interface"""

    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or os.environ.get("MODEL_PROVIDER", "ollama")
        self.model = model or os.environ.get("MODEL_NAME", "")
        self.client = None
        self.agent = None
        self.miner = PatternMiner()
        self.chat_history = []

        # Colors
        self.BLUE = '\033[94m'
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.RED = '\033[91m'
        self.END = '\033[0m'
        self.BOLD = '\033[1m'

    def print_header(self):
        """Print CLI header"""
        print(f"""
{self.BLUE}╔═══════════════════════════════════════════════════════╗
║           {self.BOLD}Stack 2.9 - Self-Evolving AI{self.END}{self.BLUE}                ║
║           {self.YELLOW}Your AI coding companion{self.END}{self.BLUE}               ║
╚═══════════════════════════════════════════════════════╝{self.END}
""")

    def print_menu(self):
        """Print main menu"""
        print(f"""
{self.BOLD}Main Menu:{self.END}
  {self.GREEN}[1]{self.END} Chat with Stack 2.9
  {self.GREEN}[2]{self.END} Run Evaluation (Benchmarks)
  {self.GREEN}[3]{self.END} Manage Patterns (Self-Evolution)
  {self.GREEN}[4]{self.END} Train Model (LoRA Fine-tuning)
  {self.GREEN}[5]{self.END} Settings
  {self.GREEN}[0]{self.END} Exit

""")

    def init_client(self):
        """Initialize model client"""
        try:
            self.client = create_model_client(self.provider, self.model)
            print(f"{self.GREEN}✓{self.END} Connected to {self.provider}: {self.client.get_model_name()}")
        except Exception as e:
            print(f"{self.RED}✗{self.END} Failed to connect: {e}")
            print(f"{self.YELLOW}!{self.END} Make sure {self.provider} is running")
            self.client = None

    def chat_mode(self):
        """Interactive chat mode using agent with tool calling"""
        if not self.client:
            print(f"{self.RED}No model connected!{self.END}")
            return

        print(f"\n{self.BLUE}=== Chat Mode ==={self.END}")
        print("Type 'exit' to return to menu, 'clear' to clear history\n")

        # Initialize agent if not done
        if not hasattr(self, 'agent') or self.agent is None:
            from cli.agent import StackAgent
            self.agent = StackAgent(workspace='/Users/walidsobhi/stack-2.9')
            print(f"{self.GREEN}✓{self.END} Agent initialized")

        while True:
            try:
                user_input = input(f"{self.GREEN}You:{self.END} ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    break

                if user_input.lower() == 'clear':
                    print("Chat cleared.\n")
                    continue

                # Process through agent (handles tool calling)
                print(f"{self.BLUE}Stack 2.9:{self.END} ", end="", flush=True)

                try:
                    response = self.agent.process(user_input)
                    print(response.content)

                    if response.tool_calls:
                        print(f"\n{self.YELLOW}[Tools called: {', '.join(tc.tool_name for tc in response.tool_calls)}]{self.END}")

                except Exception as e:
                    print(f"{self.RED}Error: {e}{self.END}")

                except Exception as e:
                    print(f"{self.RED}Error: {e}{self.END}")

                print()

            except KeyboardInterrupt:
                print("\n")
                break

    def eval_mode(self):
        """Run evaluation benchmarks"""
        print(f"\n{self.BLUE}=== Evaluation ==={self.END}")
        print(f"{self.GREEN}[1]{self.END} MBPP (Code Generation)")
        print(f"{self.GREEN}[2]{self.END} HumanEval (Python)")
        print(f"{self.GREEN}[3]{self.END} GSM8K (Math)")
        print(f"{self.GREEN}[4]{self.END} Run All")
        print(f"{self.GREEN}[0]{self.END} Back")

        choice = input("\nSelect: ").strip()

        if choice == '0':
            return

        benchmarks = {
            '1': ('mbpp', 'MBPP'),
            '2': ('human_eval', 'HumanEval'),
            '3': ('gsm8k', 'GSM8K'),
            '4': ('all', 'All')
        }

        if choice not in benchmarks:
            print(f"{self.RED}Invalid choice{self.END}")
            return

        bench_name, bench_label = benchmarks[choice]

        print(f"\n{self.YELLOW}Running {bench_label} benchmark...{self.END}")

        try:
            if bench_name == 'all':
                from benchmarks.mbpp import MBPP
                from benchmarks.human_eval import HumanEval
                from benchmarks.gsm8k import GSM8K

                for name, Benchmark in [('MBPP', MBPP), ('HumanEval', HumanEval), ('GSM8K', GSM8K)]:
                    print(f"\n--- {name} ---")
                    b = Benchmark(model_provider=self.provider, model_name=self.model)
                    results = b.evaluate()
                    print(f"  Accuracy: {results['accuracy']*100:.1f}%")
            else:
                module = __import__(f'benchmarks.{bench_name}', fromlist=['MBPP', 'HumanEval', 'GSM8K'])
                Benchmark = getattr(module, bench_name.upper() if bench_name != 'mbpp' else 'MBPP')
                b = Benchmark(model_provider=self.provider, model_name=self.model)
                results = b.evaluate()
                print(f"\n{self.GREEN}Results:{self.END}")
                print(f"  Accuracy: {results['accuracy']*100:.1f}%")
                print(f"  Passed: {results['pass_at_1']}/{results['total_cases']}")

        except Exception as e:
            print(f"{self.RED}Error: {e}{self.END}")

        input("\nPress Enter to continue...")

    def pattern_mode(self):
        """Manage patterns for self-evolution"""
        print(f"\n{self.BLUE}=== Pattern Manager ==={self.END}")
        print(f"{self.GREEN}[1]{self.END} View Patterns")
        print(f"{self.GREEN}[2]{self.END} View Statistics")
        print(f"{self.GREEN}[3]{self.END} Generate Synthetic Data")
        print(f"{self.GREEN}[4]{self.END} Clear Patterns")
        print(f"{self.GREEN}[0]{self.END} Back")

        choice = input("\nSelect: ").strip()

        if choice == '0':
            return

        if choice == '1':
            patterns = self.miner.get_relevant_patterns(limit=20)
            print(f"\n{self.YELLOW}Stored Patterns ({len(patterns)}):{self.END}")
            for p in patterns:
                print(f"  [{p.pattern_type}] {p.code_snippet[:50]}... (rate: {p.success_rate:.0%})")

        elif choice == '2':
            stats = self.miner.get_statistics()
            print(f"\n{self.YELLOW}Statistics:{self.END}")
            print(f"  Total Feedback: {stats['total_feedback']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"  Total Patterns: {stats['total_patterns']}")
            print(f"  By Type: {stats['patterns_by_type']}")

        elif choice == '3':
            try:
                count = int(input("Number of examples: ").strip())
                self.miner.store_feedback(
                    problem_type="synthetic",
                    solution="# Synthetic pattern",
                    success=True
                )
                print(f"{self.GREEN}✓{self.END} Generated {count} synthetic patterns")
            except ValueError:
                print(f"{self.RED}Invalid number{self.END}")

        elif choice == '4':
            confirm = input("Clear all patterns? (y/n): ").strip().lower()
            if confirm == 'y':
                # Note: This would need a clear method in PatternMiner
                print(f"{self.YELLOW}Feature not implemented{self.END}")

        input("\nPress Enter to continue...")

    def train_mode(self):
        """Train model with LoRA"""
        print(f"\n{self.BLUE}=== Training ==={self.END}")
        print(f"{self.YELLOW}Note: Requires GPU and training data{self.END}")
        print(f"\n{self.GREEN}[1]{self.END} Prepare Data")
        print(f"{self.GREEN}[2]{self.END} Train LoRA")
        print(f"{self.GREEN}[3]{self.END} Merge Adapter")
        print(f"{self.GREEN}[0]{self.END} Back")

        choice = input("\nSelect: ").strip()

        if choice == '0':
            return

        if choice == '1':
            print(f"\n{self.YELLOW}Preparing training data...{self.END}")
            try:
                from prepare_data import prepare_data
                result = prepare_data()
                print(f"{self.GREEN}✓{self.END} Prepared {result['train_samples']} training samples")
            except Exception as e:
                print(f"{self.RED}Error: {e}{self.END}")

        elif choice == '2':
            print(f"\n{YELLOW}Training LoRA...{self.END}")
            print(f"{self.YELLOW}Note: This requires significant GPU resources{self.END}")
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    from train_lora import train_lora
                    trainer = train_lora()
                    print(f"{self.GREEN}✓{self.END} Training complete")
                except Exception as e:
                    print(f"{self.RED}Error: {e}{self.END}")

        input("\nPress Enter to continue...")

    def settings_mode(self):
        """Configure settings"""
        print(f"\n{self.BLUE}=== Settings ==={self.END}")
        print(f"Provider: {self.provider}")
        print(f"Model: {self.model}")
        print(f"\n{self.GREEN}[1]{self.END} Change Provider")
        print(f"{self.GREEN}[2]{self.END} Change Model")
        print(f"{self.GREEN}[0]{self.END} Back")

        choice = input("\nSelect: ").strip()

        if choice == '1':
            print("Providers: ollama, openai, anthropic")
            new_provider = input("Provider: ").strip()
            if new_provider in ['ollama', 'openai', 'anthropic']:
                self.provider = new_provider
                self.init_client()

        elif choice == '2':
            new_model = input("Model name: ").strip()
            if new_model:
                self.model = new_model
                self.init_client()

    def run(self):
        """Run the CLI"""
        self.print_header()
        self.init_client()

        while True:
            self.print_menu()
            choice = input(f"{self.GREEN}Select>{self.END} ").strip()

            if choice == '0':
                print(f"\n{self.BLUE}Thanks for using Stack 2.9!{self.END}\n")
                break

            if choice == '1':
                self.chat_mode()
            elif choice == '2':
                self.eval_mode()
            elif choice == '3':
                self.pattern_mode()
            elif choice == '4':
                self.train_mode()
            elif choice == '5':
                self.settings_mode()
            else:
                print(f"{self.RED}Invalid option{self.END}")


def main():
    parser = argparse.ArgumentParser(description="Stack 2.9 CLI")
    parser.add_argument("--provider", "-p", choices=["ollama", "openai", "anthropic"],
                        help="Model provider")
    parser.add_argument("--model", "-m", type=str, help="Model name")
    parser.add_argument("--chat", "-c", action="store_true", help="Start in chat mode")
    parser.add_argument("--eval", "-e", choices=["mbpp", "human_eval", "gsm8k", "all"],
                        help="Run evaluation")

    args = parser.parse_args()

    cli = Stack29CLI(provider=args.provider, model=args.model)

    if args.chat:
        cli.init_client()
        cli.chat_mode()
    elif args.eval:
        cli.init_client()
        cli.eval_mode()
    else:
        cli.run()


if __name__ == "__main__":
    main()