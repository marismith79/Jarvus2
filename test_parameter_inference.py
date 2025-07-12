#!/usr/bin/env python3
"""
Test script for parameter inference system.
Demonstrates how the system reduces clarification questions by using semantic memory.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvus_app import create_app
from jarvus_app.db import db
from jarvus_app.models.user import User
from jarvus_app.services.onboarding_service import onboarding_service
from jarvus_app.services.parameter_inference_service import parameter_inference_service
from jarvus_app.services.orchestrating_agent import orchestrating_agent

def test_parameter_inference():
    """Test the parameter inference system."""
    
    # Set up Flask app context
    app = create_app()
    with app.app_context():
        print("🧪 Testing Parameter Inference System")
        print("=" * 50)
        
        # Create a test user
        test_user = User(
            id="test_user_123",
            name="Test User",
            email="test@example.com"
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user")
        except Exception as e:
            print(f"⚠️  User might already exist: {e}")
            db.session.rollback()
        
        user_id = test_user.id
        
        # Step 1: Initialize user preferences during onboarding
        print("\n📋 Step 1: Initializing User Preferences")
        print("-" * 40)
        
        custom_preferences = {
            "timezone_preference": "America/Los_Angeles",
            "meeting_duration_preference": "90",
            "email_signature": "Best regards,\nTest User\nSoftware Engineer",
            "reminder_preference": "30"
        }
        
        stored_memories = onboarding_service.initialize_user_preferences(
            user_id=user_id,
            custom_preferences=custom_preferences
        )
        
        print(f"✅ Stored {len(stored_memories)} user preferences")
        
        # Step 2: Test parameter inference
        print("\n🔍 Step 2: Testing Parameter Inference")
        print("-" * 40)
        
        # Test case 1: Calendar event with missing parameters
        print("\n📅 Test Case 1: Calendar Event Creation")
        user_message = "Schedule a meeting with the team"
        tool_name = "create_calendar_event"
        provided_params = {
            "summary": "Team Meeting"
        }
        
        print(f"User message: {user_message}")
        print(f"Tool: {tool_name}")
        print(f"Provided params: {provided_params}")
        
        inferred_params = parameter_inference_service.infer_missing_parameters(
            user_id=user_id,
            tool_name=tool_name,
            provided_params=provided_params,
            user_message=user_message
        )
        
        print(f"✅ Inferred params: {inferred_params}")
        
        # Test case 2: Email with missing parameters
        print("\n📧 Test Case 2: Email Creation")
        user_message = "Send an email to john@example.com about the project update"
        tool_name = "send_email"
        provided_params = {
            "to": "john@example.com",
            "subject": "Project Update"
        }
        
        print(f"User message: {user_message}")
        print(f"Tool: {tool_name}")
        print(f"Provided params: {provided_params}")
        
        inferred_params = parameter_inference_service.infer_missing_parameters(
            user_id=user_id,
            tool_name=tool_name,
            provided_params=provided_params,
            user_message=user_message
        )
        
        print(f"✅ Inferred params: {inferred_params}")
        
        # Step 3: Test orchestrating agent decision making
        print("\n🎯 Step 3: Testing Orchestrating Agent")
        print("-" * 40)
        
        # Test case 3: Critical missing parameters
        print("\n⚠️  Test Case 3: Critical Missing Parameters")
        user_message = "Create a calendar event"
        tool_name = "create_calendar_event"
        missing_params = ["summary", "start_time", "end_time"]
        
        should_ask, params_to_ask_for, inferred_params = orchestrating_agent.should_ask_for_clarification(
            user_id=user_id,
            tool_name=tool_name,
            missing_params=missing_params,
            user_message=user_message
        )
        
        print(f"User message: {user_message}")
        print(f"Missing params: {missing_params}")
        print(f"Should ask for clarification: {should_ask}")
        print(f"Params to ask for: {params_to_ask_for}")
        print(f"Inferred params: {inferred_params}")
        
        if should_ask:
            clarification_question = orchestrating_agent.generate_clarification_question(
                tool_name=tool_name,
                params_to_ask_for=params_to_ask_for,
                user_message=user_message
            )
            print(f"🤔 Clarification question: {clarification_question}")
        
        # Test case 4: Optional missing parameters
        print("\n✅ Test Case 4: Optional Missing Parameters")
        user_message = "Schedule a 2-hour meeting with the team tomorrow at 2pm"
        tool_name = "create_calendar_event"
        missing_params = ["timezone", "reminder"]
        
        should_ask, params_to_ask_for, inferred_params = orchestrating_agent.should_ask_for_clarification(
            user_id=user_id,
            tool_name=tool_name,
            missing_params=missing_params,
            user_message=user_message
        )
        
        print(f"User message: {user_message}")
        print(f"Missing params: {missing_params}")
        print(f"Should ask for clarification: {should_ask}")
        print(f"Params to ask for: {params_to_ask_for}")
        print(f"Inferred params: {inferred_params}")
        
        # Step 4: Show user preferences
        print("\n👤 Step 4: Current User Preferences")
        print("-" * 40)
        
        preferences = onboarding_service.get_user_preferences(user_id)
        for key, value in preferences.items():
            print(f"  {key}: {value}")
        
        print("\n🎉 Parameter Inference System Test Complete!")
        print("=" * 50)
        
        # Cleanup
        try:
            db.session.delete(test_user)
            db.session.commit()
            print("🧹 Cleaned up test user")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

if __name__ == "__main__":
    test_parameter_inference() 