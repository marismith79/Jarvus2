#!/usr/bin/env python3
"""
Test script demonstrating hierarchical memory system with vacation context example.
Shows how high-level contextual states influence all lower-level agent decisions.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
USER_EMAIL = "test@example.com"
USER_PASSWORD = "password123"

class HierarchicalMemoryDemo:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.vacation_context_id = None
        
    def login(self):
        """Login to get session"""
        login_data = {
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def create_vacation_context(self):
        """Create the main vacation context that influences everything"""
        print("\n🏖️  Creating Vacation Context...")
        
        vacation_data = {
            "name": "Vacation Mode",
            "description": "User is on vacation - should prioritize relaxation and minimize work",
            "context_data": {
                "status": "on_vacation",
                "start_date": "2024-06-01",
                "end_date": "2024-06-15",
                "location": "Hawaii",
                "work_priority": "minimal",
                "relaxation_level": "high"
            },
            "influence_rules": {
                "override": {
                    "work_urgency": "low",
                    "response_style": "relaxed",
                    "automation_level": "high",
                    "interruption_threshold": "critical_only"
                },
                "modify": {
                    "email_check_frequency": {"operation": "multiply", "value": 0.25},
                    "meeting_suggestions": {"operation": "multiply", "value": 0.1},
                    "task_priority": {"operation": "multiply", "value": 0.3},
                    "response_time_expectation": {"operation": "multiply", "value": 4.0}
                },
                "add": {
                    "vacation_aware": True,
                    "relaxation_focus": True,
                    "work_deferral_enabled": True
                }
            },
            "memory_type": "context",
            "priority": 100  # High priority to override other contexts
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/context", json=vacation_data)
        if response.status_code == 201:
            result = response.json()
            self.vacation_context_id = result['context']['id']
            print(f"✅ Vacation context created: {result['context']['name']}")
            print(f"   Context ID: {self.vacation_context_id}")
            return True
        else:
            print(f"❌ Failed to create vacation context: {response.text}")
            return False
    
    def create_email_preferences_context(self):
        """Create email preferences that inherit from vacation context"""
        print("\n📧 Creating Email Preferences Context...")
        
        email_data = {
            "name": "Vacation Email Preferences",
            "description": "Email handling preferences during vacation",
            "context_data": {
                "check_frequency": "once_per_day",
                "auto_reply_enabled": True,
                "urgent_only": True,
                "batch_processing": True,
                "notification_sound": "off"
            },
            "parent_id": self.vacation_context_id,
            "influence_rules": {
                "override": {
                    "email_urgency_threshold": "critical_only",
                    "response_time_expectation": "24_hours",
                    "email_notifications": "disabled"
                },
                "add": {
                    "vacation_auto_reply": True,
                    "email_filtering": "urgent_only"
                }
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/context", json=email_data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Email preferences created: {result['context']['name']}")
            return result['context']['id']
        else:
            print(f"❌ Failed to create email preferences: {response.text}")
            return None
    
    def create_meeting_preferences_context(self):
        """Create meeting preferences that inherit from vacation context"""
        print("\n📅 Creating Meeting Preferences Context...")
        
        meeting_data = {
            "name": "Vacation Meeting Preferences",
            "description": "Meeting handling preferences during vacation",
            "context_data": {
                "meeting_acceptance": "decline_all",
                "calendar_visibility": "busy",
                "out_of_office": True,
                "delegate_meetings": True
            },
            "parent_id": self.vacation_context_id,
            "influence_rules": {
                "override": {
                    "meeting_suggestions": "none",
                    "calendar_availability": "unavailable",
                    "meeting_reminders": "disabled"
                },
                "add": {
                    "vacation_delegation": True,
                    "meeting_decline_message": "On vacation until June 15th"
                }
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/context", json=meeting_data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Meeting preferences created: {result['context']['name']}")
            return result['context']['id']
        else:
            print(f"❌ Failed to create meeting preferences: {response.text}")
            return None
    
    def store_user_preferences(self):
        """Store some base user preferences that will be influenced by vacation context"""
        print("\n💾 Storing Base User Preferences...")
        
        # Store base email preferences
        email_prefs = {
            "type": "email_preferences",
            "data": {
                "check_frequency": "every_30_minutes",
                "auto_reply_enabled": False,
                "urgent_only": False,
                "batch_processing": False,
                "notification_sound": "on",
                "response_time_expectation": "2_hours"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/semantic", json=email_prefs)
        if response.status_code == 201:
            print("✅ Base email preferences stored")
        
        # Store base meeting preferences
        meeting_prefs = {
            "type": "meeting_preferences",
            "data": {
                "meeting_acceptance": "accept_relevant",
                "calendar_visibility": "available",
                "out_of_office": False,
                "delegate_meetings": False,
                "meeting_suggestions": "frequent",
                "calendar_availability": "available"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/semantic", json=meeting_prefs)
        if response.status_code == 201:
            print("✅ Base meeting preferences stored")
    
    def demonstrate_context_influence(self):
        """Demonstrate how vacation context influences decisions"""
        print("\n🎯 Demonstrating Context Influence...")
        
        # Test 1: Get decision context for email handling
        print("\n1️⃣  Email Handling Decision:")
        email_decision = {
            "decision_type": "email_handling"
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/decision-context", json=email_decision)
        if response.status_code == 200:
            context = response.json()['context']
            print("   Combined Context:")
            for key, value in context.items():
                print(f"   - {key}: {value}")
        
        # Test 2: Get contextualized email preferences
        print("\n2️⃣  Contextualized Email Preferences:")
        response = self.session.get(
            f"{BASE_URL}/api/memory/hierarchical/contextualized/semantic",
            params={"query": "email", "context_id": self.vacation_context_id}
        )
        if response.status_code == 200:
            result = response.json()
            print("   Context Influence:")
            for key, value in result['context_influence'].items():
                print(f"   - {key}: {value}")
        
        # Test 3: Get specific context influence
        print("\n3️⃣  Vacation Context Influence:")
        response = self.session.get(f"{BASE_URL}/api/memory/hierarchical/context/{self.vacation_context_id}")
        if response.status_code == 200:
            influence = response.json()['influence']
            print("   Vacation Influence:")
            for key, value in influence.items():
                print(f"   - {key}: {value}")
    
    def simulate_agent_decisions(self):
        """Simulate how an agent would make decisions with vacation context"""
        print("\n🤖 Simulating Agent Decisions with Vacation Context...")
        
        # Decision 1: Should I check email now?
        print("\n📧 Decision: Should I check email now?")
        decision_context = self.session.post(
            f"{BASE_URL}/api/memory/hierarchical/decision-context",
            json={"decision_type": "email_check"}
        ).json()['context']
        
        if decision_context.get('email_check_frequency', 1.0) < 0.5:
            print("   🏖️  VACATION MODE: Check email less frequently (once per day)")
        else:
            print("   📧 NORMAL MODE: Check email regularly")
        
        # Decision 2: Should I accept this meeting invitation?
        print("\n📅 Decision: Should I accept this meeting invitation?")
        decision_context = self.session.post(
            f"{BASE_URL}/api/memory/hierarchical/decision-context",
            json={"decision_type": "meeting_acceptance"}
        ).json()['context']
        
        if decision_context.get('meeting_suggestions', 1.0) < 0.5:
            print("   🏖️  VACATION MODE: Decline meeting - on vacation")
        else:
            print("   📅 NORMAL MODE: Consider accepting meeting")
        
        # Decision 3: How quickly should I respond to this message?
        print("\n⏰ Decision: How quickly should I respond to this message?")
        decision_context = self.session.post(
            f"{BASE_URL}/api/memory/hierarchical/decision-context",
            json={"decision_type": "response_timing"}
        ).json()['context']
        
        response_time = decision_context.get('response_time_expectation', 2.0)
        if response_time > 8.0:
            print(f"   🏖️  VACATION MODE: Relaxed response time ({response_time} hours)")
        else:
            print(f"   ⚡ NORMAL MODE: Quick response time ({response_time} hours)")
    
    def show_context_hierarchy(self):
        """Show the complete context hierarchy"""
        print("\n🌳 Context Hierarchy:")
        
        # Get root contexts
        response = self.session.get(f"{BASE_URL}/api/memory/hierarchical/root-contexts")
        if response.status_code == 200:
            root_contexts = response.json()['contexts']
            for context in root_contexts:
                print(f"   📍 {context['name']} (Level {context['level']})")
                print(f"      Path: {context['path']}")
                print(f"      Priority: {context['priority']}")
                
                # Get children
                children_response = self.session.get(f"{BASE_URL}/api/memory/hierarchical/context/{context['id']}/children")
                if children_response.status_code == 200:
                    children = children_response.json()['children']
                    for child in children:
                        print(f"      └── 📍 {child['name']} (Level {child['level']})")
                        print(f"          Path: {child['path']}")
    
    def run_demo(self):
        """Run the complete hierarchical memory demo"""
        print("🚀 Starting Hierarchical Memory Demo")
        print("=" * 50)
        
        # Step 1: Login
        if not self.login():
            return
        
        # Step 2: Create vacation context
        if not self.create_vacation_context():
            return
        
        # Step 3: Create child contexts
        email_context_id = self.create_email_preferences_context()
        meeting_context_id = self.create_meeting_preferences_context()
        
        # Step 4: Store base preferences
        self.store_user_preferences()
        
        # Step 5: Demonstrate influence
        self.demonstrate_context_influence()
        
        # Step 6: Simulate agent decisions
        self.simulate_agent_decisions()
        
        # Step 7: Show hierarchy
        self.show_context_hierarchy()
        
        print("\n" + "=" * 50)
        print("✅ Hierarchical Memory Demo Complete!")
        print("\nKey Takeaways:")
        print("• High-level contexts (vacation) influence all lower-level decisions")
        print("• Influence rules can override, modify, or add context data")
        print("• Child contexts inherit and can further modify parent influences")
        print("• The system automatically combines all relevant contexts for decisions")


if __name__ == "__main__":
    demo = HierarchicalMemoryDemo()
    demo.run_demo() 