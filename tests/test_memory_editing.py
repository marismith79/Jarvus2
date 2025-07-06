#!/usr/bin/env python3
"""
Test script for Memory Editing & Improvement System

This script demonstrates the comprehensive memory editing capabilities:
- Memory merging and consolidation
- Memory improvement and enhancement
- Memory quality assessment
- Memory conflict detection and resolution
- Memory evolution tracking
- Bulk operations and auto-consolidation
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
USER_EMAIL = "test@example.com"
USER_PASSWORD = "testpassword"

def pretty_print(title, data):
    """Pretty print JSON data"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2, default=str))

def login():
    """Login and get session"""
    session = requests.Session()
    
    # Login
    login_data = {
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def create_test_memories(session):
    """Create test memories for editing operations"""
    print("\n📝 Creating test memories...")
    
    # Create similar episodic memories for merging
    episodic_memories = []
    
    # Memory 1: Email checking
    memory1 = {
        "type": "chrome_action",
        "action": "click",
        "target": "button#check-email",
        "url": "https://gmail.com",
        "result": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "details": {"note": "Checked email in the morning"}
    }
    
    response = session.post(f"{BASE_URL}/api/memory/chrome-action", json=memory1)
    if response.status_code == 201:
        episodic_memories.append(response.json()['memory_id'])
        print("✅ Created episodic memory 1")
    
    # Memory 2: Similar email checking
    memory2 = {
        "type": "chrome_action",
        "action": "click",
        "target": "button#check-email",
        "url": "https://gmail.com",
        "result": "success",
        "timestamp": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        "details": {"note": "Checked email in the afternoon"}
    }
    
    response = session.post(f"{BASE_URL}/api/memory/chrome-action", json=memory2)
    if response.status_code == 201:
        episodic_memories.append(response.json()['memory_id'])
        print("✅ Created episodic memory 2")
    
    # Memory 3: Another similar action
    memory3 = {
        "type": "chrome_action",
        "action": "click",
        "target": "button#check-email",
        "url": "https://gmail.com",
        "result": "success",
        "timestamp": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
        "details": {"note": "Checked email in the evening"}
    }
    
    response = session.post(f"{BASE_URL}/api/memory/chrome-action", json=memory3)
    if response.status_code == 201:
        episodic_memories.append(response.json()['memory_id'])
        print("✅ Created episodic memory 3")
    
    # Create procedural memories for improvement
    procedural_memories = []
    
    # Procedure 1: Basic workflow
    procedure1 = {
        "name": "Start Zoom Meeting",
        "steps": [
            {"action": "open_url", "url": "https://zoom.us"},
            {"action": "click", "target": "Start Meeting"}
        ],
        "result": "success",
        "duration": 30,
        "success": True
    }
    
    response = session.post(f"{BASE_URL}/api/memory/workflow-execution", json=procedure1)
    if response.status_code == 201:
        procedural_memories.append(response.json()['memory_id'])
        print("✅ Created procedural memory 1")
    
    # Procedure 2: Similar workflow with different steps
    procedure2 = {
        "name": "Start Zoom Meeting",
        "steps": [
            {"action": "open_url", "url": "https://zoom.us"},
            {"action": "click", "target": "Sign In"},
            {"action": "click", "target": "Start Meeting"}
        ],
        "result": "success",
        "duration": 45,
        "success": True
    }
    
    response = session.post(f"{BASE_URL}/api/memory/workflow-execution", json=procedure2)
    if response.status_code == 201:
        procedural_memories.append(response.json()['memory_id'])
        print("✅ Created procedural memory 2")
    
    # Create semantic memories
    semantic_memories = []
    
    # Fact 1
    fact1 = {
        "text": "User prefers dark mode",
        "type": "preference",
        "importance": 1.5
    }
    
    response = session.post(f"{BASE_URL}/api/memory/store", json=fact1)
    if response.status_code == 201:
        semantic_memories.append(response.json()['memory_id'])
        print("✅ Created semantic memory 1")
    
    # Fact 2: Potentially conflicting
    fact2 = {
        "text": "User prefers light mode for reading",
        "type": "preference",
        "importance": 1.0
    }
    
    response = session.post(f"{BASE_URL}/api/memory/store", json=fact2)
    if response.status_code == 201:
        semantic_memories.append(response.json()['memory_id'])
        print("✅ Created semantic memory 2")
    
    return {
        'episodic': episodic_memories,
        'procedural': procedural_memories,
        'semantic': semantic_memories
    }

def test_memory_merging(session, test_memories):
    """Test memory merging capabilities"""
    print("\n🔄 Testing Memory Merging...")
    
    # 1. Find mergeable memories
    print("\n1. Finding mergeable memories...")
    response = session.get(f"{BASE_URL}/api/memory/find-mergeable?namespace=episodes&similarity=0.8")
    
    if response.status_code == 200:
        data = response.json()
        pretty_print("Mergeable Groups Found", data)
        
        if data['mergeable_groups']:
            # 2. Merge the first group
            group = data['mergeable_groups'][0]
            memory_ids = [memory['memory_id'] for memory in group['memories']]
            
            print(f"\n2. Merging {len(memory_ids)} memories...")
            merge_data = {
                "memory_ids": memory_ids,
                "merge_type": "episodic"
            }
            
            response = session.post(f"{BASE_URL}/api/memory/merge", json=merge_data)
            if response.status_code == 201:
                pretty_print("Merged Memory Result", response.json())
            else:
                print(f"❌ Merge failed: {response.text}")
        else:
            print("ℹ️ No mergeable groups found")
    else:
        print(f"❌ Failed to find mergeable memories: {response.text}")

def test_memory_improvement(session, test_memories):
    """Test memory improvement capabilities"""
    print("\n🔧 Testing Memory Improvement...")
    
    # 1. Improve a procedural memory
    if test_memories['procedural']:
        memory_id = test_memories['procedural'][0]
        print(f"\n1. Improving procedural memory {memory_id}...")
        
        improvement_data = {
            "improvement_type": "procedural"
        }
        
        response = session.post(f"{BASE_URL}/api/memory/improve/{memory_id}", json=improvement_data)
        if response.status_code == 200:
            pretty_print("Improved Procedural Memory", response.json())
        else:
            print(f"❌ Improvement failed: {response.text}")
    
    # 2. Improve a semantic memory
    if test_memories['semantic']:
        memory_id = test_memories['semantic'][0]
        print(f"\n2. Improving semantic memory {memory_id}...")
        
        improvement_data = {
            "improvement_type": "semantic"
        }
        
        response = session.post(f"{BASE_URL}/api/memory/improve/{memory_id}", json=improvement_data)
        if response.status_code == 200:
            pretty_print("Improved Semantic Memory", response.json())
        else:
            print(f"❌ Improvement failed: {response.text}")

def test_quality_assessment(session, test_memories):
    """Test memory quality assessment"""
    print("\n📊 Testing Memory Quality Assessment...")
    
    # 1. Assess individual memory quality
    if test_memories['episodic']:
        memory_id = test_memories['episodic'][0]
        print(f"\n1. Assessing quality of memory {memory_id}...")
        
        response = session.get(f"{BASE_URL}/api/memory/assess-quality/{memory_id}")
        if response.status_code == 200:
            pretty_print("Memory Quality Assessment", response.json())
        else:
            print(f"❌ Quality assessment failed: {response.text}")
    
    # 2. Get comprehensive quality report
    print("\n2. Generating comprehensive quality report...")
    response = session.get(f"{BASE_URL}/api/memory/quality-report?namespace=episodes&limit=20")
    
    if response.status_code == 200:
        pretty_print("Memory Quality Report", response.json())
    else:
        print(f"❌ Quality report failed: {response.text}")

def test_conflict_detection(session):
    """Test memory conflict detection and resolution"""
    print("\n⚠️ Testing Memory Conflict Detection...")
    
    # 1. Detect conflicts
    print("\n1. Detecting memory conflicts...")
    response = session.get(f"{BASE_URL}/api/memory/detect-conflicts?namespace=episodes")
    
    if response.status_code == 200:
        data = response.json()
        pretty_print("Detected Conflicts", data)
        
        if data['conflicts']:
            # 2. Resolve conflicts
            print(f"\n2. Resolving {len(data['conflicts'])} conflicts...")
            resolve_data = {
                "conflicts": data['conflicts']
            }
            
            response = session.post(f"{BASE_URL}/api/memory/resolve-conflicts", json=resolve_data)
            if response.status_code == 200:
                pretty_print("Conflict Resolutions", response.json())
            else:
                print(f"❌ Conflict resolution failed: {response.text}")
        else:
            print("ℹ️ No conflicts detected")
    else:
        print(f"❌ Conflict detection failed: {response.text}")

def test_memory_evolution(session, test_memories):
    """Test memory evolution tracking"""
    print("\n📈 Testing Memory Evolution Tracking...")
    
    if test_memories['episodic']:
        memory_id = test_memories['episodic'][0]
        print(f"\n1. Getting evolution history for memory {memory_id}...")
        
        response = session.get(f"{BASE_URL}/api/memory/evolution/{memory_id}")
        if response.status_code == 200:
            pretty_print("Memory Evolution History", response.json())
        else:
            print(f"❌ Evolution tracking failed: {response.text}")

def test_bulk_operations(session, test_memories):
    """Test bulk memory operations"""
    print("\n📦 Testing Bulk Memory Operations...")
    
    # 1. Bulk improve memories
    all_memory_ids = []
    all_memory_ids.extend(test_memories['episodic'])
    all_memory_ids.extend(test_memories['procedural'])
    all_memory_ids.extend(test_memories['semantic'])
    
    if all_memory_ids:
        print(f"\n1. Bulk improving {len(all_memory_ids)} memories...")
        bulk_data = {
            "memory_ids": all_memory_ids,
            "improvement_type": "auto"
        }
        
        response = session.post(f"{BASE_URL}/api/memory/bulk-improve", json=bulk_data)
        if response.status_code == 200:
            pretty_print("Bulk Improvement Results", response.json())
        else:
            print(f"❌ Bulk improvement failed: {response.text}")
    
    # 2. Auto-consolidate memories
    print("\n2. Auto-consolidating similar memories...")
    consolidate_data = {}
    
    response = session.post(f"{BASE_URL}/api/memory/auto-consolidate?namespace=episodes&similarity=0.8", json=consolidate_data)
    if response.status_code == 200:
        pretty_print("Auto-Consolidation Results", response.json())
    else:
        print(f"❌ Auto-consolidation failed: {response.text}")

def test_advanced_features(session):
    """Test advanced memory editing features"""
    print("\n🚀 Testing Advanced Memory Features...")
    
    # 1. Test memory similarity calculation
    print("\n1. Testing memory similarity calculation...")
    
    # Get some memories to compare
    response = session.get(f"{BASE_URL}/api/memory/episodes?limit=5")
    if response.status_code == 200:
        memories = response.json().get('episodes', [])
        if len(memories) >= 2:
            memory1 = memories[0]
            memory2 = memories[1]
            
            print(f"Comparing memories: {memory1['memory_id']} vs {memory2['memory_id']}")
            
            # This would require accessing the service method directly
            # For now, we'll just show the memory data
            print(f"Memory 1 data: {memory1['memory_data']}")
            print(f"Memory 2 data: {memory2['memory_data']}")

def main():
    """Main test function"""
    print("🧠 Memory Editing & Improvement System Test")
    print("=" * 60)
    
    # Login
    session = login()
    if not session:
        return
    
    try:
        # Create test memories
        test_memories = create_test_memories(session)
        
        # Wait a moment for memories to be processed
        time.sleep(1)
        
        # Run all tests
        test_memory_merging(session, test_memories)
        test_memory_improvement(session, test_memories)
        test_quality_assessment(session, test_memories)
        test_conflict_detection(session)
        test_memory_evolution(session, test_memories)
        test_bulk_operations(session, test_memories)
        test_advanced_features(session)
        
        print("\n✅ All memory editing tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    main() 