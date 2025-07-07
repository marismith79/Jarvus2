from datetime import datetime
from ..db import db


class OAuthCredentials(db.Model):
    __tablename__ = "oauth_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(50), db.ForeignKey("users.id"), nullable=False
    )  # Link to users table
    service = db.Column(db.String(50), nullable=False)
    connect_id = db.Column(db.String(255), nullable=True)  
    state = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

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
    def store_credentials(cls, user_id, service, connect_id, state=None):
        """Store or update Pipedream credentials (connect_id)"""
        creds = cls.get_credentials(user_id, service)
        if creds:
            creds.connect_id = connect_id
            if state:
                creds.state = state
            creds.updated_at = datetime.utcnow()
        else:
            creds = cls(
                user_id=user_id,
                service=service,
                connect_id=connect_id,
                state=state,
            )
            db.session.add(creds)
        db.session.commit()
        return creds

    @classmethod
    def get_connect_id(cls, user_id, service):
        """Get connect_id for a user and service (Pipedream authentication)"""
        creds = cls.get_credentials(user_id, service)
        return creds.connect_id if creds else None

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
            "connect_id": self.connect_id,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
