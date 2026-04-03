"""
Observer System - Logs and analyzes the AI's problem-solving process.
Tracks reasoning patterns, decisions, and outcomes for learning.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict
import threading


class ReasoningObserver:
    """Observes and logs reasoning processes for later analysis."""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        self.current_session = None
        self.current_task = None
        self.reasoning_log = []
        self.decisions = []
        self._lock = threading.Lock()
        
        # In-memory buffer before flushing to disk
        self._buffer_size = 10
        self._buffer = []
    
    def start_session(self, session_id: str, context: Dict = None):
        """Start observing a new session."""
        with self._lock:
            self.current_session = {
                'session_id': session_id,
                'start_time': datetime.utcnow().isoformat(),
                'context': context or {},
                'tasks': []
            }
            self.reasoning_log = []
            self.decisions = []
    
    def start_task(self, task_id: str, task_type: str, description: str):
        """Start observing a new task within the session."""
        with self._lock:
            self.current_task = {
                'task_id': task_id,
                'task_type': task_type,
                'description': description,
                'start_time': datetime.utcnow().isoformat(),
                'steps': [],
                'decisions': [],
                'outcomes': []
            }
    
    def log_reasoning_step(self, step_type: str, content: str, 
                          metadata: Dict = None):
        """Log a reasoning step."""
        with self._lock:
            step = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': step_type,
                'content': content,
                'metadata': metadata or {}
            }
            self.reasoning_log.append(step)
            
            if self.current_task:
                self.current_task['steps'].append(step)
            
            self._buffer.append(step)
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def log_decision(self, decision_type: str, choice: str, 
                     alternatives: List[str] = None, rationale: str = None):
        """Log a decision made during problem-solving."""
        with self._lock:
            decision = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': decision_type,
                'choice': choice,
                'alternatives': alternatives or [],
                'rationale': rationale
            }
            self.decisions.append(decision)
            
            if self.current_task:
                self.current_task['decisions'].append(decision)
    
    def log_outcome(self, outcome_type: str, result: Any, 
                    success: bool, details: Dict = None):
        """Log the outcome of a step or task."""
        with self._lock:
            outcome = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': outcome_type,
                'result': str(result),
                'success': success,
                'details': details or {}
            }
            
            if self.current_task:
                self.current_task['outcomes'].append(outcome)
            
            # Flush buffer on outcome to ensure logs are saved
            if self._buffer:
                self._flush_buffer()
    
    def end_task(self, success: bool, summary: str = None,
                 lessons: List[str] = None):
        """End observing the current task."""
        with self._lock:
            if self.current_task and self.current_session:
                self.current_task['end_time'] = datetime.utcnow().isoformat()
                self.current_task['success'] = success
                self.current_task['summary'] = summary
                self.current_task['lessons'] = lessons
                
                self.current_session['tasks'].append(self.current_task)
                
                # Save task to disk
                self._save_task(self.current_task)
                
                self.current_task = None
    
    def end_session(self) -> Dict:
        """End the current session and return summary."""
        with self._lock:
            if self.current_session:
                self.current_session['end_time'] = datetime.utcnow().isoformat()
                
                # Calculate session stats
                tasks = self.current_session['tasks']
                completed = sum(1 for t in tasks if t.get('success', False))
                failed = sum(1 for t in tasks if not t.get('success', True))
                
                self.current_session['stats'] = {
                    'total_tasks': len(tasks),
                    'successful': completed,
                    'failed': failed,
                    'success_rate': completed / len(tasks) if tasks else 0
                }
                
                # Save session
                self._save_session(self.current_session)
                
                session = self.current_session
                self.current_session = None
                return session
            
            return {}
    
    def _flush_buffer(self):
        """Flush buffered log entries to disk."""
        if not self._buffer:
            return
        
        log_file = self.log_dir / 'observer_buffer.jsonl'
        with open(log_file, 'a') as f:
            for entry in self._buffer:
                f.write(json.dumps(entry) + '\n')
        self._buffer = []
    
    def _save_task(self, task: Dict):
        """Save task log to disk."""
        task_file = self.log_dir / f"task_{task['task_id']}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
    
    def _save_session(self, session: Dict):
        """Save session log to disk."""
        session_file = self.log_dir / f"session_{session['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
    
    def get_current_session(self) -> Optional[Dict]:
        """Get the current session data."""
        return self.current_session
    
    def analyze_reasoning_patterns(self, session_id: str = None) -> Dict:
        """Analyze reasoning patterns from logs."""
        analysis = {
            'reasoning_types': defaultdict(int),
            'decision_patterns': defaultdict(int),
            'success_patterns': [],
            'failure_patterns': []
        }
        
        # Load sessions from disk
        if session_id:
            session_file = self.log_dir / f"session_{session_id}.json"
            if session_file.exists():
                with open(session_file) as f:
                    sessions = [json.load(f)]
            else:
                sessions = []
        else:
            # Load all sessions
            sessions = []
            for f in self.log_dir.glob('session_*.json'):
                with open(f) as fp:
                    sessions.append(json.load(fp))
        
        for session in sessions:
            for task in session.get('tasks', []):
                # Analyze reasoning types
                for step in task.get('steps', []):
                    analysis['reasoning_types'][step.get('type', 'unknown')] += 1
                
                # Analyze decisions
                for decision in task.get('decisions', []):
                    analysis['decision_patterns'][decision.get('type', 'unknown')] += 1
                
                # Separate success and failure patterns
                if task.get('success'):
                    analysis['success_patterns'].append({
                        'task_type': task.get('task_type'),
                        'steps': len(task.get('steps', [])),
                        'decisions': len(task.get('decisions', []))
                    })
                else:
                    analysis['failure_patterns'].append({
                        'task_type': task.get('task_type'),
                        'steps': len(task.get('steps', [])),
                        'decisions': len(task.get('decisions', []))
                    })
        
        return dict(analysis)


class ReasoningTracker:
    """Context manager for easy reasoning tracking."""
    
    def __init__(self, observer: ReasoningObserver, task_id: str,
                 task_type: str, description: str):
        self.observer = observer
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.success = False
        self.summary = None
        self.lessons = []
    
    def __enter__(self):
        self.observer.start_task(self.task_id, self.task_type, self.description)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.success = exc_type is None
        if exc_type:
            self.summary = str(exc_val)
        self.observer.end_task(self.success, self.summary, self.lessons)
    
    def add_lesson(self, lesson: str):
        """Add a lesson learned during the task."""
        self.lessons.append(lesson)


# Global instance
_observer_instance = None
_instance_lock = threading.Lock()


def get_observer() -> ReasoningObserver:
    """Get or create the global observer instance."""
    global _observer_instance
    with _instance_lock:
        if _observer_instance is None:
            _observer_instance = ReasoningObserver()
    return _observer_instance