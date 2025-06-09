from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models.oauth import OAuthCredentials

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    # Check which services are connected
    gmail_connected = OAuthCredentials.get_credentials(current_user.id, 'gmail') is not None
    notion_connected = OAuthCredentials.get_credentials(current_user.id, 'notion') is not None
    slack_connected = OAuthCredentials.get_credentials(current_user.id, 'slack') is not None
    zoom_connected = OAuthCredentials.get_credentials(current_user.id, 'zoom') is not None
    
    return render_template('profile.html',
        user=current_user,
        gmail_connected=gmail_connected,
        notion_connected=notion_connected,
        slack_connected=slack_connected,
        zoom_connected=zoom_connected) 