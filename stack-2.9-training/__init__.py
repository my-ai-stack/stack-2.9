"""
Self-Evolution System for Stack 2.9
A self-improvement infrastructure that allows the AI to:
1. Observe its own problem-solving process
2. Learn from successes and failures
3. Remember patterns across sessions
4. Apply learned knowledge to new problems
5. Gradually improve itself
"""

from .memory import PersistentMemory, get_memory
from .observer import ReasoningObserver, ReasoningTracker, get_observer
from .learner import ExperienceLearner, get_learner
from .apply import PatternApplicator, ActionExecutor, get_applicator, get_executor
from .trainer import SelfTrainer, TrainingScheduler, get_trainer, get_scheduler

__all__ = [
    # Memory
    'PersistentMemory',
    'get_memory',
    # Observer
    'ReasoningObserver',
    'ReasoningTracker',
    'get_observer',
    # Learner
    'ExperienceLearner',
    'get_learner',
    # Apply
    'PatternApplicator',
    'ActionExecutor',
    'get_applicator',
    'get_executor',
    # Trainer
    'SelfTrainer',
    'TrainingScheduler',
    'get_trainer',
    'get_scheduler',
]

__version__ = '1.0.0'