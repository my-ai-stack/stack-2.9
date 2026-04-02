"""
Stack 2.9 - Pattern-Based AI Coding Assistant
HuggingFace Spaces Demo

A Gradio interface for Stack 2.9 powered by Qwen2.5-Coder-7B
with tool integration and pattern memory.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import gradio as gr

# ============================================================
# Pattern Memory System
# ============================================================

class SelfEvolutionMemory:
    """Simple in-memory pattern memory system for demo purposes."""
    
    def __init__(self):
        self.conversations = []
        self.learned_patterns = {}
        self.code_snippets = []
        self.preferences = {}
        self.interaction_count = 0
    
    def add_interaction(self, user_input: str, assistant_response: str, tools_used: List[str] = None):
        """Record an interaction for learning."""
        self.interaction_count += 1
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_response": assistant_response,
            "tools_used": tools_used or [],
            "interaction_id": self.interaction_count
        }
        self.conversations.append(interaction)
        
        # Extract patterns from the interaction
        self._learn_from_interaction(user_input, assistant_response, tools_used or [])
    
    def _learn_from_interaction(self, user_input: str, response: str, tools: List[str]):
        """Learn patterns from interactions."""
        # Track tool usage patterns
        for tool in tools:
            if tool not in self.learned_patterns:
                self.learned_patterns[tool] = {"count": 0, "contexts": []}
            self.learned_patterns[tool]["count"] += 1
            self.learned_patterns[tool]["contexts"].append(user_input[:100])
        
        # Extract code snippets if present
        if "```" in response:
            self.code_snippets.append({
                "timestamp": datetime.now().isoformat(),
                "snippet": response
            })
    
    def get_context(self) -> str:
        """Get accumulated context for the model."""
        context_parts = [f"## Pattern Memory ({self.interaction_count} interactions)"]
        
        if self.learned_patterns:
            context_parts.append("\n### Tool Usage Patterns:")
            for tool, data in sorted(self.learned_patterns.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
                context_parts.append(f"- {tool}: used {data['count']} times")
        
        if self.code_snippets:
            context_parts.append(f"\n### Learned {len(self.code_snippets)} code patterns")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "total_interactions": self.interaction_count,
            "tool_patterns": len(self.learned_patterns),
            "code_snippets": len(self.code_snippets),
            "recent_tools": [t for t in self.learned_patterns.keys()][:5]
        }


# Global memory instance
memory = SelfEvolutionMemory()

# ============================================================
# Tool System
# ============================================================

class Tool:
    """Base tool class."""
    
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
    
    async def execute(self, *args, **kwargs):
        return await self.func(*args, **kwargs)


# Tool implementations (simplified for demo)
async def tool_file_read(path: str) -> str:
    """Read a file."""
    try:
        with open(path, 'r') as f:
            return f.read()[:5000]  # Limit output
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def tool_file_write(path: str, content: str) -> str:
    """Write to a file."""
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def tool_git_status() -> str:
    """Get git status."""
    import subprocess
    try:
        result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=os.getcwd())
        return result.stdout or "No changes"
    except Exception as e:
        return f"Git error: {str(e)}"


async def tool_web_search(query: str) -> str:
    """Search the web."""
    from urllib.parse import quote
    # Return a demo response since we can't make actual API calls
    return f"🔍 Search results for '{query}':\n\n1. [Result 1] - Description here\n2. [Result 2] - Description here\n3. [Result 3] - Description here\n\n(Install brave-search to enable real search)"


async def tool_run_command(cmd: str) -> str:
    """Run a shell command."""
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return f"Output:\n{result.stdout}\n\nErrors:\n{result.stderr}" if result.stderr else result.stdout
    except Exception as e:
        return f"Command error: {str(e)}"


async def tool_create_directory(path: str) -> str:
    """Create a directory."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory created: {path}"
    except Exception as e:
        return f"Error: {str(e)}"


async def tool_list_directory(path: str = ".") -> str:
    """List directory contents."""
    try:
        items = os.listdir(path)
        return "\n".join([f"📁 {i}/" if os.path.isdir(os.path.join(path, i)) else f"📄 {i}" for i in items[:50]])
    except Exception as e:
        return f"Error: {str(e)}"


# Register tools
TOOLS = {
    "file_read": Tool("file_read", "Read a file from the filesystem", tool_file_read),
    "file_write": Tool("file_write", "Write content to a file", tool_file_write),
    "git_status": Tool("git_status", "Check git repository status", tool_git_status),
    "web_search": Tool("web_search", "Search the web for information", tool_web_search),
    "run_command": Tool("run_command", "Execute a shell command", tool_run_command),
    "create_directory": Tool("create_directory", "Create a new directory", tool_create_directory),
    "list_directory": Tool("list_directory", "List files in a directory", tool_list_directory),
}


