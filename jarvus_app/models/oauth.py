from datetime import datetime
from ..db import db


class OAuthCredentials(db.Model):
    __tablename__ = "oauth_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(50), db.ForeignKey("users.id"), nullable=False
    )  # Link to users table
    service = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer, nullable=True)  # 1 for connected, NULL for not connected
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
    def store_credentials(cls, user_id, service, state=None):
        """Store or update OAuth credentials with status=1 (connected)"""
        creds = cls.get_credentials(user_id, service)
        if creds:
            creds.status = 1  # Set as connected
            if state:
                creds.state = state
            creds.updated_at = datetime.utcnow()
        else:
            creds = cls(
                user_id=user_id,
                service=service,
                status=1,  # Set as connected
                state=state,
            )
            db.session.add(creds)
        db.session.commit()
        return creds

    @classmethod
    def is_connected(cls, user_id, service):
        """Check if user is connected to a service"""
        creds = cls.get_credentials(user_id, service)
        return creds is not None and creds.status == 1

    @classmethod
    def remove_credentials(cls, user_id: int, service: str) -> bool:
        """Remove OAuth credentials for a user and service"""
        try:
            # print(
            #     f"Removing OAuth credentials for user {user_id}, service {service}"
            # )

            creds = cls.query.filter_by(user_id=user_id, service=service).first()
            if creds:
                # print(f"[DEBUG] Found creds: {creds}")
                db.session.delete(creds)
                try:
                    db.session.commit()
                    # print("[DEBUG] Commit successful")
                    return True
                except Exception as e:
                    # print(f"[DEBUG] Commit failed: {e}")
                    db.session.rollback()
                    return False
            else:
                # print("[DEBUG] No credentials found to delete.")
                return False
        except Exception as e:
            db.session.rollback()
            return False

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "service": self.service,
            "status": self.status,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
