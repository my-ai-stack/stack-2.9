#!/usr/bin/env python3
"""
Stack 2.9 - CLI Entry Point
A complete CLI and agent interface showcasing Stack 2.9 capabilities.
"""

import os
import sys
import cmd
import json
import argparse
import asyncio
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent import create_agent, StackAgent
from .context import create_context_manager


# ============================================================================
# UTILITIES
# ============================================================================

def print_banner():
    """Print the Stack 2.9 banner."""
    banner = r"""
    ____                _           _         _    
   |  _ \ ___ _ __   __| |_ __ ___ (_)_ __   | | __
   | |_) / _ \ '_ \ / _` | '__/ _ \| | '_ \  | |/ /
   |  _ <  __/ | | | (_| | | | (_) | | | | | |   <
   |_| \_\___|_| |_|\__,_|_|  \___/|_|_| |_| |_|\_\
                                              
   Stack 2.9 CLI & Agent Interface
   """
    print(banner)


def print_colored(text: str, color: str = "white", bold: bool = False):
    """Print colored text."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    if bold:
        text = f"\033[1m{text}\033[0m"
    
    sys.stdout.write(colors.get(color, "white"))
    print(text)
    sys.stdout.write(colors["reset"])


def format_output(data: Any, format: str = "text") -> str:
    """Format output for display."""
    if format == "json":
        return json.dumps(data, indent=2)
    elif isinstance(data, dict):
        return "\n".join(f"  {k}: {v}" for k, v in data.items())
    elif isinstance(data, list):
        return "\n".join(f"  - {item}" for item in data)
    else:
        return str(data)


# ============================================================================
# MODE 1: INTERACTIVE CHAT
# ============================================================================

class ChatMode(cmd.Cmd):
    """Interactive chat mode with the agent."""
    
    intro = """
    Welcome to Stack 2.9 Interactive Chat!
    Type your queries or use commands:
      /tools    - List available tools
      /schema   - Show tool schemas
      /context  - Show current context
      /history  - Show conversation history
      /clear    - Clear chat history
      /exit     - Exit chat mode
      
    Just type your question or task to get started!
    """
    prompt = "\n[Stack]> "
    
    def __init__(self, agent: StackAgent):
        super().__init__()
        self.agent = agent
        self.history: List[Dict[str, Any]] = []
        self.show_tool_calls = False
        self.output_format = "text"
        self.voice_input = False
    
    def default(self, line: str):
        """Handle user input as a query to the agent."""
        if line.startswith('/'):
            return
        
        print_colored("\nThinking...", "cyan")
        
        try:
            response = self.agent.process(line)
            self.history.append({
                "query": line,
                "response": response.content,
                "tool_calls": [tc.tool_name for tc in response.tool_calls],
                "timestamp": "now"
            })
            
            # Display response
            print("\n" + "="*50)
            print_colored("Response:", "green", bold=True)
            print(response.content)
            
            # Show tool usage if enabled
            if self.show_tool_calls and response.tool_calls:
                print("\n" + "-"*50)
                print_colored("Tools Used:", "yellow")
                for tc in response.tool_calls:
                    status = "✓" if tc.success else "✗"
                    print(f"  {status} {tc.tool_name}")
                    if not tc.success and tc.error:
                        print(f"     Error: {tc.error}")
            
            if response.needs_clarification:
                print_colored(f"\nNote: {response.clarification_needed}", "yellow")
            
        except KeyboardInterrupt:
            print_colored("\nInterrupted.", "red")
        except Exception as e:
            print_colored(f"\nError: {e}", "red")
    
    def do_tools(self, arg):
        """List all available tools."""
        tools = self.agent.context_manager.session.tools_used
        if tools:
            print(f"\nUsed {len(tools)} tools this session:")
            for tool in set(tools):
                print(f"  - {tool}")
        else:
            print("\nNo tools used yet this session.")
    
    def do_schema(self, arg):
        """Show tool schemas for tool calling."""
        schemas = self.agent.get_schemas()
        print(f"\nTool Schemas ({len(schemas)} tools):")
        for schema in schemas[:10]:
            print(f"\n  {schema['name']}: {schema['description']}")
        print(f"\n  ... and {len(schemas) - 10} more")
    
    def do_context(self, arg):
        """Show current context."""
        context = self.agent.get_context()
        print("\n" + context)
    
    def do_history(self, arg):
        """Show conversation history."""
        print(f"\nChat History ({len(self.history)} messages):")
        for i, entry in enumerate(self.history[-10:], 1):
            print(f"\n{i}. Query: {entry['query'][:50]}...")
            print(f"   Tools: {', '.join(entry['tool_calls'])}")
    
    def do_clear(self, arg):
        """Clear chat history."""
        self.history.clear()
        self.agent.context_manager.session.messages.clear()
        print_colored("Chat history cleared.", "green")
    
    def do_voice(self, arg):
        """Toggle voice input."""
        self.voice_input = not self.voice_input
        status = "enabled" if self.voice_input else "disabled"
        print_colored(f"Voice input {status} (note: requires additional setup)", "cyan")
    
    def do_exit(self, arg):
        """Exit chat mode."""
        print_colored("Goodbye!", "green")
        return True
    
    def do_EOF(self, arg):
        """Handle Ctrl+D."""
        print()
        return self.do_exit(arg)
    
    def postcmd(self, stop: bool, line: str) -> bool:
        """Save session after each command."""
        return stop
    
    def run(self):
        """Run the chat loop."""
        print_banner()
        print(self.intro)
        
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")


# ============================================================================
# MODE 2: COMMAND EXECUTION
# ============================================================================

class CommandMode:
    """Execute single commands."""
    
    def __init__(self, agent: StackAgent):
        self.agent = agent
        self.context_manager = create_context_manager()
    
    def execute(
        self,
        query: str,
        output_file: Optional[str] = None,
        output_format: str = "text"
    ) -> str:
        """Execute a query and return result."""
        print(f"Executing: {query}")
        
        response = self.agent.process(query)
        
        result = format_output(response.content, output_format)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
            print(f"Output saved to: {output_file}")
        
        return result
    
    def execute_tools(
        self,
        tools: List[str],
        output_file: Optional[str] = None
    ) -> str:
        """Execute specific tools directly."""
        print(f"Executing tools: {', '.join(tools)}")
        
        response = self.agent.process_with_tools("", tools)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(response.content)
            print(f"Output saved to: {output_file}")
        
        return response.content


# ============================================================================
# MODE 3: VOICE INTERFACE (PLACEHOLDER)
# ============================================================================

class VoiceInterface:
    """Voice input/output interface (requires additional setup)."""
    
    def __init__(self):
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if voice dependencies are available."""
        try:
            import speech_recognition as sr
            import pyttsx3
            return True
        except ImportError:
            return False
    
    def listen(self) -> Optional[str]:
        """Listen for voice input."""
        if not self.available:
            print("Voice recognition not available. Install with: pip install SpeechRecognition pyttsx3 pyaudio")
            return None
        
        try:
            import speech_recognition as sr
            
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening... (speak now)")
                audio = r.listen(source, timeout=5)
                
            text = r.recognize_google(audio)
            print(f"Heard: {text}")
            return text
        except Exception as e:
            print(f"Voice error: {e}")
            return None
    
    def speak(self, text: str):
        """Speak text output."""
        if not self.available:
            print(f"(TTS not available): {text}")
            return
        
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")


