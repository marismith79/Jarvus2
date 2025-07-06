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
        """Convert to dictionary format"""
        return {
            'thread_id': self.thread_id,
            'state_data': self.state_data,
            'checkpoint_id': self.checkpoint_id,
            'step_number': self.step_number,
            'parent_checkpoint_id': self.parent_checkpoint_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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


class HierarchicalMemory(db.Model):
    """Hierarchical memory for contextual state management and influence propagation"""
    __tablename__ = 'hierarchical_memory'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Hierarchical structure
    memory_id = db.Column(db.String(255), nullable=False, index=True)  # UUID for the memory
    parent_id = db.Column(db.String(255), nullable=True, index=True)  # Parent memory ID
    level = db.Column(db.Integer, default=0)  # Hierarchy level (0 = root, 1 = child, etc.)
    path = db.Column(db.String(1000), nullable=True)  # Full path from root (e.g., "vacation/email_preferences")
    
    # Memory content
    name = db.Column(db.String(255), nullable=False)  # Human-readable name
    description = db.Column(db.Text, nullable=True)  # Description of this memory
    context_data = db.Column(db.JSON, nullable=False, default=dict)  # Contextual data
    influence_rules = db.Column(db.JSON, nullable=True)  # Rules for how this affects children
    
    # Metadata
    memory_type = db.Column(db.String(50), nullable=False, default='context')  # context, preference, rule, etc.
    is_active = db.Column(db.Boolean, default=True)  # Whether this context is currently active
    priority = db.Column(db.Integer, default=0)  # Priority for conflict resolution
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='hierarchical_memories')

    def __repr__(self):
        return f"<HierarchicalMemory name={self.name} level={self.level} path={self.path}>"

    @classmethod
    def get_root_contexts(cls, user_id: int) -> list['HierarchicalMemory']:
        """Get all root-level contexts for a user"""
        return cls.query.filter_by(
            user_id=user_id,
            level=0,
            is_active=True
        ).order_by(cls.priority.desc(), cls.last_accessed.desc()).all()

    @classmethod
    def get_children(cls, memory_id: str, user_id: int) -> list['HierarchicalMemory']:
        """Get all children of a memory"""
        return cls.query.filter_by(
            parent_id=memory_id,
            user_id=user_id,
            is_active=True
        ).order_by(cls.priority.desc(), cls.last_accessed.desc()).all()

    @classmethod
    def get_ancestors(cls, memory_id: str, user_id: int) -> list['HierarchicalMemory']:
        """Get all ancestors of a memory (parent, grandparent, etc.)"""
        ancestors = []
        current = cls.query.filter_by(memory_id=memory_id, user_id=user_id).first()
        
        while current and current.parent_id:
            parent = cls.query.filter_by(memory_id=current.parent_id, user_id=user_id).first()
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors

    @classmethod
    def get_descendants(cls, memory_id: str, user_id: int) -> list['HierarchicalMemory']:
        """Get all descendants of a memory (children, grandchildren, etc.)"""
        descendants = []
        children = cls.get_children(memory_id, user_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(cls.get_descendants(child.memory_id, user_id))
        
        return descendants

    @classmethod
    def get_active_contexts(cls, user_id: int) -> list['HierarchicalMemory']:
        """Get all active contexts for a user"""
        return cls.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(cls.level.asc(), cls.priority.desc()).all()

    def get_influence_context(self) -> Dict[str, Any]:
        """Get the combined influence context from this memory and its ancestors"""
        context = self.context_data.copy()
        ancestors = self.get_ancestors(self.memory_id, self.user_id)
        
        # Apply ancestor influences (higher level contexts override lower level ones)
        for ancestor in reversed(ancestors):  # Start from root
            if ancestor.influence_rules:
                context = self.apply_influence_rules(context, ancestor.influence_rules)
        
        return context

    def apply_influence_rules(self, context: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply influence rules to modify context"""
        modified_context = context.copy()
        
        for rule_type, rule_data in rules.items():
            if rule_type == 'override':
                # Direct override of values
                for key, value in rule_data.items():
                    modified_context[key] = value
            elif rule_type == 'modify':
                # Modify existing values
                for key, modification in rule_data.items():
                    if key in modified_context:
                        if isinstance(modification, dict) and 'operation' in modification:
                            op = modification['operation']
                            value = modification.get('value')
                            
                            if op == 'multiply':
                                modified_context[key] *= value
                            elif op == 'add':
                                modified_context[key] += value
                            elif op == 'set':
                                modified_context[key] = value
                        else:
                            modified_context[key] = modification
            elif rule_type == 'add':
                # Add new values if they don't exist
                for key, value in rule_data.items():
                    if key not in modified_context:
                        modified_context[key] = value
        
        return modified_context

    def update_access_time(self):
        """Update the last accessed time"""
        self.last_accessed = datetime.utcnow()
        db.session.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'id': self.memory_id,
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'path': self.path,
            'context_data': self.context_data,
            'influence_rules': self.influence_rules,
            'type': self.memory_type,
            'is_active': self.is_active,
            'priority': self.priority,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }


class MemoryEmbedding(db.Model):
    """Embeddings for semantic search"""
    __tablename__ = 'memory_embeddings'

    id = db.Column(db.Integer, primary_key=True)
    memory_id = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Embedding data
    embedding_vector = db.Column(db.Text, nullable=False)  # JSON-encoded list of floats
    model_name = db.Column(db.String(100), nullable=False)  # e.g., "text-embedding-3-small"
    
    # Metadata
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    user = db.relationship('User', backref='memory_embeddings')

    def __repr__(self):
        return f"<MemoryEmbedding memory_id={self.memory_id} model={self.model_name}>" 