from flask_login import UserMixin

from ..db import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    # The __init__ is now handled by SQLAlchemy.
    # We will create User instances by passing keyword arguments, e.g., User(id=..., name=...)

    # Add this line
    histories = db.relationship('History', back_populates='user', lazy=True, cascade="all, delete-orphan")
    todos = db.relationship('Todo', back_populates='user', lazy=True, cascade="all, delete-orphan")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
