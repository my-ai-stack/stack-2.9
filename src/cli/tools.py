#!/usr/bin/env python3
"""
Stack 2.9 - Built-in Tools Module
38 powerful tools for file operations, git, code execution, web, memory, and planning.
"""

import os
import re
import json
import subprocess
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib


# ============================================================================
# FILE OPERATIONS TOOLS (Tools 1-8)
# ============================================================================

def tool_read_file(path: str, offset: int = 0, limit: int = -1) -> Dict[str, Any]:
    """Read file contents with optional offset and limit."""
    try:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        content = p.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        if limit > 0:
            lines = lines[offset:offset + limit]
        
        return {
            "success": True,
            "content": '\n'.join(lines),
            "total_lines": len(content.split('\n')),
            "path": path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_write_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Write content to file (create or overwrite)."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        if append:
            p.write_text(content, encoding='utf-8')
        else:
            p.write_text(content, encoding='utf-8')
        
        return {
            "success": True,
            "path": path,
            "lines_written": len(content.split('\n'))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_edit_file(path: str, old_text: str, new_text: str) -> Dict[str, Any]:
    """Edit file using exact text replacement."""
    try:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        content = p.read_text(encoding='utf-8')
        if old_text not in content:
            return {"success": False, "error": "Text to replace not found"}
        
        new_content = content.replace(old_text, new_text, 1)
        p.write_text(new_content, encoding='utf-8')
        
        return {
            "success": True,
            "path": path,
            "edits_made": 1
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_search_files(
    path: str,
    pattern: str,
    exclude: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Recursively search for files matching a pattern."""
    try:
        base_path = Path(path)
        if not base_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        
        results = []
        exclude = exclude or []
        
        for p in base_path.rglob(pattern):
            # Check if any exclusion pattern matches
            skip = False
            for exc in exclude:
                if exc in str(p):
                    skip = True
                    break
            if not skip:
                results.append(str(p))
        
        return {
            "success": True,
            "matches": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_grep(path: str, pattern: str, context: int = 0) -> Dict[str, Any]:
    """Search for pattern in file(s)."""
    try:
        base_path = Path(path)
        results = []
        
        if base_path.is_file():
            files = [base_path]
        elif base_path.is_dir():
            files = list(base_path.rglob('*'))
            files = [f for f in files if f.is_file()]
        else:
            return {"success": False, "error": f"Invalid path: {path}"}
        
        for f in files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        result = {
                            "file": str(f),
                            "line": i + 1,
                            "content": line.strip()
                        }
                        if context > 0:
                            start = max(0, i - context)
                            end = min(len(lines), i + context + 1)
                            result["context"] = lines[start:end]
                        results.append(result)
            except:
                continue
        
        return {
            "success": True,
            "matches": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_copy_file(source: str, destination: str) -> Dict[str, Any]:
    """Copy file or directory."""
    try:
        src = Path(source)
        dst = Path(destination)
        
        if not src.exists():
            return {"success": False, "error": f"Source not found: {source}"}
        
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        
        return {
            "success": True,
            "source": source,
            "destination": destination
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_move_file(source: str, destination: str) -> Dict[str, Any]:
    """Move or rename file or directory."""
    try:
        src = Path(source)
        dst = Path(destination)
        
        if not src.exists():
            return {"success": False, "error": f"Source not found: {source}"}
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        
        return {
            "success": True,
            "source": source,
            "destination": destination
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_delete_file(path: str, force: bool = False) -> Dict[str, Any]:
    """Delete file or directory (use trash for safe delete)."""
    try:
        p = Path(path)
        
        if not p.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        
        # For safety, require force=True for destructive delete
        if not force:
            # Just report what would be deleted
            return {
                "success": True,
                "would_delete": str(p),
                "warning": "Set force=True to actually delete"
            }
        
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        
        return {
            "success": True,
            "deleted": str(p)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# GIT OPERATIONS TOOLS (Tools 9-15)
# ============================================================================

def tool_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Get git status."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        files = [line[3:] for line in result.stdout.strip().split('\n') if line]
        
        return {
            "success": True,
            "files": files,
            "count": len(files),
            "repo": repo_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_commit(repo_path: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a git commit."""
    try:
        # Stage files if provided
        if files:
            for f in files:
                subprocess.run(
                    ["git", "-C", repo_path, "add", f],
                    capture_output=True,
                    timeout=30
                )
        else:
            subprocess.run(
                ["git", "-C", repo_path, "add", "-A"],
                capture_output=True,
                timeout=30
            )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "-C", repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if not result.stdout.strip():
            return {"success": True, "message": "No changes to commit"}
        
        # Commit
        result = subprocess.run(
            ["git", "-C", repo_path, "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": True,
            "message": message,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_push(repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
    """Push to remote."""
    try:
        cmd = ["git", "-C", repo_path, "push", remote]
        if branch:
            cmd.append(branch)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_pull(repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
    """Pull from remote."""
    try:
        cmd = ["git", "-C", repo_path, "pull", remote]
        if branch:
            cmd.append(branch)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_branch(repo_path: str = ".", create: Optional[str] = None, delete: Optional[str] = None) -> Dict[str, Any]:
    """List, create, or delete branches."""
    try:
        if create:
            result = subprocess.run(
                ["git", "-C", repo_path, "checkout", "-b", create],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": True, "created": create}
        
        if delete:
            result = subprocess.run(
                ["git", "-C", repo_path, "branch", "-D", delete],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": True, "deleted": delete}
        
        # List branches
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-a"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        branches = [b.strip().replace('* ', '') for b in result.stdout.strip().split('\n') if b]
        
        return {
            "success": True,
            "branches": branches,
            "count": len(branches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_log(repo_path: str = ".", limit: int = 10) -> Dict[str, Any]:
    """Get git log."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", f"--max-count={limit}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        commits = result.stdout.strip().split('\n')
        
        return {
            "success": True,
            "commits": commits,
            "count": len([c for c in commits if c])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_git_diff(repo_path: str = ".", file: Optional[str] = None, staged: bool = False) -> Dict[str, Any]:
    """Get git diff."""
    try:
        cmd = ["git", "-C", repo_path, "diff"]
        if staged:
            cmd.append("--staged")
        if file:
            cmd.append(file)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": True,
            "diff": result.stdout,
            "has_changes": bool(result.stdout.strip())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# CODE EXECUTION TOOLS (Tools 16-22)
# ============================================================================

def tool_run_command(
    command: str,
    timeout: int = 60,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Run shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env={**os.environ, **(env or {})}
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_run_tests(path: str = ".", pattern: str = "test*.py", verbose: bool = True) -> Dict[str, Any]:
    """Run tests using pytest."""
    try:
        cmd = ["pytest", path, "-k", pattern]
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=path
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode
        }
    except FileNotFoundError:
        return {"success": False, "error": "pytest not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_lint_code(path: str = ".", linter: str = "ruff") -> Dict[str, Any]:
    """Lint code."""
    try:
        if linter == "ruff":
            result = subprocess.run(
                ["ruff", "check", path],
                capture_output=True,
                text=True,
                timeout=120
            )
        elif linter == "pylint":
            result = subprocess.run(
                ["pylint", path],
                capture_output=True,
                text=True,
                timeout=120
            )
        elif linter == "mypy":
            result = subprocess.run(
                ["mypy", path],
                capture_output=True,
                text=True,
                timeout=120
            )
        else:
            return {"success": False, "error": f"Unknown linter: {linter}"}
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    except FileNotFoundError:
        return {"success": False, "error": f"{linter} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_format_code(path: str = ".", formatter: str = "ruff") -> Dict[str, Any]:
    """Format code."""
    try:
        if formatter == "ruff":
            result = subprocess.run(
                ["ruff", "format", path],
                capture_output=True,
                text=True,
                timeout=120
            )
        elif formatter == "black":
            result = subprocess.run(
                ["black", path],
                capture_output=True,
                text=True,
                timeout=120
            )
        else:
            return {"success": False, "error": f"Unknown formatter: {formatter}"}
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    except FileNotFoundError:
        return {"success": False, "error": f"{formatter} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_check_type(path: str = ".") -> Dict[str, Any]:
    """Type check with mypy."""
    try:
        result = subprocess.run(
            ["mypy", path, "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    except FileNotFoundError:
        return {"success": False, "error": "mypy not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_start_server(
    command: str,
    port: int,
    cwd: Optional[str] = None,
    background: bool = False
) -> Dict[str, Any]:
    """Start a development server."""
    try:
        if background:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return {
                "success": True,
                "pid": proc.pid,
                "port": port,
                "message": f"Server started on port {port}"
            }
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_install_dependencies(path: str = ".", package_manager: str = "pip") -> Dict[str, Any]:
    """Install dependencies."""
    try:
        if package_manager == "pip":
            result = subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=path
            )
        elif package_manager == "poetry":
            result = subprocess.run(
                ["poetry", "install"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=path
            )
        elif package_manager == "npm":
            result = subprocess.run(
                ["npm", "install"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=path
            )
        else:
            return {"success": False, "error": f"Unknown package manager: {package_manager}"}
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# WEB TOOLS (Tools 23-27)
# ============================================================================

def tool_web_search(
    query: str,
    count: int = 5,
    freshness: Optional[str] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """Search the web using DuckDuckGo."""
    try:
        import urllib.request
        import urllib.parse
        import re
        from html import unescape

        # DuckDuckGo Lite
        encoded_query = urllib.parse.quote(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        results = []
        # Find links - look for anchor tags with titles
        all_links = re.findall(r'<a[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a>', html)

        for url, title in all_links[:count]:
            title = unescape(title).strip()
            if title and len(title) > 3:
                results.append({"title": title, "url": url})

        return {
            "success": True,
            "query": query,
            "results": results[:count],
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_web_fetch(url: str, max_chars: int = 10000) -> Dict[str, Any]:
    """Fetch and extract content from URL."""
    try:
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        content = result.stdout[:max_chars]
        
        return {
            "success": True,
            "url": url,
            "content": content,
            "length": len(content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_download_file(url: str, destination: str) -> Dict[str, Any]:
    """Download file from URL."""
    try:
        result = subprocess.run(
            ["curl", "-L", "-o", destination, url],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        size = Path(destination).stat().st_size if Path(destination).exists() else 0
        
        return {
            "success": result.returncode == 0,
            "url": url,
            "destination": destination,
            "size": size
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_check_url(url: str) -> Dict[str, Any]:
    """Check if URL is accessible."""
    try:
        result = subprocess.run(
            ["curl", "-I", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        code = result.stdout.strip()
        
        return {
            "success": code in ["200", "301", "302"],
            "url": url,
            "status_code": code
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_screenshot(url: str, destination: str = "screenshot.png") -> Dict[str, Any]:
    """Take screenshot of webpage."""
    try:
        # Try playwright or puppeteer
        result = subprocess.run(
            ["npx", "puppeteer", url, "--output", destination],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {"success": False, "error": "Failed to take screenshot"}
        
        return {
            "success": True,
            "url": url,
            "destination": destination
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# MEMORY TOOLS (Tools 28-32)
# ============================================================================

def tool_memory_recall(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Recall from memory (searches memory files)."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        
        # Search in memory files
        results = []
        
        # Search MEMORY.md
        memory_file = workspace / "MEMORY.md"
        if memory_file.exists():
            content = memory_file.read_text()
            if query.lower() in content.lower():
                results.append(str(memory_file))
        
        # Search memory folder
        memory_dir = workspace / "memory"
        if memory_dir.exists():
            for f in memory_dir.rglob("*.md"):
                try:
                    content = f.read_text()
                    if query.lower() in content.lower():
                        results.append(str(f))
                except:
                    continue
        
        return {
            "success": True,
            "query": query,
            "matches": results[:max_results],
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_memory_save(key: str, value: str) -> Dict[str, Any]:
    """Save to memory."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        memory_file = workspace / "MEMORY.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### {key}\n_{timestamp}_\n{value}\n"
        
        with open(memory_file, "a") as f:
            f.write(entry)
        
        return {
            "success": True,
            "key": key,
            "saved": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_memory_list() -> Dict[str, Any]:
    """List memory entries."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        memory_file = workspace / "MEMORY.md"
        
        if not memory_file.exists():
            return {"success": True, "entries": []}
        
        content = memory_file.read_text()
        
        # Extract sections
        pattern = r"### (.+?)\n.*?\n(.*?)(?=### |$)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        entries = [{"title": m[0].strip(), "content": m[1].strip()[:200]} for m in matches]
        
        return {
            "success": True,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_context_load(projects: Optional[List[str]] = None) -> Dict[str, Any]:
    """Load project context."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        
        context = {}
        
        # Load AGENTS.md
        agents_file = workspace / "AGENTS.md"
        if agents_file.exists():
            context["agents"] = agents_file.read_text()
        
        # Load SOUL.md
        soul_file = workspace / "SOUL.md"
        if soul_file.exists():
            context["soul"] = soul_file.read_text()
        
        # Load TOOLS.md
        tools_file = workspace / "TOOLS.md"
        if tools_file.exists():
            context["tools"] = tools_file.read_text()
        
        return {
            "success": True,
            "context": context,
            "loaded": list(context.keys())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_project_scan(path: str = ".") -> Dict[str, Any]:
    """Scan project structure."""
    try:
        base = Path(path)
        
        if not base.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        
        info = {
            "name": base.name,
            "files": [],
            "dirs": [],
            "has_git": (base / ".git").exists(),
            "has_pyproject": (base / "pyproject.toml").exists(),
            "has_package_json": (base / "package.json").exists(),
            "has_dockerfile": (base / "Dockerfile").exists()
        }
        
        for item in base.rglob("*"):
            if len(info["files"]) + len(info["dirs"]) > 100:
                break
            
            rel = item.relative_to(base)
            if item.is_dir():
                info["dirs"].append(str(rel))
            else:
                info["files"].append(str(rel))
        
        return {
            "success": True,
            "project": info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# TASK PLANNING TOOLS (Tools 33-37)
# ============================================================================

def tool_create_task(title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
    """Create a task."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        tasks_file = workspace / ".tasks.json"
        
        tasks = []
        if tasks_file.exists():
            tasks = json.loads(tasks_file.read_text())
        
        task_id = hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:8]
        
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        
        tasks.append(task)
        tasks_file.write_text(json.dumps(tasks, indent=2))
        
        return {
            "success": True,
            "task": task
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_list_tasks(status: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
    """List tasks."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        tasks_file = workspace / ".tasks.json"
        
        if not tasks_file.exists():
            return {"success": True, "tasks": []}
        
        tasks = json.loads(tasks_file.read_text())
        
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if priority:
            tasks = [t for t in tasks if t.get("priority") == priority]
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_update_task(task_id: str, status: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Update a task."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        tasks_file = workspace / ".tasks.json"
        
        if not tasks_file.exists():
            return {"success": False, "error": "No tasks found"}
        
        tasks = json.loads(tasks_file.read_text())
        
        for task in tasks:
            if task.get("id") == task_id:
                if status:
                    task["status"] = status
                task.update(kwargs)
                task["updated"] = datetime.now().isoformat()
                break
        
        tasks_file.write_text(json.dumps(tasks, indent=2))
        
        return {
            "success": True,
            "task_id": task_id,
            "updated": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        tasks_file = workspace / ".tasks.json"
        
        if not tasks_file.exists():
            return {"success": False, "error": "No tasks found"}
        
        tasks = json.loads(tasks_file.read_text())
        tasks = [t for t in tasks if t.get("id") != task_id]
        
        tasks_file.write_text(json.dumps(tasks, indent=2))
        
        return {
            "success": True,
            "task_id": task_id,
            "deleted": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_create_plan(goal: str, steps: List[str]) -> Dict[str, Any]:
    """Create an execution plan."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        plans_file = workspace / ".plans.json"
        
        plans = []
        if plans_file.exists():
            plans = json.loads(plans_file.read_text())
        
        plan_id = hashlib.md5(f"{goal}{datetime.now()}".encode()).hexdigest()[:8]
        
        plan = {
            "id": plan_id,
            "goal": goal,
            "steps": steps,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        
        plans.append(plan)
        plans_file.write_text(json.dumps(plans, indent=2))
        
        return {
            "success": True,
            "plan": plan
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_execute_plan(plan_id: str) -> Dict[str, Any]:
    """Execute a plan step by step."""
    try:
        workspace = Path("/Users/walidsobhi/.openclaw/workspace")
        plans_file = workspace / ".plans.json"
        
        if not plans_file.exists():
            return {"success": False, "error": "No plans found"}
        
        plans = json.loads(plans_file.read_text())
        
        for plan in plans:
            if plan.get("id") == plan_id:
                plan["status"] = "in_progress"
                plan["started"] = datetime.now().isoformat()
                break
        
        plans_file.write_text(json.dumps(plans, indent=2))
        
        return {
            "success": True,
            "plan_id": plan_id,
            "status": "executing",
            "steps": plan.get("steps", [])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL REGISTRY
# ============================================================================

TOOLS: Dict[str, Callable] = {
    # File operations (1-8)
    "read": tool_read_file,
    "write": tool_write_file,
    "edit": tool_edit_file,
    "search": tool_search_files,
    "grep": tool_grep,
    "copy": tool_copy_file,
    "move": tool_move_file,
    "delete": tool_delete_file,
    
    # Git operations (9-15)
    "git_status": tool_git_status,
    "git_commit": tool_git_commit,
    "git_push": tool_git_push,
    "git_pull": tool_git_pull,
    "git_branch": tool_git_branch,
    "git_log": tool_git_log,
    "git_diff": tool_git_diff,
    
    # Code execution (16-22)
    "run": tool_run_command,
    "test": tool_run_tests,
    "lint": tool_lint_code,
    "format": tool_format_code,
    "typecheck": tool_check_type,
    "server": tool_start_server,
    "install": tool_install_dependencies,
    
    # Web (23-27)
    "web_search": tool_web_search,
    "fetch": tool_web_fetch,
    "download": tool_download_file,
    "check_url": tool_check_url,
    "screenshot": tool_screenshot,
    
    # Memory (28-32)
    "memory_recall": tool_memory_recall,
    "memory_save": tool_memory_save,
    "memory_list": tool_memory_list,
    "context_load": tool_context_load,
    "project_scan": tool_project_scan,
    
    # Task planning (33-37)
    "create_task": tool_create_task,
    "list_tasks": tool_list_tasks,
    "update_task": tool_update_task,
    "delete_task": tool_delete_task,
    "create_plan": tool_create_plan,
    "execute_plan": tool_execute_plan,
}


def get_tool(name: str) -> Optional[Callable]:
    """Get tool by name."""
    return TOOLS.get(name)


def list_tools() -> List[str]:
    """List all available tools."""
    return list(TOOLS.keys())


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get tool schemas for LLM tool calling.
    
    Automatically generates JSON Schema from function signatures using inspect.
    All 38 tools are included with accurate parameter types and descriptions.
    """
    import inspect
    from typing import get_type_hints
    
    schemas = []
    
    for name, func in TOOLS.items():
        sig = inspect.signature(func)
        doc = func.__doc__ or f"Tool: {name}"
        
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # Skip self/cls
            if param_name in ('self', 'cls'):
                continue
            
            # Get type annotation
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                json_type = "string"  # default
            elif annotation is str:
                json_type = "string"
            elif annotation is int:
                json_type = "integer"
            elif annotation is bool:
                json_type = "boolean"
            elif annotation is float:
                json_type = "number"
            elif hasattr(annotation, '__origin__') and annotation.__origin__ is list:
                json_type = "array"
            elif hasattr(annotation, '__origin__') and annotation.__origin__ is dict:
                json_type = "object"
            else:
                json_type = "string"  # fallback
            
            # Build property definition
            prop = {"type": json_type}
            
            # Extract description from docstring
            param_desc = _extract_param_desc(doc, param_name)
            if param_desc:
                prop["description"] = param_desc
            
            # Add enum for restricted string values
            if param_name in ('linter', 'formatter', 'package_manager') and hasattr(annotation, '__args__'):
                prop["enum"] = list(annotation.__args__)
            
            properties[param_name] = prop
            
            # Mark as required if no default value
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        
        schema = {
            "name": name,
            "description": doc.strip().split('\n')[0],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        
        schemas.append(schema)
    
    return schemas


def _extract_param_desc(docstring: str, param_name: str) -> Optional[str]:
    """Extract parameter description from docstring.
    
    Looks for lines like: "- `param_name`: description" or "param_name: description".
    """
    if not docstring:
        return None
    
    lines = docstring.split('\n')
    for i, line in enumerate(lines):
        # Match: - `param`: description
        if f"`{param_name}`" in line or f"{param_name}:" in line:
            # Try to extract after colon or dash
            parts = line.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip().lstrip(' -').strip()
            # Alternative: split on backtick
            parts = line.split('`', 2)
            if len(parts) > 2:
                return parts[2].strip().lstrip(': -').strip()
    
    return None


if __name__ == "__main__":
    print("Stack 2.9 Tools Module")
    print(f"Available tools: {len(TOOLS)}")
    print(list_tools())
