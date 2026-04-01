"""
Persistent Memory System for Self-Evolution
Stores learned patterns and enables similarity-based retrieval using vector embeddings.
"""

import json
import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import numpy as np


class PersistentMemory:
    """Vector-based persistent memory with SQLite storage."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        self.db_path = self.data_dir / 'memory.db'
        self.embeddings_dir = self.data_dir / 'embeddings'
        self.embeddings_dir.mkdir(exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with memory schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Core memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding_id TEXT UNIQUE,
                category TEXT,
                success_rate REAL DEFAULT 0.5,
                use_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Lessons learned table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                pattern TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                contexts TEXT,
                created_at TEXT NOT NULL,
                verified BOOLEAN DEFAULT 0
            )
        ''')
        
        # Improvement suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion TEXT NOT NULL,
                category TEXT,
                priority INTEGER DEFAULT 5,
                implemented BOOLEAN DEFAULT 0,
                impact_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                implemented_at TEXT
            )
        ''')
        
        # Session history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                learnings TEXT
            )
        ''')
        
        # Indexes for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories(embedding_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_pattern ON lessons(pattern)')
        
        conn.commit()
        conn.close()
    
    def _generate_embedding_id(self, content: str) -> str:
        """Generate a deterministic ID for embedding storage."""
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute a simple hash-based pseudo-embedding for similarity."""
        # Using hash-based approach - in production, use actual embeddings
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        # Create a simple embedding vector from hash
        np.random.seed(hash_val % (2**32))
        return np.random.randn(128).astype(np.float32)
    
    def store_memory(self, content: str, category: str = 'general', 
                     metadata: Dict = None) -> int:
        """Store a new memory with embedding."""
        embedding_id = self._generate_embedding_id(content)
        embedding = self._compute_embedding(content)
        
        # Save embedding
        np.save(self.embeddings_dir / f'{embedding_id}.npy', embedding)
        
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (content, embedding_id, category, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (content, embedding_id, category, now, now, 
              json.dumps(metadata) if metadata else None))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return memory_id
    
    def find_similar(self, query: str, limit: int = 5, 
                     min_similarity: float = 0.3) -> List[Dict]:
        """Find similar memories using vector similarity."""
        query_embedding = self._compute_embedding(query)
        
        memories = self.get_all_memories()
        results = []
        
        for mem in memories:
            emb_path = self.embeddings_dir / f"{mem['embedding_id']}.npy"
            if emb_path.exists():
                stored_emb = np.load(emb_path)
                similarity = float(np.dot(query_embedding, stored_emb) / 
                                 (np.linalg.norm(query_embedding) * np.linalg.norm(stored_emb) + 1e-8))
                
                if similarity >= min_similarity:
                    results.append({
                        **mem,
                        'similarity': similarity
                    })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def get_all_memories(self, category: str = None) -> List[Dict]:
        """Retrieve all memories, optionally filtered by category."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT * FROM memories WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM memories')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'content', 'embedding_id', 'category', 'success_rate', 
                   'use_count', 'last_used', 'created_at', 'updated_at', 'metadata']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def update_memory_stats(self, memory_id: int, success: bool):
        """Update success/failure stats for a memory."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT success_rate, use_count FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        
        if row:
            old_rate, use_count = row
            new_count = use_count + 1
            # Running average update
            new_rate = (old_rate * use_count + (1.0 if success else 0.0)) / new_count
            
            cursor.execute('''
                UPDATE memories 
                SET success_rate = ?, use_count = ?, last_used = ?
                WHERE id = ?
            ''', (new_rate, new_count, datetime.utcnow().isoformat(), memory_id))
        
        conn.commit()
        conn.close()
    
    def add_lesson(self, title: str, description: str, pattern: str = None,
                   context: str = None) -> int:
        """Add a new lesson learned."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        contexts = json.dumps([context]) if context else json.dumps([])
        
        cursor.execute('''
            INSERT INTO lessons (title, description, pattern, contexts, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, pattern, contexts, datetime.utcnow().isoformat()))
        
        lesson_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return lesson_id
    
    def update_lesson_stats(self, lesson_id: int, success: bool):
        """Update lesson success/failure counts."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if success:
            cursor.execute('UPDATE lessons SET success_count = success_count + 1 WHERE id = ?', (lesson_id,))
        else:
            cursor.execute('UPDATE lessons SET failure_count = failure_count + 1 WHERE id = ?', (lesson_id,))
        
        conn.commit()
        conn.close()
    
    def get_lessons(self, verified_only: bool = False) -> List[Dict]:
        """Retrieve lessons, optionally filtered by verification status."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if verified_only:
            cursor.execute('SELECT * FROM lessons WHERE verified = 1')
        else:
            cursor.execute('SELECT * FROM lessons')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'title', 'description', 'pattern', 'success_count', 
                   'failure_count', 'contexts', 'created_at', 'verified']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def add_improvement(self, suggestion: str, category: str = 'general',
                        priority: int = 5) -> int:
        """Add an improvement suggestion."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO improvements (suggestion, category, priority, created_at)
            VALUES (?, ?, ?, ?)
        ''', (suggestion, category, priority, datetime.utcnow().isoformat()))
        
        imp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return imp_id
    
    def mark_improvement_implemented(self, improvement_id: int, impact_score: float = 0.0):
        """Mark an improvement as implemented."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE improvements 
            SET implemented = 1, implemented_at = ?, impact_score = ?
            WHERE id = ?
        ''', (datetime.utcnow().isoformat(), impact_score, improvement_id))
        
        conn.commit()
        conn.close()
    
    def get_pending_improvements(self) -> List[Dict]:
        """Get unimplemented improvements sorted by priority."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM improvements 
            WHERE implemented = 0 
            ORDER BY priority DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'suggestion', 'category', 'priority', 'implemented',
                  'impact_score', 'created_at', 'implemented_at']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def log_session(self, session_id: str) -> int:
        """Log the start of a new session."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (session_id, started_at)
            VALUES (?, ?)
        ''', (session_id, datetime.utcnow().isoformat()))
        
        session_id_db = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id_db
    
    def end_session(self, session_id: str, tasks_completed: int, 
                    tasks_failed: int, learnings: str = None):
        """End a session and record its stats."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET ended_at = ?, tasks_completed = ?, tasks_failed = ?, learnings = ?
            WHERE session_id = ?
        ''', (datetime.utcnow().isoformat(), tasks_completed, tasks_failed, 
              learnings, session_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        stats = {}
        
        # Memory stats
        cursor.execute('SELECT COUNT(*), AVG(success_rate), SUM(use_count) FROM memories')
        mem_stats = cursor.fetchone()
        stats['total_memories'] = mem_stats[0]
        stats['avg_success_rate'] = round(mem_stats[1] or 0, 3)
        stats['total_uses'] = mem_stats[2] or 0
        
        # Lesson stats
        cursor.execute('SELECT COUNT(*), SUM(success_count), SUM(failure_count) FROM lessons')
        lesson_stats = cursor.fetchone()
        stats['total_lessons'] = lesson_stats[0]
        stats['lesson_successes'] = lesson_stats[1] or 0
        stats['lesson_failures'] = lesson_stats[2] or 0
        
        # Improvement stats
        cursor.execute('SELECT COUNT(*) FROM improvements WHERE implemented = 0')
        stats['pending_improvements'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*), AVG(impact_score) FROM improvements WHERE implemented = 1')
        imp_stats = cursor.fetchone()
        stats['implemented_improvements'] = imp_stats[0]
        stats['avg_impact'] = round(imp_stats[1] or 0, 3)
        
        # Session stats
        cursor.execute('SELECT SUM(tasks_completed), SUM(tasks_failed) FROM sessions')
        session_stats = cursor.fetchone()
        stats['total_tasks_completed'] = session_stats[0] or 0
        stats['total_tasks_failed'] = session_stats[1] or 0
        
        if stats['total_tasks_completed'] + stats['total_tasks_failed'] > 0:
            stats['overall_success_rate'] = round(
                stats['total_tasks_completed'] / 
                (stats['total_tasks_completed'] + stats['total_tasks_failed']), 3)
        else:
            stats['overall_success_rate'] = 0.0
        
        conn.close()
        
        return stats


# Global instance for easy importing
_memory_instance = None


def get_memory() -> PersistentMemory:
    """Get or create the global memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = PersistentMemory()
    return _memory_instance