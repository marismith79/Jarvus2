from datetime import datetime
from jarvus_app.db import db

class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), index=True, nullable=False)
    messages = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<History session_id={self.session_id} id={self.id}>" 