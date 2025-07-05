from datetime import datetime
from jarvus_app.db import db
import json
from typing import Dict, Any, Optional

class ShortTermMemory(db.Model):
    """Short-term memory for thread-level persistence (conversation context)"""
    __tablename__ = 'short_term_memory'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('history.id'), nullable=False)
    
    # State data stored as JSON
    state_data = db.Column(db.JSON, nullable=False, default=dict)
    
    # Metadata for checkpoint management
    checkpoint_id = db.Column(db.String(255), nullable=True)
    step_number = db.Column(db.Integer, default=0)
    parent_checkpoint_id = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='short_term_memories')
    agent = db.relationship('History', backref='short_term_memories')

    def __repr__(self):
        return f"<ShortTermMemory thread_id={self.thread_id} step={self.step_number}>"

    @classmethod
    def get_latest_checkpoint(cls, thread_id: str, user_id: int) -> Optional['ShortTermMemory']:
        """Get the latest checkpoint for a thread"""
        return cls.query.filter_by(
            thread_id=thread_id, 
            user_id=user_id
        ).order_by(cls.step_number.desc()).first()

    @classmethod
    def get_checkpoint_history(cls, thread_id: str, user_id: int) -> list['ShortTermMemory']:
        """Get all checkpoints for a thread in chronological order"""
        return cls.query.filter_by(
            thread_id=thread_id, 
            user_id=user_id
        ).order_by(cls.step_number.asc()).all()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LangGraph compatibility"""
        return {
            'values': self.state_data,
            'config': {
                'configurable': {
                    'thread_id': self.thread_id,
                    'checkpoint_id': self.checkpoint_id,
                    'step': self.step_number
                }
            },
            'metadata': {
                'source': 'loop',
                'step': self.step_number,
                'thread_id': self.thread_id,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        }


class LongTermMemory(db.Model):
    """Long-term memory for cross-thread persistence (user-specific data)"""
    __tablename__ = 'long_term_memory'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Memory organization
    namespace = db.Column(db.String(255), nullable=False, index=True)  # e.g., "memories", "preferences"
    memory_id = db.Column(db.String(255), nullable=False, index=True)  # UUID for the memory
    
    # Memory content
    memory_data = db.Column(db.JSON, nullable=False, default=dict)
    
    # For semantic search
    embedding_vector = db.Column(db.Text, nullable=True)  # Store as JSON string
    search_text = db.Column(db.Text, nullable=True)  # Text for semantic search
    
    # Metadata
    memory_type = db.Column(db.String(50), nullable=False, default='fact')  # fact, preference, rule, etc.
    importance_score = db.Column(db.Float, default=1.0)  # For memory prioritization
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='long_term_memories')

    def __repr__(self):
        return f"<LongTermMemory namespace={self.namespace} memory_id={self.memory_id}>"

    @classmethod
    def search_memories(cls, user_id: int, namespace: str, query: str = None, limit: int = 10) -> list['LongTermMemory']:
        """Search memories by namespace and optionally by query text"""
        query_obj = cls.query.filter_by(user_id=user_id, namespace=namespace)
        
        if query:
            # Simple text search for now - can be enhanced with semantic search
            query_obj = query_obj.filter(cls.search_text.contains(query))
        
        return query_obj.order_by(cls.importance_score.desc(), cls.last_accessed.desc()).limit(limit).all()

    @classmethod
    def get_memory(cls, user_id: int, namespace: str, memory_id: str) -> Optional['LongTermMemory']:
        """Get a specific memory by ID"""
        return cls.query.filter_by(
            user_id=user_id,
            namespace=namespace,
            memory_id=memory_id
        ).first()

    def update_access_time(self):
        """Update the last accessed time"""
        self.last_accessed = datetime.utcnow()
        db.session.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'id': self.memory_id,
            'data': self.memory_data,
            'type': self.memory_type,
            'importance': self.importance_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }


class MemoryEmbedding(db.Model):
    """Store embeddings for semantic search in long-term memory"""
    __tablename__ = 'memory_embeddings'

    id = db.Column(db.Integer, primary_key=True)
    memory_id = db.Column(db.Integer, db.ForeignKey('long_term_memory.id'), nullable=False)
    
    # Embedding data
    embedding_vector = db.Column(db.Text, nullable=False)  # JSON string of embedding
    embedding_model = db.Column(db.String(100), nullable=False, default='text-embedding-3-small')
    embedding_dimensions = db.Column(db.Integer, nullable=False, default=1536)
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    memory = db.relationship('LongTermMemory', backref='embeddings')

    def __repr__(self):
        return f"<MemoryEmbedding memory_id={self.memory_id} model={self.embedding_model}>"

    def get_vector(self) -> list[float]:
        """Get the embedding vector as a list of floats"""
        try:
            return json.loads(self.embedding_vector)
        except (json.JSONDecodeError, TypeError):
            return [] 