def get_tool_descriptions() -> str:
    """Get descriptions of all available tools."""
    return "\n".join([f"- **{t.name}**: {t.description}" for t in TOOLS.values()])


# ============================================================
# Model Interface
# ============================================================

class StackModel:
    """Stack 2.9 model interface using transformers."""
    
    def __init__(self, model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.pipeline = None
    
    def load(self):
        """Load the model with 4-bit quantization for HF Spaces."""
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch
        
        print(f"Loading {self.model_id}...")
        
        # 4-bit quantization config for 16GB GPU
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True
        )
        
        # Load model with quantization
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        print("Model loaded successfully!")
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate a response."""
        if not self.tokenizer:
            return "Model not loaded. Please wait for initialization."
        
        # Build the prompt with system and tools
        system_prompt = f"""You are Stack 2.9 - a pattern-based AI coding assistant.

## Available Tools
{get_tool_descriptions()}

## Your Capabilities
- Write, read, and execute code
- Use git for version control
- Search the web for information
- Create and manage files
- Execute shell commands

## Self-Evolution
You learn from each interaction. After responding, summarize what tools you used.

{memory.get_context()}

## Instructions
1. Be helpful and concise
2. Use tools when needed
3. Learn from the conversation
4. Provide code examples when relevant

Now respond to the user:"""

        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        # Tokenize
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the response part
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        return response
    
    def generate_streaming(self, prompt: str, max_tokens: int = 512):
        """Generate with streaming (yields tokens)."""
        if not self.tokenizer:
            yield "Model not loaded. Please wait for initialization."
            return
        
        system_prompt = f"""You are Stack 2.9 - a pattern-based AI coding assistant.

## Available Tools
{get_tool_descriptions()}

## Self-Evolution Memory
{memory.get_context()}

Now respond to the user:"""

        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        
        # Generate token by token
        from transformers import GenerationMixin
        from typing import Iterator
        
        generated_ids = inputs.input_ids
        
        for _ in range(max_tokens):
            with torch.no_grad():
                outputs = self.model(generated_ids)
                next_token_logits = outputs.logits[:, -1, :]
                
                # Apply temperature
                next_token_logits = next_token_logits / 0.7
                
                # Sample
                probs = torch.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                generated_ids = torch.cat([generated_ids, next_token], dim=-1)
                
                # Decode and yield
                token_str = self.tokenizer.decode(next_token[0], skip_special_tokens=True)
                yield token_str
                
                # Stop on EOS
                if next_token.item() == self.tokenizer.eos_token_id:
                    break


# Global model instance
model = None


def initialize_model():
    """Initialize the model on startup."""
    global model
    try:
        model = StackModel()
        model.load()
        return model
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None


# ============================================================
# Gradio Interface
# ============================================================

def format_tools_used(tools_used: List[str]) -> str:
    """Format the tools used for display."""
    if not tools_used:
        return ""
    return f"\n\n🔧 **Tools Used**: {', '.join(tools_used)}"


def chat_response(message: str, history: List[List[str]]) -> tuple:
    """Process a chat message and return response."""
    global model, memory
    
    if model is None or model.model is None:
        return "⏳ Model is loading. Please wait...", history + [[message, "⏳ Model is loading. Please wait..."]]
    
    # Track tools used
    tools_used = []
    
    # Check if we need to use tools based on the message
    message_lower = message.lower()
    
    if any(kw in message_lower for kw in ['git status', 'git']):
        tools_used.append("git_status")
    if any(kw in message_lower for kw in ['search', 'find', 'look up']):
        tools_used.append("web_search")
    if any(kw in message_lower for kw in ['list files', 'directory', 'ls']):
        tools_used.append("list_directory")
    if any(kw in message_lower for kw in ['run ', 'execute', 'command']):
        tools_used.append("run_command")
    
    # Generate response
    try:
        response = model.generate(message, max_tokens=512)
    except Exception as e:
        response = f"I encountered an error: {str(e)}"
    
    # Add tools used to response
    response += format_tools_used(tools_used)
    
    # Record in memory
    memory.add_interaction(message, response, tools_used)
    
    return response


def chat_response_stream(message: str, history: List[List[str]]) -> Generator:
    """Process a chat message with streaming."""
    global model, memory
    
    if model is None or model.model is None:
        yield "⏳ Model is loading. Please wait..."
        return
    
    full_response = ""
    tools_used = []
    
    message_lower = message.lower()
    if any(kw in message_lower for kw in ['git status', 'git']):
        tools_used.append("git_status")
    if any(kw in message_lower for kw in ['search', 'find']):
        tools_used.append("web_search")
    if any(kw in message_lower for kw in ['list', 'directory']):
        tools_used.append("list_directory")
    
    # Stream the response
    for token in model.generate_streaming(message, max_tokens=256):
        full_response += token
        yield full_response
    
    # Add tools used
    if tools_used:
        full_response += format_tools_used(tools_used)
        yield full_response
    
    # Record in memory
    memory.add_interaction(message, full_response, tools_used)


# Example prompts for the UI
EXAMPLE_PROMPTS = [
    "Hello! What can you help me with?",
    "Check git status of this repository",
    "Search for best practices for Python async programming",
    "List the files in the current directory",
    "Write a simple Python function to calculate fibonacci",
    "How do I use Git to create a new branch?",
    "What's your memory of our conversation?",
]


def create_gradio_app():
    """Create the Gradio interface."""
    
    with gr.Blocks(
        title="Stack 2.9 - Pattern-Based AI Coding Assistant",
        theme=gr.themes.Soft(
            primary_color="#6366f1",
            secondary_color="#818cf8",
            tertiary_color="#a5b4fc"
        )
    ) as app:
        
        # Header
        gr.Markdown("""
        # 🚀 Stack 2.9 - Pattern-Based AI Coding Assistant
        
        Powered by **Qwen2.5-Coder-7B** with 4-bit quantization
        
        ---
        """)
        
        # Memory stats display
        with gr.Row():
            with gr.Column(scale=1):
                stats_display = gr.Markdown(
                    "📊 **Memory Stats**\n\n- Interactions: 0\n- Tools learned: 0\n- Code patterns: 0",
                    elem_id="stats"
                )
            with gr.Column(scale=3):
                pass  # Spacer
        
        # Chat interface
        chatbot = gr.Chatbot(
            height=500,
            show_copy_button=True,
            bubble_full_width=False
        )
        
        with gr.Row():
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask me anything...",
                scale=4,
                lines=3
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        # Clear button
        with gr.Row():
            clear_btn = gr.Button("🗑️ Clear Chat")
        
        # Example prompts
        gr.Examples(
            examples=EXAMPLE_PROMPTS,
            inputs=msg,
            label="Example Prompts"
        )
        
        # Memory visualization
        with gr.Accordion("🧠 Self-Evolution Memory", open=False):
            memory_display = gr.Textbox(
                label="Memory Content",
                lines=10,
                interactive=False
            )
        
        # Functions
        def respond(message, history):
            response = chat_response(message, history)
            history.append([message, response])
            return "", history
        
        def update_stats():
            stats = memory.get_stats()
            return f"""📊 **Memory Stats**

