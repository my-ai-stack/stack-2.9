#!/usr/bin/env python3
"""
Stack 2.9 - Context Management Module
Handles project awareness, session memory, and long-term memory integration.
"""

import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ProjectContext:
    """Represents a project's context."""
    name: str
    path: str
    language: Optional[str] = None
    framework: Optional[str] = None
    files: List[str] = field(default_factory=list)
    dirs: List[str] = field(default_factory=list)
    has_git: bool = False
    dependencies: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMemory:
    """Represents the current session's memory."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)
    commands_run: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to session memory."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.last_updated = datetime.now()
    
    def add_tool_usage(self, tool_name: str, result: Any):
        """Record tool usage."""
        self.tools_used.append({
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False) if isinstance(result, dict) else True
        })
        self.last_updated = datetime.now()
    
    def add_file_touched(self, file_path: str, action: str):
        """Record file access."""
        self.files_touched.append({
            "path": file_path,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def add_command(self, command: str, result: Optional[Dict] = None):
        """Record command execution."""
        self.commands_run.append({
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        return {
            "messages_count": len(self.messages),
            "tools_used_count": len(self.tools_used),
            "files_touched_count": len(self.files_touched),
            "commands_run_count": len(self.commands_run),
            "duration_minutes": (datetime.now() - self.created_at).total_seconds() / 60,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


class ContextManager:
    """Manages context across projects, sessions, and long-term memory."""
    
    def __init__(self, workspace_path: str = "/Users/walidsobhi/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.session = SessionMemory()
        self.projects: Dict[str, ProjectContext] = {}
        self.current_project: Optional[ProjectContext] = None
        self._load_context()
    
    def _load_context(self):
        """Load existing context files."""
        # Load workspace context files
        context_files = {
            "AGENTS.md": "agents",
            "SOUL.md": "soul",
            "TOOLS.md": "tools",
            "USER.md": "user",
            "MEMORY.md": "memory"
        }
        
        self.context = {}
        for filename, key in context_files.items():
            file_path = self.workspace / filename
            if file_path.exists():
                self.context[key] = file_path.read_text(encoding='utf-8')
        
        # Scan for projects
        self._scan_projects()
    
    def _scan_projects(self):
        """Scan workspace for projects."""
        for item in self.workspace.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it's a project
                if (item / "pyproject.toml").exists() or (item / "package.json").exists():
                    self.projects[item.name] = ProjectContext(
                        name=item.name,
                        path=str(item)
                    )
    
    def load_project(self, project_name: str) -> Optional[ProjectContext]:
        """Load a specific project."""
        project_path = self.workspace / project_name
        
        if not project_path.exists():
            return None
        
        # Create project context
        ctx = ProjectContext(
            name=project_name,
            path=str(project_path)
        )
        
        # Detect language/framework
        if (project_path / "pyproject.toml").exists():
            ctx.language = "python"
            try:
                content = (project_path / "pyproject.toml").read_text()
                if "fastapi" in content:
                    ctx.framework = "fastapi"
                elif "django" in content:
                    ctx.framework = "django"
                elif "flask" in content:
                    ctx.framework = "flask"
            except:
                pass
        
        if (project_path / "package.json").exists():
            ctx.language = "javascript"
            try:
                content = json.loads((project_path / "package.json").read_text())
                ctx.dependencies = list(content.get("dependencies", {}).keys())
                if "next" in content.get("dependencies", {}):
                    ctx.framework = "next"
                elif "react" in content.get("dependencies", {}):
                    ctx.framework = "react"
            except:
                pass
        
        # Check for git
        ctx.has_git = (project_path / ".git").exists()
        
        # Scan files
        try:
            for item in project_path.rglob("*"):
                if len(ctx.files) > 100:
                    break
                rel = item.relative_to(project_path)
                if item.is_file():
                    ctx.files.append(str(rel))
                elif item.is_dir() and not item.name.startswith('.'):
                    ctx.dirs.append(str(rel))
        except:
            pass
        
        # Find entry points
        entry_patterns = ["main.py", "app.py", "index.js", "main.js", "server.py"]
        for pattern in entry_patterns:
            for f in ctx.files:
                if f.endswith(pattern):
                    ctx.entry_points.append(f)
        
        self.projects[project_name] = ctx
        self.current_project = ctx
        return ctx
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get context summary."""
        return {
            "workspace": str(self.workspace),
            "projects": list(self.projects.keys()),
            "current_project": self.current_project.name if self.current_project else None,
            "session": self.session.get_summary(),
            "has_agents": "agents" in self.context,
            "has_soul": "soul" in self.context,
            "has_tools": "tools" in self.context,
            "has_memory": "memory" in self.context
        }
    
    def get_workspace_context(self) -> str:
        """Get formatted workspace context."""
        lines = ["# Workspace Context"]
        lines.append(f"\n## Projects ({len(self.projects)})")
        
        for name, proj in self.projects.items():
            lines.append(f"- **{name}** ({proj.language or 'unknown'})")
            if proj.framework:
                lines.append(f"  - Framework: {proj.framework}")
            lines.append(f"  - Path: {proj.path}")
            if proj.has_git:
                lines.append("  - Git: ✓")
        
        if self.current_project:
            lines.append(f"\n## Current Project: {self.current_project.name}")
            lines.append(f"- Files: {len(self.current_project.files)}")
            lines.append(f"- Dirs: {len(self.current_project.dirs)}")
            if self.current_project.entry_points:
                lines.append(f"- Entry: {self.current_project.entry_points[0]}")
        
        lines.append(f"\n## Session")
        summary = self.session.get_summary()
        lines.append(f"- Messages: {summary['messages_count']}")
        lines.append(f"- Tools used: {summary['tools_used_count']}")
        lines.append(f"- Files touched: {summary['files_touched_count']}")
        
        return "\n".join(lines)
    
    def search_memory(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search long-term memory."""
        results = []
        
        # Search MEMORY.md
        memory_file = self.workspace / "MEMORY.md"
        if memory_file.exists():
            content = memory_file.read_text()
            if query.lower() in content.lower():
                results.append({
                    "file": str(memory_file),
                    "type": "memory",
                    "content": content[:500]
                })
        
        # Search memory folder
        memory_dir = self.workspace / "memory"
        if memory_dir.exists():
            for f in memory_dir.rglob("*.md"):
                try:
                    content = f.read_text()
                    if query.lower() in content.lower():
                        results.append({
                            "file": str(f),
                            "type": "daily",
                            "content": content[:500]
                        })
                except:
                    continue
        
        return results[:max_results]
    
    def save_to_memory(self, key: str, value: str):
        """Save to long-term memory."""
        memory_file = self.workspace / "MEMORY.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### {key}\n_{timestamp}_\n{value}\n"
        
        with open(memory_file, "a") as f:
            f.write(entry)
    
    def get_recent_context(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent context from memory."""
        results = []
        
        memory_dir = self.workspace / "memory"
        if memory_dir.exists():
            # Get files from last N days
            cutoff = datetime.now() - timedelta(days=days)
            
            for f in sorted(memory_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime > cutoff:
                        content = f.read_text()
                        results.append({
                            "file": str(f),
                            "date": mtime.isoformat(),
                            "content": content[:1000]
                        })
                except:
                    continue
        
        return results


class ProjectAware:
    """Mixin for project-aware functionality."""
    
    def __init__(self):
        self.context_manager = ContextManager()
    
    def detect_project(self, path: str) -> Optional[str]:
        """Detect project from path."""
        p = Path(path).resolve()
        
        # Walk up to find project root
        while p != p.parent:
            for name in ["pyproject.toml", "package.json", "Cargo.toml", "go.mod"]:
                if (p / name).exists():
                    return p.name
            p = p.parent
        
        return None
    
    def get_project_context(self, project_name: str) -> Optional[ProjectContext]:
        """Get project context."""
        return self.context_manager.load_project(project_name)
    
    def format_context_for_prompt(self) -> str:
        """Format context for LLM prompt."""
        return self.context_manager.get_workspace_context()


def create_context_manager(workspace: Optional[str] = None) -> ContextManager:
    """Factory function to create context manager."""
    return ContextManager(workspace or "/Users/walidsobhi/.openclaw/workspace")


if __name__ == "__main__":
    print("Stack 2.9 Context Module")
    cm = ContextManager()
    print(cm.get_context_summary())
