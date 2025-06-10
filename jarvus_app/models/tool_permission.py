"""
Database model for storing detailed tool permissions for each user.
This includes specific permissions like read/write access for different tool features.
"""

from jarvus_app.db import db
from datetime import datetime

class ToolPermission(db.Model):
    __tablename__ = 'tool_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    tool_name = db.Column(db.String(50), nullable=False)
    permission_type = db.Column(db.String(50), nullable=False)  # e.g., 'read', 'write', 'admin'
    feature = db.Column(db.String(100), nullable=False)  # e.g., 'emails', 'calendar', 'contacts'
    is_granted = db.Column(db.Boolean, default=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship to the User model
    user = db.relationship('User', backref=db.backref('tool_permissions', lazy=True))

    def __repr__(self):
        return f'<ToolPermission {self.tool_name}.{self.feature}.{self.permission_type} for User {self.user_id}>'

    @classmethod
    def grant_permission(cls, user_id, tool_name, permission_type, feature, expires_at=None):
        """Grant a specific permission to a user."""
        permission = cls.query.filter_by(
            user_id=user_id,
            tool_name=tool_name,
            permission_type=permission_type,
            feature=feature
        ).first()

        if permission:
            permission.is_granted = True
            permission.granted_at = datetime.utcnow()
            permission.expires_at = expires_at
        else:
            permission = cls(
                user_id=user_id,
                tool_name=tool_name,
                permission_type=permission_type,
                feature=feature,
                is_granted=True,
                expires_at=expires_at
            )
            db.session.add(permission)

        db.session.commit()
        return permission

    @classmethod
    def revoke_permission(cls, user_id, tool_name, permission_type, feature):
        """Revoke a specific permission from a user."""
        permission = cls.query.filter_by(
            user_id=user_id,
            tool_name=tool_name,
            permission_type=permission_type,
            feature=feature
        ).first()

        if permission:
            permission.is_granted = False
            db.session.commit()
            return True
        return False

    @classmethod
    def has_permission(cls, user_id, tool_name, permission_type, feature):
        """Check if a user has a specific permission."""
        permission = cls.query.filter_by(
            user_id=user_id,
            tool_name=tool_name,
            permission_type=permission_type,
            feature=feature,
            is_granted=True
        ).first()

        if not permission:
            return False

        # Check if permission has expired
        if permission.expires_at and permission.expires_at < datetime.utcnow():
            permission.is_granted = False
            db.session.commit()
            return False

        return True

    @classmethod
    def get_user_permissions(cls, user_id, tool_name=None):
        """Get all permissions for a user, optionally filtered by tool."""
        query = cls.query.filter_by(user_id=user_id, is_granted=True)
        if tool_name:
            query = query.filter_by(tool_name=tool_name)
        return query.all() 