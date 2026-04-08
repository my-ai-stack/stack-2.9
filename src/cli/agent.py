#!/usr/bin/env python3
"""
Stack 2.9 - Core Agent Logic Module
Query understanding, tool selection, response generation, and self-reflection loop.
"""

import os
import json
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .tools import TOOLS, get_tool, list_tools, get_tool_schemas
from .context import ContextManager, create_context_manager


class QueryIntent(Enum):
    """Intents recognized by the agent."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    FILE_SEARCH = "file_search"
    GIT_OPERATION = "git_operation"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    MEMORY = "memory"
    TASK = "task"
    QUESTION = "question"
    GENERAL = "general"


@dataclass
class ToolCall:
    """Represents a tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """Represents the agent's response."""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    context_used: List[str] = field(default_factory=list)
    confidence: float = 1.0
    needs_clarification: bool = False
    clarification_needed: Optional[str] = None


class QueryUnderstanding:
    """Understands user queries and maps them to intents and tools."""
    
    # Intent patterns
    PATTERNS = {
        QueryIntent.FILE_READ: [
            r"read\s+(?:the\s+)?(?:file\s+)?(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"show\s+(?:me\s+)?(?:the\s+)?(?:content\s+of\s+)?(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"what('s| is)\s+in\s+(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"cat\s+(.+)",
            r"view\s+(.+)",
        ],
        QueryIntent.FILE_WRITE: [
            r"write\s+(?:to\s+)?(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"create\s+(?:file\s+)?(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"save\s+(?:to\s+)?(.+)",
        ],
        QueryIntent.FILE_EDIT: [
            r"edit\s+(.+\.py|.+\.js|.+\.txt|.+\.md|.+\.json)",
            r"modify\s+(.+)",
            r"change\s+(.+)",
            r"replace\s+(.+)",
        ],
        QueryIntent.FILE_SEARCH: [
            r"find\s+(?:files?\s+)?(?:named\s+)?(.+)",
            r"search\s+for\s+(?:files?\s+)?(.+)",
            r"where\s+is\s+(.+)",
            r"locate\s+(.+)",
        ],
        QueryIntent.GIT_OPERATION: [
            r"git\s+(commit|push|pull|branch|status|log|diff)",
            r"(commit|push|pull|branch)\s+(?:to\s+)?(?:the\s+)?(?:repo|repository)?",
        ],
        QueryIntent.CODE_EXECUTION: [
            r"run\s+(?:the\s+)?(?:command\s+)?(.+)",
            r"execute\s+(.+)",
            r"start\s+(?:the\s+)?(?:server\s+)?(.+)",
            r"test\s+(?:the\s+)?(.+)",
            r"lint\s+(.+)",
            r"format\s+(.+)",
        ],
        QueryIntent.WEB_SEARCH: [
            r"search\s+(?:the\s+)?web\s+for\s+(.+)",
            r"google\s+(.+)",
            r"look\s+up\s+(.+)",
            r"find\s+information\s+about\s+(.+)",
        ],
        QueryIntent.MEMORY: [
            r"(remember|recall|what do you remember)\s+(.+)",
            r"(save|store)\s+(?:to\s+)?memory\s+(.+)",
            r"what('s| is)\s+in\s+(?:the\s+)?memory",
        ],
        QueryIntent.TASK: [
            r"(create|add|new)\s+task\s+(.+)",
            r"list\s+(?:my\s+)?tasks?",
            r"(complete|finish|done)\s+task\s+(.+)",
        ],
        QueryIntent.QUESTION: [
            r"what\s+is\s+(.+)",
            r"how\s+(?:do|does)\s+(.+)",
            r"why\s+(.+)",
            r"can\s+(.+)",
            r"(?:help|explain)\s+(.+)",
        ],
    }
    
    def __init__(self):
        self.tools = list_tools()
    
    def parse(self, query: str) -> Dict[str, Any]:
        """Parse query and determine intent."""
        query = query.strip().lower()
        
        # Check each intent pattern
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    return {
                        "intent": intent.value,
                        "matched": match.group(0),
                        "extracted": match.groups() if match.groups() else None,
                        "confidence": 0.8
                    }
        
        return {
            "intent": QueryIntent.GENERAL.value,
            "matched": None,
            "extracted": None,
            "confidence": 0.5
        }
    
    def extract_file_path(self, text: str) -> Optional[str]:
        """Extract file path from text."""
        # Common patterns for file paths
        patterns = [
            r"([a-zA-Z0-9_/\-\.]+\.py)",
            r"([a-zA-Z0-9_/\-\.]+\.js)",
            r"([a-zA-Z0-9_/\-\.]+\.ts)",
            r"([a-zA-Z0-9_/\-\.]+\.md)",
            r"([a-zA-Z0-9_/\-\.]+\.json)",
            r"([a-zA-Z0-9_/\-\.]+\.txt)",
            r"([a-zA-Z0-9_/\-\.]+\.yaml|\.yml)",
            r"([a-zA-Z0-9_/\-\.]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None


class ToolSelector:
    """Selects appropriate tools based on query intent."""
    
    # Intent to tool mapping
    INTENT_TOOLS = {
        QueryIntent.FILE_READ: ["read"],
        QueryIntent.FILE_WRITE: ["write"],
        QueryIntent.FILE_EDIT: ["edit"],
        QueryIntent.FILE_SEARCH: ["search", "grep"],
        QueryIntent.GIT_OPERATION: ["git_status", "git_commit", "git_push", "git_pull", "git_branch", "git_log"],
        QueryIntent.CODE_EXECUTION: ["run", "test", "lint", "format"],
        QueryIntent.WEB_SEARCH: ["web_search", "fetch"],
        QueryIntent.MEMORY: ["memory_recall", "memory_save", "memory_list"],
        QueryIntent.TASK: ["create_task", "list_tasks", "update_task"],
    }
    
    def select(self, intent: str, context: Dict[str, Any]) -> List[str]:
        """Select tools for given intent."""
        # Map string to QueryIntent enum
        INTENT_MAP = {
            "file_read": QueryIntent.FILE_READ,
            "file_write": QueryIntent.FILE_WRITE,
            "file_edit": QueryIntent.FILE_EDIT,
            "file_search": QueryIntent.FILE_SEARCH,
            "git_operation": QueryIntent.GIT_OPERATION,
            "code_execution": QueryIntent.CODE_EXECUTION,
            "web_search": QueryIntent.WEB_SEARCH,
            "memory": QueryIntent.MEMORY,
            "task": QueryIntent.TASK,
            "general": QueryIntent.GENERAL,
        }
        
        tools = []
        intent_enum = INTENT_MAP.get(intent)
        if intent_enum:
            tools = list(self.INTENT_TOOLS.get(intent_enum, []))
        
        # For git operations, filter based on query keywords
        if intent == "git_operation" and context.get("query"):
            query = context["query"].lower()
            git_keyword_tools = {
                "status": ["git_status"],
                "commit": ["git_commit"],
                "push": ["git_push"],
                "pull": ["git_pull"],
                "branch": ["git_branch"],
                "log": ["git_log"],
                "diff": ["git_diff"],
            }
            filtered = []
            for kw, tool_list in git_keyword_tools.items():
                if kw in query:
                    filtered.extend(tool_list)
            # Default to git_status if no specific keyword found but query mentions git
            if not filtered and "git" in query:
                filtered = ["git_status"]
            if filtered:
                tools = filtered
        
        return tools
    
    def get_tool_parameters(self, tool_name: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for a tool from query and context."""
        params = {}
        
        query_lower = query.lower()
        
        if tool_name == "read":
            path = re.search(r"(?:read|show|cat|view)\s+(?:the\s+)?(?:file\s+)?(.+)", query, re.IGNORECASE)
            if path:
                params["path"] = path.group(1).strip()
        
        elif tool_name == "write":
            path = re.search(r"write\s+(?:to\s+)?(.+?)(?:\s+with|\s+content|$)", query, re.IGNORECASE)
            if path:
                params["path"] = path.group(1).strip()
            # Try to extract content
            content_match = re.search(r"(?:content|with):\s*(.+)$", query, re.IGNORECASE)
            if content_match:
                params["content"] = content_match.group(1)
        
        elif tool_name == "git_commit":
            msg = re.search(r"commit(?:\s+with)?\s+(?:message\s+)?[\"']?(.+)[\"']?", query, re.IGNORECASE)
            if msg:
                params["message"] = msg.group(1).strip()
        
        elif tool_name == "web_search":
            # Extract search query
            patterns = [
                r"search\s+(?:the\s+)?web\s+for\s+(.+)",
                r"google\s+(.+)",
                r"look\s+up\s+(.+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    params["query"] = match.group(1).strip()
                    break
        
        return params


class ResponseGenerator:
    """Generates natural language responses."""
    
    def __init__(self):
        self.context_manager = create_context_manager()
    
    def generate(
        self,
        tool_results: List[ToolCall],
        intent: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate response from tool results."""
        if not tool_results:
            return "I couldn't find any results for your query."
        
        responses = []
        
        for call in tool_results:
            if call.result is None:
                responses.append(f"I tried to use {call.tool_name} but got no result.")
                continue
            
            if call.result.get("success"):
                result = call.result
                
                # Format based on tool
                if call.tool_name == "read":
                    if "content" in result:
                        content = result["content"]
                        if len(content) > 500:
                            content = content[:500] + "..."
                        responses.append(f"Here's the content:\n```\n{content}\n```")
                
                elif call.tool_name == "grep":
                    if "matches" in result:
                        matches = result["matches"]
                        if matches:
                            resp = f"Found {len(matches)} matches:\n"
                            for m in matches[:10]:
                                resp += f"- {m.get('file', '?')}:{m.get('line', '?')} - {m.get('content', '')}\n"
                            responses.append(resp)
                        else:
                            responses.append("No matches found.")
                
                elif call.tool_name in ["git_status", "git_log"]:
                    if "files" in result:
                        files = result["files"]
                        if files:
                            responses.append(f"Changed files ({len(files)}):\n" + "\n".join(f"  - {f}" for f in files))
                        else:
                            responses.append("No changes detected.")
                    elif "commits" in result:
                        commits = result["commits"]
                        if commits:
                            responses.append("Recent commits:\n" + "\n".join(f"  - {c}" for c in commits[:5]))
                
                elif call.tool_name == "web_search":
                    if "results" in result:
                        results = result["results"]
                        resp = "Search results:\n"
                        for r in results[:5]:
                            resp += f"- {r.get('title', 'Untitled')}\n"
                        responses.append(resp)
                
                elif call.tool_name == "run":
                    stdout = result.get("stdout", "")
                    stderr = result.get("stderr", "")
                    if stdout:
                        responses.append(f"Output:\n```\n{stdout[:500]}\n```")
                    if stderr:
                        responses.append(f"Errors:\n```\n{stderr[:500]}\n```")
                    if not stdout and not stderr:
                        responses.append("Command executed successfully.")
                
                elif call.tool_name == "memory_recall":
                    if "matches" in result:
                        matches = result["matches"]
                        if matches:
                            responses.append(f"Found {len(matches)} memory entries.")
                        else:
                            responses.append("No matching memories found.")
                
                else:
                    # Generic success response
                    responses.append(f"{call.tool_name}: {json.dumps(result)[:200]}")
            else:
                error = call.result.get("error", "Unknown error")
                responses.append(f"Error in {call.tool_name}: {error}")
        
        return "\n\n".join(responses) or "I processed your request but have no results to show."
    
    def generate_clarification(self, question: str) -> str:
        """Generate clarification question."""
        return f"I need some clarification: {question}"


class SelfReflection:
    """Self-reflection loop for improving responses."""
    
    def __init__(self):
        self.max_iterations = 3
        self.min_confidence = 0.7
    
    def reflect(
        self,
        query: str,
        tool_calls: List[ToolCall],
        response: str
    ) -> Dict[str, Any]:
        """Reflect on the response and determine if improvement is needed."""
        # Check if any tool call failed
        failed_calls = [c for c in tool_calls if not c.success]
        
        # Calculate confidence
        success_rate = len(tool_calls) / max(len(tool_calls), 1)
        confidence = success_rate
        
        needs_reflection = (
            len(failed_calls) > 0 or
            confidence < self.min_confidence or
            len(response) < 20
        )
        
        return {
            "needs_reflection": needs_reflection,
            "confidence": confidence,
            "failed_calls": len(failed_calls),
            "response_length": len(response),
            "suggestion": self._get_suggestion(failed_calls, confidence) if needs_reflection else None
        }
    
    def _get_suggestion(self, failed_calls: List[ToolCall], confidence: float) -> str:
        """Get improvement suggestion."""
        if not failed_calls:
            return "Try providing more context in your query."
        
        return f"Failed tool calls: {', '.join(c.tool_name for c in failed_calls)}"


class StackAgent:
    """
    Core agent that combines all components for intelligent assistance.
    """
    
    def __init__(self, workspace: Optional[str] = None):
        self.query_understanding = QueryUnderstanding()
        self.tool_selector = ToolSelector()
        self.response_generator = ResponseGenerator()
        self.self_reflection = SelfReflection()
        self.context_manager = create_context_manager(workspace)
        self.conversation_history: List[Dict[str, Any]] = []
    
    def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        """Process a user query."""
        context = context or {}
        
        # Step 1: Understand query
        parsed = self.query_understanding.parse(query)
        intent = parsed["intent"]
        confidence = parsed["confidence"]
        
        # Step 2: Select tools (pass query in context for smart filtering)
        selected_tools = self.tool_selector.select(intent, {"query": query, **context})
        tool_params = {}
        
        for tool_name in selected_tools:
            tool_params[tool_name] = self.tool_selector.get_tool_parameters(tool_name, query, context)
        
        # Step 3: Execute tools
        tool_calls = []
        for tool_name in selected_tools:
            tool = get_tool(tool_name)
            if tool is None:
                continue
            
            params = tool_params.get(tool_name, {})
            try:
                result = tool(**params)
                call = ToolCall(
                    tool_name=tool_name,
                    arguments=params,
                    result=result,
                    success=result.get("success", False) if isinstance(result, dict) else True
                )
            except Exception as e:
                call = ToolCall(
                    tool_name=tool_name,
                    arguments=params,
                    error=str(e),
                    success=False
                )
            
            tool_calls.append(call)
            
            # Record in session
            self.context_manager.session.add_tool_usage(tool_name, call.result)
        
        # Step 4: Generate response
        response_content = self.response_generator.generate(tool_calls, intent, context)
        
        # Step 5: Self-reflect
        reflection = self.self_reflection.reflect(query, tool_calls, response_content)
        
        # Step 6: Add to conversation history
        self.conversation_history.append({
            "query": query,
            "intent": intent,
            "tool_calls": [c.tool_name for c in tool_calls],
            "response": response_content,
            "reflection": reflection,
            "timestamp": datetime.now().isoformat()
        })
        
        return AgentResponse(
            content=response_content,
            tool_calls=tool_calls,
            confidence=reflection.get("confidence", confidence),
            needs_clarification=reflection.get("needs_reflection", False),
            clarification_needed=reflection.get("suggestion")
        )
    
    def process_with_tools(self, query: str, forced_tools: List[str]) -> AgentResponse:
        """Process query with explicitly specified tools."""
        tool_calls = []
        
        for tool_name in forced_tools:
            tool = get_tool(tool_name)
            if tool is None:
                continue
            
            try:
                result = tool()
                call = ToolCall(
                    tool_name=tool_name,
                    arguments={},
                    result=result,
                    success=result.get("success", False) if isinstance(result, dict) else True
                )
            except Exception as e:
                call = ToolCall(
                    tool_name=tool_name,
                    arguments={},
                    error=str(e),
                    success=False
                )
            
            tool_calls.append(call)
        
        response_content = self.response_generator.generate(tool_calls, "general", {})
        
        return AgentResponse(
            content=response_content,
            tool_calls=tool_calls,
            confidence=1.0
        )
    
    def get_context(self) -> str:
        """Get current context as string."""
        return self.context_manager.get_workspace_context()
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for tool calling."""
        return get_tool_schemas()


def create_agent(workspace: Optional[str] = None) -> StackAgent:
    """Factory function to create agent."""
    return StackAgent(workspace)


if __name__ == "__main__":
    print("Stack 2.9 Agent Module")
    agent = create_agent()
    print(f"Agent initialized with {len(list_tools())} tools")
    
    # Test query
    response = agent.process("list my tasks")
    print(f"\nQuery: 'list my tasks'")
    print(f"Response: {response.content[:200]}")
