"""
Apply System - Applies learned patterns to new tasks.
Uses memory and learning to inform decision-making on new problems.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .memory import get_memory
from .observer import get_observer
from .learner import get_learner


class PatternApplicator:
    """Applies learned patterns and knowledge to new tasks."""
    
    def __init__(self, memory=None, observer=None, learner=None):
        self.memory = memory or get_memory()
        self.observer = observer or get_observer()
        self.learner = learner or get_learner()
        
        self.max_context_patterns = 5
        self.min_similarity_threshold = 0.4
    
    def prepare_context(self, task_type: str, task_description: str) -> Dict:
        """Prepare relevant context for a new task based on learned patterns."""
        context = {
            'task_type': task_type,
            'task_description': task_description,
            'relevant_patterns': [],
            'lessons': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Find similar past tasks
        similar = self.memory.find_similar(
            task_description, 
            limit=self.max_context_patterns,
            min_similarity=self.min_similarity_threshold
        )
        
        context['relevant_patterns'] = [
            {
                'content': p['content'],
                'success_rate': p.get('success_rate', 0),
                'similarity': p.get('similarity', 0)
            }
            for p in similar
        ]
        
        # Get relevant lessons
        lessons = self.memory.get_lessons(verified_only=False)
        relevant_lessons = [
            l for l in lessons 
            if task_type.lower() in l.get('description', '').lower() or
               task_type.lower() in l.get('title', '').lower()
        ]
        
        context['lessons'] = [
            {
                'title': l['title'],
                'description': l['description'],
                'success_count': l.get('success_count', 0),
                'failure_count': l.get('failure_count', 0)
            }
            for l in relevant_lessons[:5]
        ]
        
        # Get warnings from failure patterns
        for pattern in context['relevant_patterns']:
            if pattern.get('success_rate', 1) < 0.4:
                context['warnings'].append(
                    f"Similar approach had low success rate: {pattern['content'][:100]}"
                )
        
        # Get improvement suggestions for this task type
        improvements = self.memory.get_pending_improvements()
        relevant_improvements = [
            i for i in improvements 
            if task_type.lower() in i.get('suggestion', '').lower()
        ]
        
        context['suggestions'] = [
            i['suggestion'] for i in relevant_improvements[:3]
        ]
        
        return context
    
    def recommend_action(self, task_type: str, options: List[str],
                        context: Dict) -> Dict:
        """Recommend the best action based on learned patterns."""
        recommendations = []
        
        for option in options:
            # Score each option based on past success
            similar = self.memory.find_similar(
                f"{task_type} {option}",
                limit=3,
                min_similarity=0.3
            )
            
            if similar:
                avg_success = sum(p.get('success_rate', 0) for p in similar) / len(similar)
                total_uses = sum(p.get('use_count', 0) for p in similar)
            else:
                avg_success = 0.5  # Default
                total_uses = 0
            
            # Boost score if we have relevant lessons
            for lesson in context.get('lessons', []):
                if option.lower() in lesson.get('description', '').lower():
                    avg_success = max(avg_success, lesson.get('success_count', 0) / 
                                    max(1, lesson.get('success_count', 0) + lesson.get('failure_count', 0)))
            
            recommendations.append({
                'option': option,
                'score': avg_success,
                'confidence': min(1.0, total_uses / 10),
                'based_on': len(similar) if similar else 0
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'recommendations': recommendations,
            'best_option': recommendations[0]['option'] if recommendations else None,
            'reasoning': self._generate_reasoning(recommendations, context)
        }
    
    def _generate_reasoning(self, recommendations: List[Dict], 
                          context: Dict) -> str:
        """Generate human-readable reasoning for recommendations."""
        if not recommendations:
            return "No historical data available for this task type."
        
        best = recommendations[0]
        
        if best.get('based_on', 0) > 0:
            reason = f"Recommended '{best['option']}' based on {best['based_on']} similar past tasks "
            reason += f"with {best['score']:.0%} success rate."
        else:
            reason = f"Recommending '{best['option']}' as default option."
        
        # Add warning if applicable
        for warning in context.get('warnings', [])[:1]:
            reason += f"\nWarning: {warning[:100]}"
        
        return reason
    
    def log_task_start(self, task_id: str, task_type: str, 
                      task_description: str) -> Dict:
        """Log the start of a new task with prepared context."""
        context = self.prepare_context(task_type, task_description)
        
        # Also start observer tracking
        self.observer.start_task(task_id, task_type, task_description)
        
        # Log the context for future learning
        self.observer.log_reasoning_step(
            step_type='context_preparation',
            content=f"Loaded {len(context['relevant_patterns'])} relevant patterns",
            metadata={'context': context}
        )
        
        return context
    
    def log_task_decision(self, decision_type: str, choice: str,
                         alternatives: List[str] = None, rationale: str = None):
        """Log a decision made during task execution."""
        self.observer.log_decision(
            decision_type=decision_type,
            choice=choice,
            alternatives=alternatives or [],
            rationale=rationale
        )
        
        # Also log to memory for pattern storage
        # (will be used for future learning)
    
    def log_task_outcome(self, task_id: str, task_type: str, success: bool,
                        result: Any = None):
        """Log task outcome and trigger learning."""
        self.observer.log_outcome(
            outcome_type='task_completion',
            result=result,
            success=success
        )
        
        # Get current task data for learning
        session = self.observer.get_current_session()
        if session:
            current_task = None
            for task in session.get('tasks', []):
                if task.get('task_id') == task_id:
                    current_task = task
                    break
            
            if current_task:
                # Analyze and learn from this task
                self.learner.analyze_task_outcome(
                    task_id=task_id,
                    task_type=task_type,
                    success=success,
                    steps=current_task.get('steps', []),
                    decisions=current_task.get('decisions', [])
                )
    
    def auto_apply_improvements(self) -> List[Dict]:
        """Automatically apply implemented improvements to future tasks."""
        improvements = self.memory.get_pending_improvements()
        
        applied = []
        for imp in improvements:
            # Apply high-priority improvements
            if imp.get('priority', 5) >= 8:
                applied.append({
                    'improvement': imp['suggestion'],
                    'applied': True
                })
        
        return applied
    
    def get_task_guidance(self, task_type: str, task_description: str) -> Dict:
        """Get comprehensive guidance for a task."""
        context = self.prepare_context(task_type, task_description)
        
        guidance = {
            'overview': f"Task type: {task_type}",
            'what_worked': [],
            'what_to_avoid': [],
            'best_practices': [],
            'specific_suggestions': []
        }
        
        # Extract what worked
        for pattern in context.get('relevant_patterns', []):
            if pattern.get('success_rate', 0) > 0.6:
                guidance['what_worked'].append(pattern['content'][:200])
        
        # Extract what to avoid
        for warning in context.get('warnings', []):
            guidance['what_to_avoid'].append(warning)
        
        # Get lessons
        for lesson in context.get('lessons', []):
            success_rate = lesson.get('success_count', 0) / max(1, 
                lesson.get('success_count', 0) + lesson.get('failure_count', 0))
            if success_rate > 0.7:
                guidance['best_practices'].append(lesson['description'])
        
        # Get suggestions
        guidance['specific_suggestions'] = context.get('suggestions', [])
        
        return guidance


class ActionExecutor:
    """Executes actions with built-in learning and adaptation."""
    
    def __init__(self, applicator: PatternApplicator = None):
        self.applicator = applicator or PatternApplicator()
        self.active_tasks = {}
    
    def execute_with_guidance(self, task_id: str, task_type: str,
                             task_description: str, 
                             executor_func) -> Any:
        """Execute a task with learned guidance."""
        # Get guidance
        guidance = self.applicator.get_task_guidance(task_type, task_description)
        
        # Log task start
        context = self.applicator.log_task_start(task_id, task_type, task_description)
        
        # Track task
        self.active_tasks[task_id] = {
            'task_type': task_type,
            'guidance': guidance,
            'start_time': datetime.utcnow().isoformat()
        }
        
        # Execute with context passed to function
        try:
            result = executor_func(guidance)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        
        # Log outcome
        self.applicator.log_task_outcome(task_id, task_type, success, result)
        
        # Clean up
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        return result
    
    def get_active_task_context(self, task_id: str) -> Optional[Dict]:
        """Get the context for an active task."""
        return self.active_tasks.get(task_id)


# Global instance
_applicator_instance = None


def get_applicator() -> PatternApplicator:
    """Get or create the global applicator instance."""
    global _applicator_instance
    if _applicator_instance is None:
        _applicator_instance = PatternApplicator()
    return _applicator_instance


def get_executor() -> ActionExecutor:
    """Get or create the global executor instance."""
    return ActionExecutor()