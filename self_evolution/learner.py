"""
Learner System - Extracts improvements from experience.
Analyzes success/failure patterns and generates actionable insights.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict
from pathlib import Path
import os

from .memory import get_memory
from .observer import get_observer


class ExperienceLearner:
    """Analyzes experiences and extracts learning insights."""
    
    def __init__(self, memory=None, observer=None):
        self.memory = memory or get_memory()
        self.observer = observer or get_observer()
        
        self.min_success_for_pattern = 3
        self.min_failure_for_pattern = 2
    
    def analyze_task_outcome(self, task_id: str, task_type: str,
                            success: bool, steps: List[Dict],
                            decisions: List[Dict]) -> Dict:
        """Analyze a task's outcome and extract learnings."""
        learnings = []
        
        # Analyze decision patterns
        good_decisions = [d for d in decisions if d.get('rationale')]
        if success and good_decisions:
            # Document what worked
            for decision in good_decisions:
                self.memory.store_memory(
                    content=f"Task {task_type} succeeded when: {decision.get('choice')} - {decision.get('rationale')}",
                    category='success_pattern',
                    metadata={'task_type': task_type, 'decision': decision.get('choice')}
                )
                learnings.append({
                    'type': 'success_pattern',
                    'content': f"Using {decision.get('choice')} worked well for {task_type}"
                })
        
        if not success:
            # Document failure patterns
            for decision in decisions:
                self.memory.store_memory(
                    content=f"Task {task_type} failed when: {decision.get('choice')}",
                    category='failure_pattern',
                    metadata={'task_type': task_type, 'decision': decision.get('choice')}
                )
                learnings.append({
                    'type': 'failure_pattern',
                    'content': f"Avoid {decision.get('choice')} for {task_type}"
                })
        
        # Generate improvement suggestions based on failures
        if not success:
            suggestions = self._generate_improvements(task_type, steps, decisions)
            for suggestion in suggestions:
                self.memory.add_improvement(
                    suggestion=suggestion['suggestion'],
                    category=suggestion['category'],
                    priority=suggestion['priority']
                )
                learnings.append({
                    'type': 'improvement_suggestion',
                    'content': suggestion['suggestion']
                })
        
        # Update lesson statistics
        lesson_title = f"{task_type} task {'success' if success else 'failure'}"
        lesson_desc = f"Learned from {task_type} task: {len(steps)} steps, {len(decisions)} decisions"
        
        # Find or create lesson
        lessons = self.memory.get_lessons()
        existing = [l for l in lessons if task_type in l.get('title', '')]
        
        if existing:
            self.memory.update_lesson_stats(existing[0]['id'], success)
        else:
            self.memory.add_lesson(
                title=lesson_title,
                description=lesson_desc,
                pattern=task_type
            )
        
        return {
            'learnings': learnings,
            'improvement_suggestions': len([l for l in learnings if l['type'] == 'improvement_suggestion'])
        }
    
    def _generate_improvements(self, task_type: str, steps: List[Dict],
                               decisions: List[Dict]) -> List[Dict]:
        """Generate improvement suggestions based on failure analysis."""
        suggestions = []
        
        # Analyze step patterns
        step_types = defaultdict(int)
        for step in steps:
            step_types[step.get('type', 'unknown')] += 1
        
        # Common failure-based suggestions
        if step_types.get('error', 0) > 2:
            suggestions.append({
                'suggestion': f"Consider error handling improvements for {task_type} tasks",
                'category': 'error_handling',
                'priority': 8
            })
        
        if len(steps) > 10:
            suggestions.append({
                'suggestion': f"Break down {task_type} tasks into smaller steps",
                'category': 'task_decomposition',
                'priority': 7
            })
        
        # Decision-based suggestions
        if not decisions:
            suggestions.append({
                'suggestion': f"Add more decision checkpoints for {task_type} tasks",
                'category': 'decision_making',
                'priority': 6
            })
        
        return suggestions
    
    def extract_patterns(self, lookback_days: int = 7) -> Dict:
        """Extract patterns from recent history."""
        patterns = {
            'successful_approaches': [],
            'failure_patterns': [],
            'recommended_improvements': []
        }
        
        # Get all memories
        memories = self.memory.get_all_memories()
        
        # Analyze success patterns
        success_memories = [m for m in memories 
                          if m.get('success_rate', 0) > 0.7 and m.get('use_count', 0) > 2]
        
        for mem in success_memories[:10]:
            patterns['successful_approaches'].append({
                'content': mem['content'],
                'success_rate': mem['success_rate'],
                'uses': mem['use_count']
            })
        
        # Analyze failure patterns
        failure_memories = [m for m in memories 
                          if m.get('success_rate', 0) < 0.4]
        
        for mem in failure_memories[:10]:
            patterns['failure_patterns'].append({
                'content': mem['content'],
                'success_rate': mem['success_rate']
            })
        
        # Get pending improvements
        improvements = self.memory.get_pending_improvements()
        patterns['recommended_improvements'] = [
            {'suggestion': i['suggestion'], 'priority': i['priority']}
            for i in improvements[:10]
        ]
        
        return patterns
    
    def analyze_session_improvements(self, session_id: str) -> Dict:
        """Analyze a specific session and recommend improvements."""
        observer_data = self.observer.analyze_reasoning_patterns(session_id)
        
        # Get session from observer
        session_file = self.observer.log_dir / f"session_{session_id}.json"
        if not session_file.exists():
            return {'error': 'Session not found'}
        
        with open(session_file) as f:
            session = json.load(f)
        
        recommendations = []
        
        # Analyze task types
        task_success = defaultdict(lambda: {'success': 0, 'failed': 0})
        for task in session.get('tasks', []):
            task_type = task.get('task_type', 'unknown')
            if task.get('success'):
                task_success[task_type]['success'] += 1
            else:
                task_success[task_type]['failed'] += 1
        
        # Generate recommendations
        for task_type, stats in task_success.items():
            if stats['failed'] > stats['success']:
                recommendations.append({
                    'category': 'task_improvement',
                    'task_type': task_type,
                    'suggestion': f"Focus on improving {task_type} task handling",
                    'priority': min(10, 5 + stats['failed'])
                })
        
        return {
            'session_id': session_id,
            'task_stats': dict(task_success),
            'recommendations': recommendations
        }
    
    def generate_learning_report(self) -> Dict:
        """Generate a comprehensive learning report."""
        stats = self.memory.get_stats()
        patterns = self.extract_patterns()
        
        # Calculate improvement metrics
        total_tasks = stats.get('total_tasks_completed', 0) + stats.get('total_tasks_failed', 0)
        if total_tasks > 0:
            improvement_trend = stats.get('overall_success_rate', 0)
        else:
            improvement_trend = 0
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': stats,
            'patterns': patterns,
            'improvement_trend': improvement_trend,
            'top_recommendations': patterns['recommended_improvements'][:5]
        }
    
    def continuous_learning_cycle(self):
        """Run a continuous learning cycle - analyze and improve."""
        # Get all lessons
        lessons = self.memory.get_lessons()
        
        # Find lessons that need verification
        unverified_lessons = [l for l in lessons if not l.get('verified')]
        
        # Mark high-success lessons as verified
        for lesson in lessons:
            total = lesson.get('success_count', 0) + lesson.get('failure_count', 0)
            if total >= self.min_success_for_pattern:
                success_rate = lesson.get('success_count', 0) / total
                if success_rate > 0.7:
                    # Could mark as verified (would need update method)
                    pass
        
        # Generate new improvement suggestions based on patterns
        patterns = self.extract_patterns()
        
        new_suggestions = []
        
        # Check for repetitive failures
        for failure in patterns.get('failure_patterns', [])[:3]:
            # Generate specific improvement
            new_suggestions.append({
                'suggestion': f"Address pattern: {failure.get('content', '')[:100]}",
                'category': 'pattern_improvement',
                'priority': 6
            })
        
        # Add new suggestions
        for suggestion in new_suggestions:
            self.memory.add_improvement(
                suggestion=suggestion['suggestion'],
                category=suggestion['category'],
                priority=suggestion['priority']
            )
        
        return {
            'verified_lessons': len([l for l in lessons if l.get('verified')]),
            'new_suggestions': len(new_suggestions),
            'pending_improvements': len(patterns.get('recommended_improvements', []))
        }


# Global instance
_learner_instance = None


def get_learner() -> ExperienceLearner:
    """Get or create the global learner instance."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = ExperienceLearner()
    return _learner_instance