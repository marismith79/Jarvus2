from datetime import datetime
from jarvus_app.db import db

class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tools = db.Column(db.JSON, nullable=True)
    messages = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user
    user = db.relationship('User', back_populates='histories')

    def __repr__(self):
        return f"<History session_id={self.name} id={self.id}>"

class InteractionHistory(db.Model):
    __tablename__ = 'interaction_history'

    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('history.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    assistant_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    history = db.relationship('History', backref='interactions')
    user = db.relationship('User', backref='interaction_histories')

    def __repr__(self):
        return f"<InteractionHistory id={self.id} history_id={self.history_id}>" 