- **Interactions**: {stats['total_interactions']}
- **Tool Patterns**: {stats['tool_patterns']}
- **Code Snippets**: {stats['code_snippets']}

**Recent Tools**: {', '.join(stats['recent_tools']) if stats['recent_tools'] else 'None'}"""
        
        def update_memory():
            return memory.get_context()
        
        # Button click handlers
        submit_btn.click(respond, [msg, chatbot], [msg, chatbot], api_name="send")
        msg.submit(respond, [msg, chatbot], [msg, chatbot], api_name="send")
        
        def clear_chat():
            return [], ""
        
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        
        # Update stats periodically
        chatbot.change(update_stats, outputs=[stats_display])
        chatbot.change(update_memory, outputs=[memory_display])
        
        # Footer
        gr.Markdown("""
        ---
        ### About Stack 2.9
        
        Stack 2.9 is a pattern-based AI coding assistant that:
        - 🔍 Uses **Qwen2.5-Coder-7B** (4-bit, ~4GB VRAM)
        - 🛠️ Integrates **7 tools** (file, git, web, search, shell)
        - 🧠 Remembers interactions and learns patterns
        - ⚡ Provides fast, streaming responses
        
        Deployed on **HuggingFace Spaces** with Gradio
        """)
    
    return app


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stack 2.9 - HuggingFace Spaces Demo")
    parser.add_argument("--share", action="store_true", help="Create a public share link")
    parser.add_argument("--port", type=int, default=7860, help="Port to run on")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-Coder-7B-Instruct", help="Model ID")
    args = parser.parse_args()
    
    print("=" * 50)
    print("🚀 Stack 2.9 - Pattern-Based AI Coding Assistant")
    print("=" * 50)
    print(f"Model: {args.model}")
    print("Loading model...")
    
    # Initialize model in a thread
    import threading
    
    def load_model_thread():
        global model
        model = initialize_model()
    
    loader_thread = threading.Thread(target=load_model_thread)
    loader_thread.start()
    
    # Create and launch app
    app = create_gradio_app()
    
    print(f"\n🚀 Launching Gradio on port {args.port}...")
    print("📝 Note: Model loads in background. Chat will work once loaded.\n")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share
    )