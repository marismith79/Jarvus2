"""
Database model for the user_tools table.
This table associates users with their available tools.
"""

from jarvus_app.db import db


class UserTool(db.Model):
    __tablename__ = "user_tools"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(50), db.ForeignKey("users.id"), nullable=False
    )
    tool_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to the User model
    user = db.relationship("User", backref=db.backref("tools", lazy=True))

    def __repr__(self):
        return f"<UserTool {self.tool_name} for User {self.user_id}>"
