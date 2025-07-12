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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_todos(cls, user_id):
        """Get all todos for a user, ordered by creation date."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
    
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
    
    def update_todo(self, text=None, completed=None):
        """Update todo text and/or completion status."""
        if text is not None:
            self.text = text
        if completed is not None:
            self.completed = completed
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def delete_todo(self):
        """Delete the todo."""
        db.session.delete(self)
        db.session.commit() 