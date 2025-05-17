from datetime import datetime
import json
import os
from pathlib import Path

class EmailSignup:
    """Simple model to store email signups in a JSON file"""
    
    STORAGE_DIR = Path(__file__).parent.parent / "data"
    STORAGE_FILE = STORAGE_DIR / "email_signups.json"
    
    def __init__(self, email, timestamp=None):
        self.email = email
        self.timestamp = timestamp or datetime.now().isoformat()
    
    @classmethod
    def initialize_storage(cls):
        """Ensure the storage directory and file exist"""
        if not cls.STORAGE_DIR.exists():
            os.makedirs(cls.STORAGE_DIR)
        
        if not cls.STORAGE_FILE.exists():
            with open(cls.STORAGE_FILE, 'w') as f:
                json.dump([], f)
    
    @classmethod
    def save_email(cls, email):
        """Save an email to the storage file"""
        cls.initialize_storage()
        
        # Load existing emails
        emails = cls.get_all_emails()
        
        # Check if email already exists
        if any(entry.get('email') == email for entry in emails):
            return False
        
        # Add new email
        signup = EmailSignup(email)
        emails.append({
            'email': signup.email,
            'timestamp': signup.timestamp
        })
        
        # Save back to file
        with open(cls.STORAGE_FILE, 'w') as f:
            json.dump(emails, f, indent=2)
        
        return True
    
    @classmethod
    def get_all_emails(cls):
        """Get all saved emails"""
        cls.initialize_storage()
        
        try:
            with open(cls.STORAGE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return [] 