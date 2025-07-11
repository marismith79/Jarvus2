from ..db import db
from datetime import datetime

class ToolDiscoveryCache(db.Model):
    __tablename__ = 'tool_discovery_cache'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    app_slug = db.Column(db.String, nullable=False)
    tools_json = db.Column(db.Text, nullable=False)  # Store as JSON string
    discovered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sdk_tools_blob = db.Column(db.LargeBinary, nullable=True)  # Store pickled SDK tool definitions

    __table_args__ = (db.UniqueConstraint('user_id', 'app_slug', name='_user_app_uc'),) 