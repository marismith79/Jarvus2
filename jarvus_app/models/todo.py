"""
Todo model for storing user todo items.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..db import db


class Todo(db.Model):
    """Todo model for storing user todo items."""
    
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    current_task = Column(Boolean, default=False, nullable=False)  # New field for current task
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="todos")
    
    def __repr__(self):
        return f'<Todo {self.id}: {self.text[:50]}...>'
    
    def to_dict(self):
        """Convert todo to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'current_task': self.current_task,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_todos(cls, user_id):
        """Get all todos for a user, ordered by creation date."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_current_task(cls, user_id):
        """Get the current active task for a user."""
        return cls.query.filter_by(user_id=user_id, current_task=True, completed=False).first()
    
    @classmethod
    def create_todo(cls, user_id, text, completed=False):
        """Create a new todo for a user."""
        todo = cls(
            user_id=user_id,
            text=text,
            completed=completed
        )
        db.session.add(todo)
        db.session.commit()
        return todo
    
    def update_todo(self, text=None, completed=None, current_task=None):
        """Update todo text, completion status, and/or current task status."""
        if text is not None:
            self.text = text
        if completed is not None:
            self.completed = completed
        if current_task is not None:
            # If setting this as current task, unset all other current tasks for this user
            if current_task:
                Todo.query.filter_by(user_id=self.user_id, current_task=True).update({'current_task': False})
            self.current_task = current_task
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def delete_todo(self):
        """Delete the todo."""
        db.session.delete(self)
        db.session.commit() 