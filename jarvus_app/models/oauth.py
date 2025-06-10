from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from ..db import db

class OAuthCredentials(db.Model):
    __tablename__ = 'google_oauth_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)  # Link to users table
    service = db.Column(db.String(50), nullable=False)
    credentials_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('oauth_credentials', lazy=True))
    
    def __repr__(self):
        return f'<OAuthCredentials {self.service} for user {self.user_id}>'
    
    @classmethod
    def get_credentials(cls, user_id, service):
        """Get OAuth credentials for a user and service"""
        return cls.query.filter_by(user_id=user_id, service=service).first()
    
    @classmethod
    def store_credentials(cls, user_id, service, credentials_json):
        """Store or update OAuth credentials"""
        creds = cls.get_credentials(user_id, service)
        if creds:
            creds.credentials_json = credentials_json
            creds.updated_at = datetime.utcnow()
        else:
            creds = cls(
                user_id=user_id,
                service=service,
                credentials_json=credentials_json
            )
            db.session.add(creds)
        db.session.commit()
        return creds
    
    @classmethod
    def remove_credentials(cls, user_id, service):
        """Remove OAuth credentials"""
        creds = cls.get_credentials(user_id, service)
        if creds:
            db.session.delete(creds)
            db.session.commit()
            return True
        return False 