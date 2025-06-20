from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from ..db import db


class OAuthCredentials(db.Model):
    __tablename__ = "oauth_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(50), db.ForeignKey("users.id"), nullable=False
    )  # Link to users table
    service = db.Column(db.String(50), nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)  # Some services might not provide refresh tokens
    expires_at = db.Column(db.DateTime, nullable=True)  # When the access token expires
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    scopes = db.Column(db.Text, nullable=True)

    # Relationship with User model
    user = db.relationship(
        "User", backref=db.backref("oauth_credentials", lazy=True)
    )

    def __repr__(self):
        return f"<OAuthCredentials {self.service} for user {self.user_id}>"

    @classmethod
    def get_credentials(cls, user_id, service):
        """Get OAuth credentials for a user and service"""
        return cls.query.filter_by(user_id=user_id, service=service).first()

    @classmethod
    def store_credentials(cls, user_id, service, access_token, refresh_token=None, expires_at=None, scopes=None):
        """Store or update OAuth credentials"""
        creds = cls.get_credentials(user_id, service)
        scopes_str = " ".join(scopes) if scopes else ""
        if creds:
            creds.access_token = access_token
            if refresh_token:
                creds.refresh_token = refresh_token
            if expires_at:
                creds.expires_at = expires_at
            if scopes is not None:
                creds.scopes = scopes_str
            creds.updated_at = datetime.utcnow()
        else:
            creds = cls(
                user_id=user_id,
                service=service,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                scopes=scopes_str,
            )
            db.session.add(creds)
        db.session.commit()
        return creds

    @classmethod
    def remove_credentials(cls, user_id, service):
        """Remove OAuth credentials"""
        print(
            f"[DEBUG] Attempting to remove credentials for user_id={user_id}, service={service}"
        )
        creds = cls.get_credentials(user_id, service)
        print(f"[DEBUG] Found creds: {creds}")
        if creds:
            db.session.delete(creds)
            try:
                db.session.commit()
                print("[DEBUG] Commit successful")
            except Exception as e:
                print(f"[DEBUG] Commit failed: {e}")
            return True
        print("[DEBUG] No credentials found to delete.")
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "service": self.service,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "scopes": self.scopes.split(" ") if self.scopes else [],
        }