# ============================================================================
# MAIN CLI
# ============================================================================

class StackCLI:
    """Main CLI entry point."""
    
    def __init__(self):
        self.agent = create_agent()
        self.chat_mode = ChatMode(self.agent)
        self.command_mode = CommandMode(self.agent)
        self.voice = VoiceInterface()
    
    def run_interactive(self):
        """Run interactive chat mode."""
        self.chat_mode.run()
    
    def run_command(self, query: str, out_file: Optional[str] = None, fmt: str = "text"):
        """Run a single command."""
        result = self.command_mode.execute(query, out_file, fmt)
        print(result)
        return result
    
    def run_tools(self, tools: List[str], out_file: Optional[str] = None):
        """Run specific tools."""
        result = self.command_mode.execute_tools(tools, out_file)
        print(result)
        return result

    def run_eval(self, benchmark: str, provider: str = 'ollama', model: str = None):
        """Run evaluation benchmarks."""
        print_colored(f"\n=== Running {benchmark} benchmark ===", "blue")

        import sys
        from pathlib import Path
        eval_dir = Path(__file__).parent.parent / "stack-2.9-eval"
        if eval_dir.exists():
            sys.path.insert(0, str(eval_dir))

        try:
            if benchmark == 'mbpp':
                from benchmarks.mbpp import MBPP
                b = MBPP(model_provider=provider, model_name=model)
            elif benchmark == 'human_eval':
                from benchmarks.human_eval import HumanEval
                b = HumanEval(model_provider=provider, model_name=model)
            elif benchmark == 'gsm8k':
                from benchmarks.gsm8k import GSM8K
                b = GSM8K(model_provider=provider, model_name=model)
            elif benchmark == 'all':
                from benchmarks.mbpp import MBPP
                from benchmarks.human_eval import HumanEval
                from benchmarks.gsm8k import GSM8K
                for name, Benchmark in [('MBPP', MBPP), ('HumanEval', HumanEval), ('GSM8K', GSM8K)]:
                    print_colored(f"\n--- {name} ---", "yellow")
                    b = Benchmark(model_provider=provider, model_name=model)
                    results = b.evaluate()
                    print(f"  Accuracy: {results['accuracy']*100:.1f}%")
                return

            results = b.evaluate()
            print_colored(f"\nResults:", "green")
            print(f"  Accuracy: {results['accuracy']*100:.1f}%")
            print(f"  Passed: {results['pass_at_1']}/{results['total_cases']}")
            print(f"  Model: {results['model']}")
        except Exception as e:
            print_colored(f"Error: {e}", "red")

    def run_patterns(self, action: str):
        """Manage learned patterns."""
        print_colored(f"\n=== Pattern Management ===", "blue")

        import sys
        from pathlib import Path
        train_dir = Path(__file__).parent.parent / "stack-2.9-training"
        if train_dir.exists():
            sys.path.insert(0, str(train_dir))

        try:
            from pattern_miner import PatternMiner
            miner = PatternMiner()

            if action == 'list':
                patterns = miner.get_relevant_patterns(limit=20)
                print_colored(f"\nStored Patterns:", "yellow")
                for p in patterns:
                    print(f"  [{p.pattern_type}] {p.code_snippet[:50]}...")
            elif action == 'stats':
                stats = miner.get_statistics()
                print_colored(f"\nStatistics:", "yellow")
                print(f"  Total Feedback: {stats['total_feedback']}")
                print(f"  Success Rate: {stats['success_rate']:.1%}")
                print(f"  Total Patterns: {stats['total_patterns']}")
        except Exception as e:
            print_colored(f"Error: {e}", "red")

    def run_voice(self):
        """Run voice mode loop."""
        if not self.voice.available:
            print_colored("Voice interface not available.", "red")
            return
        
        print_banner()
        print("Voice Mode - Say 'exit' to quit")
        
        try:
            while True:
                text = self.voice.listen()
                if not text:
                    continue
                
                if "exit" in text.lower():
                    print("Exiting...")
                    break
                
                # Process with agent
                response = self.agent.process(text)
                print(f"\nResponse: {response.content[:200]}")
                
                # Speak response
                self.voice.speak(response.content[:200])
                
        except KeyboardInterrupt:
            print("\nExiting...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stack 2.9 CLI and Agent Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Interactive chat mode
  %(prog)s -c "read README.md" # Execute single command
  %(prog)s -t read write       # Execute specific tools
  %(prog)s -v                  # Voice mode
        """
    )
    
    parser.add_argument(
        '-c', '--command',
        help="Execute a single query/command"
    )
    
    parser.add_argument(
        '-t', '--tools',
        nargs='+',
        help="Execute specific tools"
    )
    
    parser.add_argument(
        '-o', '--output',
        help="Output file for results"
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json'],
        default='text',
        help="Output format"
    )
    
    parser.add_argument(
        '-v', '--voice',
        action='store_true',
        help="Enable voice mode"
    )
    
    parser.add_argument(
        '-w', '--workspace',
        default="/Users/walidsobhi/.openclaw/workspace",
        help="Workspace path"
    )

    # Evaluation options
    parser.add_argument(
        '-e', '--eval',
        choices=['mbpp', 'human_eval', 'gsm8k', 'all'],
        help="Run evaluation benchmark"
    )

    parser.add_argument(
        '--eval-provider',
        default='ollama',
        choices=['ollama', 'openai', 'anthropic', 'together'],
        help="Model provider for evaluation"
    )

    parser.add_argument(
        '--eval-model',
        type=str,
        help="Model name for evaluation"
    )

    # Pattern management
    parser.add_argument(
        '--patterns',
        choices=['list', 'stats', 'clear'],
        help="Manage learned patterns"
    )

    # Training
    parser.add_argument(
        '--train',
        action='store_true',
        help="Run LoRA training"
    )

    args = parser.parse_args()
    
    try:
        # Create CLI with custom workspace if provided
        cli = StackCLI()

        # Handle evaluation
        if args.eval:
            cli.run_eval(args.eval, args.eval_provider, args.eval_model)
            return

        # Handle pattern management
        if args.patterns:
            cli.run_patterns(args.patterns)
            return

        # Handle training
        if args.train:
            cli.run_train()
            return

        if args.voice:
            cli.run_voice()
        elif args.tools:
            cli.run_tools(args.tools, args.output)
        elif args.command:
            exit(0 if cli.run_command(args.command, args.output, args.format) else 1)
        else:
            # Interactive mode
            cli.run_interactive()
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
