"""
Trainer System - Fine-tunes the AI using accumulated knowledge.
Generates training data and manages self-improvement cycles.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from collections import Counter
import random

from .memory import get_memory
from .learner import get_learner
from .apply import get_applicator


class SelfTrainer:
    """Manages self-improvement through training data generation and fine-tuning."""
    
    def __init__(self, memory=None, learner=None, applicator=None):
        self.memory = memory or get_memory()
        self.learner = learner or get_learner()
        self.applicator = applicator or get_applicator()
        
        self.training_data_dir = Path(os.path.join(
            os.path.dirname(__file__), '..', 'training-data'
        ))
        self.training_data_dir.mkdir(exist_ok=True, parents=True)
        
        self.min_examples_for_training = 10
        self.training_batch_size = 20
    
    def generate_training_examples(self, task_type: str = None) -> List[Dict]:
        """Generate training examples from learned patterns."""
        examples = []
        
        # Get all memories
        memories = self.memory.get_all_memories()
        
        # Filter by task type if specified
        if task_type:
            memories = [m for m in memories 
                       if task_type.lower() in m.get('content', '').lower()]
        
        # Generate positive examples from high-success patterns
        positive_memories = [m for m in memories if m.get('success_rate', 0) > 0.6]
        
        for mem in positive_memories[:self.training_batch_size]:
            example = {
                'input': self._generate_input_from_memory(mem),
                'output': mem['content'],
                'metadata': {
                    'type': 'positive',
                    'success_rate': mem.get('success_rate', 0),
                    'use_count': mem.get('use_count', 0),
                    'category': mem.get('category', 'general')
                }
            }
            examples.append(example)
        
        # Generate negative examples from failure patterns
        negative_memories = [m for m in memories if m.get('success_rate', 0) < 0.4]
        
        for mem in negative_memories[:self.training_batch_size // 2]:
            example = {
                'input': self._generate_input_from_memory(mem),
                'output': f"Avoid: {mem['content']}",
                'metadata': {
                    'type': 'negative',
                    'success_rate': mem.get('success_rate', 0),
                    'category': mem.get('category', 'general')
                }
            }
            examples.append(example)
        
        # Add examples from verified lessons
        lessons = self.memory.get_lessons(verified_only=False)
        for lesson in lessons[:10]:
            if lesson.get('success_count', 0) >= self.min_examples_for_training:
                example = {
                    'input': f"How to handle: {lesson.get('title', '')}",
                    'output': lesson['description'],
                    'metadata': {
                        'type': 'lesson',
                        'success_count': lesson.get('success_count', 0),
                        'failure_count': lesson.get('failure_count', 0)
                    }
                }
                examples.append(example)
        
        return examples
    
    def _generate_input_from_memory(self, memory: Dict) -> str:
        """Generate a realistic input prompt from memory content."""
        category = memory.get('category', 'task')
        content = memory.get('content', '')
        
        # Create a realistic input scenario
        if 'success' in category:
            return f"Given a problem similar to: {content[:100]}, how would you solve it?"
        elif 'failure' in category:
            return f"Avoid the approach that led to: {content[:100]}. What should be done instead?"
        else:
            return f"Task: {content[:150]}"
    
    def create_training_dataset(self, task_type: str = None,
                               output_file: str = None) -> Dict:
        """Create a training dataset file from accumulated knowledge."""
        examples = self.generate_training_examples(task_type)
        
        if len(examples) < self.min_examples_for_training:
            return {
                'status': 'insufficient_data',
                'available': len(examples),
                'required': self.min_examples_for_training
            }
        
        if output_file is None:
            output_file = self.training_data_dir / f"training_{task_type or 'general'}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Write as JSONL
        with open(output_file, 'w') as f:
            for ex in examples:
                f.write(json.dumps(ex) + '\n')
        
        return {
            'status': 'created',
            'file': str(output_file),
            'examples': len(examples),
            'positive': len([e for e in examples if e['metadata']['type'] == 'positive']),
            'negative': len([e for e in examples if e['metadata']['type'] == 'negative'])
        }
    
    def run_improvement_cycle(self) -> Dict:
        """Run a complete self-improvement cycle."""
        cycle_results = {
            'started_at': datetime.utcnow().isoformat(),
            'steps': []
        }
        
        # Step 1: Extract patterns
        patterns = self.learner.extract_patterns()
        cycle_results['steps'].append({
            'step': 'pattern_extraction',
            'status': 'completed',
            'patterns_found': len(patterns.get('successful_approaches', [])) +
                           len(patterns.get('failure_patterns', []))
        })
        
        # Step 2: Analyze and generate improvements
        learning_result = self.learner.continuous_learning_cycle()
        cycle_results['steps'].append({
            'step': 'learning_analysis',
            'status': 'completed',
            'new_suggestions': learning_result.get('new_suggestions', 0)
        })
        
        # Step 3: Auto-apply improvements
        applied = self.applicator.auto_apply_improvements()
        cycle_results['steps'].append({
            'step': 'apply_improvements',
            'status': 'completed',
            'applied_count': len(applied)
        })
        
        # Step 4: Generate training data
        training_result = self.create_training_dataset()
        cycle_results['steps'].append({
            'step': 'generate_training',
            'status': training_result.get('status', 'skipped'),
            'examples': training_result.get('examples', 0)
        })
        
        # Step 5: Get current stats
        stats = self.memory.get_stats()
        cycle_results['steps'].append({
            'step': 'stat_update',
            'status': 'completed',
            'overall_success_rate': stats.get('overall_success_rate', 0)
        })
        
        cycle_results['completed_at'] = datetime.utcnow().isoformat()
        
        # Save cycle results
        cycle_file = self.training_data_dir / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(cycle_file, 'w') as f:
            json.dump(cycle_results, f, indent=2)
        
        return cycle_results
    
    def get_improvement_recommendations(self) -> List[Dict]:
        """Get prioritized improvement recommendations."""
        improvements = self.memory.get_pending_improvements()
        
        recommendations = []
        for imp in improvements:
            # Score based on priority and potential impact
            score = imp.get('priority', 5) / 10.0
            
            recommendations.append({
                'id': imp['id'],
                'suggestion': imp['suggestion'],
                'category': imp['category'],
                'priority': imp['priority'],
                'score': score,
                'rationale': self._generate_improvement_rationale(imp)
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:10]
    
    def _generate_improvement_rationale(self, improvement: Dict) -> str:
        """Generate rationale for an improvement suggestion."""
        category = improvement.get('category', 'general')
        
        if category == 'error_handling':
            return "Addressing this would reduce failure rates in similar tasks"
        elif category == 'task_decomposition':
            return "Breaking down complex tasks improves success probability"
        elif category == 'decision_making':
            return "More decision checkpoints reduce cognitive load and errors"
        else:
            return "General improvement opportunity identified from pattern analysis"
    
    def benchmark_improvements(self) -> Dict:
        """Benchmark current performance against improvements."""
        stats = self.memory.get_stats()
        
        benchmark = {
            'timestamp': datetime.utcnow().isoformat(),
            'current_metrics': {
                'success_rate': stats.get('overall_success_rate', 0),
                'total_tasks': stats.get('total_tasks_completed', 0) + stats.get('total_tasks_failed', 0),
                'memories_stored': stats.get('total_memories', 0),
                'lessons_learned': stats.get('total_lessons', 0),
                'improvements_implemented': stats.get('implemented_improvements', 0)
            },
            'improvement_capacity': {
                'pending_improvements': stats.get('pending_improvements', 0),
                'unverified_lessons': len([l for l in self.memory.get_lessons() 
                                         if not l.get('verified')])
            },
            'recommendations': self.get_improvement_recommendations()[:5]
        }
        
        return benchmark
    
    def export_knowledge(self, output_file: str = None) -> Dict:
        """Export all knowledge for external use."""
        if output_file is None:
            output_file = self.training_data_dir / f"knowledge_export_{datetime.now().strftime('%Y%m%d')}.json"
        
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'memories': self.memory.get_all_memories(),
            'lessons': self.memory.get_lessons(),
            'improvements': self.memory.get_pending_improvements(),
            'stats': self.memory.get_stats()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return {
            'status': 'exported',
            'file': str(output_file),
            'memory_count': len(export_data['memories']),
            'lesson_count': len(export_data['lessons'])
        }
    
    def import_knowledge(self, input_file: str) -> Dict:
        """Import knowledge from external source."""
        with open(input_file) as f:
            imported = json.load(f)
        
        imported_count = 0
        
        # Import memories
        for mem in imported.get('memories', []):
            self.memory.store_memory(
                content=mem['content'],
                category=mem.get('category', 'imported'),
                metadata=mem.get('metadata')
            )
            imported_count += 1
        
        # Import lessons
        for lesson in imported.get('lessons', []):
            self.memory.add_lesson(
                title=lesson['title'],
                description=lesson['description'],
                pattern=lesson.get('pattern')
            )
            imported_count += 1
        
        return {
            'status': 'imported',
            'items': imported_count
        }


class TrainingScheduler:
    """Schedules and manages periodic training cycles."""
    
    def __init__(self, trainer: SelfTrainer = None):
        self.trainer = trainer or SelfTrainer()
        self.schedule_file = self.trainer.training_data_dir / 'schedule.json'
        self._load_schedule()
    
    def _load_schedule(self):
        """Load the training schedule."""
        if self.schedule_file.exists():
            with open(self.schedule_file) as f:
                self.schedule = json.load(f)
        else:
            self.schedule = {
                'enabled': False,
                'interval_hours': 24,
                'last_run': None,
                'total_runs': 0
            }
    
    def _save_schedule(self):
        """Save the training schedule."""
        with open(self.schedule_file, 'w') as f:
            json.dump(self.schedule, f, indent=2)
    
    def enable_scheduled_training(self, interval_hours: int = 24):
        """Enable scheduled training."""
        self.schedule['enabled'] = True
        self.schedule['interval_hours'] = interval_hours
        self._save_schedule()
    
    def disable_scheduled_training(self):
        """Disable scheduled training."""
        self.schedule['enabled'] = False
        self._save_schedule()
    
    def should_run(self) -> bool:
        """Check if a training cycle should run."""
        if not self.schedule.get('enabled'):
            return False
        
        last_run = self.schedule.get('last_run')
        if not last_run:
            return True
        
        last_time = datetime.fromisoformat(last_run)
        interval = timedelta(hours=self.schedule.get('interval_hours', 24))
        
        return datetime.now() - last_time >= interval
    
    def run_if_due(self) -> Optional[Dict]:
        """Run training if due, otherwise return None."""
        if self.should_run():
            result = self.trainer.run_improvement_cycle()
            
            self.schedule['last_run'] = datetime.utcnow().isoformat()
            self.schedule['total_runs'] = self.schedule.get('total_runs', 0) + 1
            self._save_schedule()
            
            return result
        
        return None
    
    def get_schedule_status(self) -> Dict:
        """Get current schedule status."""
        return {
            'enabled': self.schedule.get('enabled', False),
            'interval_hours': self.schedule.get('interval_hours', 24),
            'last_run': self.schedule.get('last_run'),
            'total_runs': self.schedule.get('total_runs', 0),
            'next_due': self._next_due_time()
        }
    
    def _next_due_time(self) -> Optional[str]:
        """Calculate next due time."""
        if not self.schedule.get('enabled'):
            return None
        
        last_run = self.schedule.get('last_run')
        if not last_run:
            return "now"
        
        last_time = datetime.fromisoformat(last_run)
        interval = timedelta(hours=self.schedule.get('interval_hours', 24))
        next_time = last_time + interval
        
        return next_time.isoformat()


# Global instances
_trainer_instance = None
_scheduler_instance = None


def get_trainer() -> SelfTrainer:
    """Get or create the global trainer instance."""
    global _trainer_instance
    if _trainer_instance is None:
        _trainer_instance = SelfTrainer()
    return _trainer_instance


def get_scheduler() -> TrainingScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TrainingScheduler()
    return _scheduler_instance