"""
Onboarding Service
Handles user onboarding and populates semantic memory with common parameter preferences.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from ..db import db
from .memory_service import memory_service

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for handling user onboarding and parameter preference initialization"""
    
    def __init__(self):
        # Common parameter preferences to populate during onboarding
        self.default_preferences = {
            # Calendar preferences
            "meeting_duration_preference": "60",
            "timezone_preference": "America/New_York",  # Could be detected from user location
            "reminder_preference": "15",
            "calendar_visibility": "available",
            "meeting_acceptance": "accept_relevant",
            
            # Email preferences
            "email_signature": "Best regards,\n[User Name]",
            "email_priority_preference": "normal",
            "email_check_frequency": "every_30_minutes",
            "auto_reply_enabled": False,
            
            # Document preferences
            "document_naming_pattern": "descriptive_with_date",
            "document_folder_preference": "Documents",
            "document_template_preference": "blank",
            
            # Search preferences
            "search_results_preference": "10",
            "search_engine_preference": "google",
            
            # General preferences
            "notification_preference": "important_only",
            "language_preference": "en",
            "date_format_preference": "MM/DD/YYYY",
            "time_format_preference": "12_hour"
        }
    
    def initialize_user_preferences(self, user_id: int, custom_preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Initialize a user's semantic memory with common parameter preferences.
        
        Args:
            user_id: User ID
            custom_preferences: Optional custom preferences to override defaults
            
        Returns:
            List of stored memory objects
        """
        try:
            stored_memories = []
            
            # Merge default preferences with custom preferences
            preferences = self.default_preferences.copy()
            if custom_preferences:
                preferences.update(custom_preferences)
            
            # Store each preference as semantic memory
            for preference_key, preference_value in preferences.items():
                memory_data = {
                    "preference_type": preference_key,
                    "value": preference_value,
                    "source": "onboarding",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                memory = memory_service.store_semantic_memory(
                    user_id=user_id,
                    fact_type="user_preference",
                    fact_data=memory_data,
                    importance_score=3.0  # High importance for user preferences
                )
                
                stored_memories.append(memory)
                logger.info(f"Stored preference {preference_key}={preference_value} for user {user_id}")
            
            logger.info(f"Initialized {len(stored_memories)} preferences for user {user_id}")
            return stored_memories
            
        except Exception as e:
            logger.error(f"Error initializing user preferences: {str(e)}")
            return []
    
    def update_user_preference(self, user_id: int, preference_key: str, value: Any) -> bool:
        """
        Update a specific user preference.
        
        Args:
            user_id: User ID
            preference_key: Preference key to update
            value: New value for the preference
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory_data = {
                "preference_type": preference_key,
                "value": value,
                "source": "user_update",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            memory_service.store_semantic_memory(
                user_id=user_id,
                fact_type="user_preference",
                fact_data=memory_data,
                importance_score=3.0
            )
            
            logger.info(f"Updated preference {preference_key}={value} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preference: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get all user preferences from semantic memory.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user preferences
        """
        try:
            memories = memory_service.search_memories(
                user_id=user_id,
                namespace='semantic',
                query='user_preference',
                limit=50
            )
            
            preferences = {}
            for memory in memories:
                memory_data = memory.memory_data.get('data', {})
                preference_key = memory_data.get('preference_type')
                if preference_key:
                    preferences[preference_key] = memory_data.get('value')
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}
    
    def detect_user_preferences_from_conversation(self, user_id: int, conversation_text: str) -> List[Dict[str, Any]]:
        """
        Detect user preferences from conversation text and store them.
        
        Args:
            user_id: User ID
            conversation_text: Text of the conversation to analyze
            
        Returns:
            List of detected and stored preferences
        """
        try:
            # This could be enhanced with LLM analysis
            # For now, use simple pattern matching
            detected_preferences = []
            
            # Simple pattern matching examples
            patterns = {
                "timezone_preference": [
                    r"timezone.*?(\w+/\w+)",
                    r"(\w+/\w+).*?timezone",
                    r"in (\w+/\w+) time"
                ],
                "meeting_duration_preference": [
                    r"(\d+).*?minute.*?meeting",
                    r"meeting.*?(\d+).*?minute"
                ],
                "email_signature": [
                    r"signature.*?([^\n]+)",
                    r"([^\n]+).*?signature"
                ]
            }
            
            import re
            for preference_key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, conversation_text, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        if self.update_user_preference(user_id, preference_key, value):
                            detected_preferences.append({
                                "preference_key": preference_key,
                                "value": value,
                                "source": "conversation_detection"
                            })
                        break
            
            return detected_preferences
            
        except Exception as e:
            logger.error(f"Error detecting preferences from conversation: {str(e)}")
            return []


# Global onboarding service instance
onboarding_service = OnboardingService() 