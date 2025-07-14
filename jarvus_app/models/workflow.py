from datetime import datetime
from jarvus_app.db import db
from typing import Dict, Any, Optional

class Workflow(db.Model):
    """Workflow model for storing AI-executable workflow definitions"""
    __tablename__ = 'workflows'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Workflow definition in the specified format
    goal = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Tool and trigger configuration
    required_tools = db.Column(db.JSON, nullable=True)  # List of required tool names
    trigger_type = db.Column(db.String(50), nullable=True)  # 'manual', 'scheduled', 'event'
    trigger_config = db.Column(db.JSON, nullable=True)  # Trigger-specific configuration
    
    # Link to procedural memory (long_term_memory)
    procedural_memory_id = db.Column(db.Integer, db.ForeignKey('long_term_memory.id'), nullable=True)

    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='workflows')

    def __repr__(self):
        return f"<Workflow {self.name} (id={self.id})>"

    def to_dict(self):
        """Convert workflow to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'goal': self.goal,
            'instructions': self.instructions,
            'notes': self.notes,
            'required_tools': self.required_tools or [],
            'trigger_type': self.trigger_type or 'manual',
            'trigger_config': self.trigger_config or {},
            'procedural_memory_id': self.procedural_memory_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_user_workflows(cls, user_id: str) -> list['Workflow']:
        """Get all workflows for a user, ordered by creation date"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_workflow_by_id(cls, workflow_id: int, user_id: str) -> Optional['Workflow']:
        """Get a specific workflow by ID for a user"""
        return cls.query.filter_by(id=workflow_id, user_id=user_id).first()

    @classmethod
    def create_workflow(cls, user_id: str, name: str, goal: str, instructions: str, 
                       description: str = None, notes: str = None, 
                       required_tools: list = None, trigger_type: str = 'manual', 
                       trigger_config: dict = None, procedural_memory_id: int = None) -> 'Workflow':
        """Create a new workflow"""
        workflow = cls(
            user_id=user_id,
            name=name,
            description=description,
            goal=goal,
            instructions=instructions,
            notes=notes,
            required_tools=required_tools or [],
            trigger_type=trigger_type,
            trigger_config=trigger_config or {},
            procedural_memory_id=procedural_memory_id
        )
        db.session.add(workflow)
        db.session.commit()
        return workflow

    def update_workflow(self, name: str = None, goal: str = None, instructions: str = None,
                       description: str = None, notes: str = None, is_active: bool = None,
                       required_tools: list = None, trigger_type: str = None, trigger_config: dict = None, procedural_memory_id: int = None):
        """Update workflow fields"""
        if name is not None:
            self.name = name
        if goal is not None:
            self.goal = goal
        if instructions is not None:
            self.instructions = instructions
        if description is not None:
            self.description = description
        if notes is not None:
            self.notes = notes
        if is_active is not None:
            self.is_active = is_active
        if required_tools is not None:
            self.required_tools = required_tools
        if trigger_type is not None:
            self.trigger_type = trigger_type
        if trigger_config is not None:
            self.trigger_config = trigger_config
        if procedural_memory_id is not None:
            self.procedural_memory_id = procedural_memory_id
        
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete_workflow(self):
        """Delete the workflow"""
        db.session.delete(self)
        db.session.commit() 