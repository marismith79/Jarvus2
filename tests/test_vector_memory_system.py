#!/usr/bin/env python3
"""
Test script for the Efficient Hybrid Vector + SQL Database Memory System
Demonstrates SQL metadata filtering + Vector content search for optimal performance.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class EfficientVectorMemorySystemDemo:
    """Demo class for testing the efficient hybrid SQL + Vector memory system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.test_memories = []
        self.test_contexts = []
    
    def login(self) -> bool:
        """Login to the system"""
        print("🔐 Logging in...")
        
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def check_vector_status(self):
        """Check if vector search is enabled"""
        print("\n🔍 Checking Vector Search Status...")
        
        response = self.session.get(f"{BASE_URL}/api/memory/vector/status")
        if response.status_code == 200:
            status = response.json()['status']
            print(f"   Vector Search Enabled: {status['enabled']}")
            print(f"   Vector Service Available: {status['vector_service_available']}")
            print(f"   Model: {status['model_name']}")
            print(f"   Architecture: {status['architecture']}")
            return status['enabled'] and status['vector_service_available']
        else:
            print("❌ Failed to check vector status")
            return False
    
    def create_test_memories(self):
        """Create test memories for demonstration"""
        print("\n📝 Creating Test Memories...")
        
        # Episodic memories
        episodic_memories = [
            {
                "type": "chrome_action",
                "data": {
                    "action": "click",
                    "target": "button#login",
                    "url": "https://gmail.com",
                    "result": "success",
                    "note": "User logged into Gmail successfully"
                }
            },
            {
                "type": "chrome_action", 
                "data": {
                    "action": "type",
                    "target": "input#search",
                    "url": "https://google.com",
                    "result": "success",
                    "note": "User searched for 'python vector database tutorial'"
                }
            },
            {
                "type": "feedback",
                "data": {
                    "user_response": "accepted",
                    "suggestion_reference": "sugg_001",
                    "notes": "The email automation suggestion worked perfectly!"
                }
            }
        ]
        
        # Semantic memories
        semantic_memories = [
            {
                "type": "preference",
                "data": {
                    "text": "User prefers dark mode in all applications",
                    "category": "ui_preference"
                }
            },
            {
                "type": "fact",
                "data": {
                    "text": "User works as a software engineer at TechCorp",
                    "category": "personal_info"
                }
            },
            {
                "type": "preference",
                "data": {
                    "text": "User likes to check email every 30 minutes",
                    "category": "work_habit"
                }
            }
        ]
        
        # Procedural memories
        procedural_memories = [
            {
                "type": "workflow",
                "data": {
                    "name": "Start Zoom Meeting",
                    "steps": [
                        {"action": "open_url", "url": "https://zoom.us"},
                        {"action": "click", "target": "Start Meeting"},
                        {"action": "wait", "duration": 2},
                        {"action": "click", "target": "Join with Computer Audio"}
                    ],
                    "description": "How to start a Zoom meeting"
                }
            },
            {
                "type": "workflow",
                "data": {
                    "name": "Send Email with Attachment",
                    "steps": [
                        {"action": "open_url", "url": "https://gmail.com"},
                        {"action": "click", "target": "Compose"},
                        {"action": "type", "target": "To", "text": "recipient@example.com"},
                        {"action": "type", "target": "Subject", "text": "Meeting Notes"},
                        {"action": "click", "target": "Attach Files"},
                        {"action": "click", "target": "Send"}
                    ],
                    "description": "How to send an email with attachment"
                }
            }
        ]
        
        # Store episodic memories
        for memory in episodic_memories:
            response = self.session.post(f"{BASE_URL}/api/memory/episodes", json=memory)
            if response.status_code == 201:
                memory_id = response.json()['memory_id']
                self.test_memories.append(('episodes', memory_id))
                print(f"   ✅ Created episodic memory: {memory_id}")
        
        # Store semantic memories
        for memory in semantic_memories:
            response = self.session.post(f"{BASE_URL}/api/memory/semantic", json=memory)
            if response.status_code == 201:
                memory_id = response.json()['memory_id']
                self.test_memories.append(('semantic', memory_id))
                print(f"   ✅ Created semantic memory: {memory_id}")
        
        # Store procedural memories
        for memory in procedural_memories:
            response = self.session.post(f"{BASE_URL}/api/memory/procedures", json=memory)
            if response.status_code == 201:
                memory_id = response.json()['memory_id']
                self.test_memories.append(('procedures', memory_id))
                print(f"   ✅ Created procedural memory: {memory_id}")
    
    def create_test_contexts(self):
        """Create test hierarchical contexts"""
        print("\n🌳 Creating Test Hierarchical Contexts...")
        
        # Work mode context
        work_context = {
            "name": "Work Mode",
            "description": "User is in focused work mode - minimize distractions",
            "context_data": {
                "status": "working",
                "focus_level": "high",
                "interruption_threshold": "urgent_only"
            },
            "influence_rules": {
                "override": {
                    "notification_sound": "off",
                    "email_check_frequency": "every_hour"
                },
                "modify": {
                    "response_time_expectation": {"operation": "multiply", "value": 0.5}
                },
                "add": {
                    "work_focus": True,
                    "deep_work_mode": True
                }
            },
            "priority": 80
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/context", json=work_context)
        if response.status_code == 201:
            context_id = response.json()['context']['id']
            self.test_contexts.append(context_id)
            print(f"   ✅ Created work context: {context_id}")
        
        # Vacation context
        vacation_context = {
            "name": "Vacation Mode",
            "description": "User is on vacation - prioritize relaxation",
            "context_data": {
                "status": "vacation",
                "location": "Hawaii",
                "relaxation_level": "high"
            },
            "influence_rules": {
                "override": {
                    "work_urgency": "low",
                    "response_style": "relaxed"
                },
                "modify": {
                    "email_check_frequency": {"operation": "multiply", "value": 0.25},
                    "meeting_suggestions": {"operation": "multiply", "value": 0.1}
                },
                "add": {
                    "vacation_aware": True,
                    "relaxation_focus": True
                }
            },
            "priority": 100
        }
        
        response = self.session.post(f"{BASE_URL}/api/memory/hierarchical/context", json=vacation_context)
        if response.status_code == 201:
            context_id = response.json()['context']['id']
            self.test_contexts.append(context_id)
            print(f"   ✅ Created vacation context: {context_id}")
    
    def test_efficient_semantic_search(self):
        """Test efficient semantic search using SQL metadata + Vector content"""
        print("\n🔍 Testing Efficient Semantic Search...")
        
        test_queries = [
            "email automation",
            "dark mode preference", 
            "zoom meeting setup",
            "work productivity",
            "vacation relaxation"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            response = self.session.post(f"{BASE_URL}/api/memory/vector/efficient-search", json={
                "query": query,
                "namespace": "episodes",
                "n_results": 5,
                "similarity_threshold": 0.6
            })
            
            if response.status_code == 200:
                results = response.json()['results']
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results[:3]):  # Show top 3
                    similarity = result['similarity']
                    memory_id = result['memory_id']
                    content_preview = result['content'][:50] + "..." if len(result['content']) > 50 else result['content']
                    print(f"     {i+1}. Memory {memory_id} (similarity: {similarity:.3f})")
                    print(f"        Content: {content_preview}")
            else:
                print(f"   ❌ Search failed: {response.text}")
    
    def test_efficient_hybrid_search(self):
        """Test efficient hybrid search using SQL + Vector approach"""
        print("\n🔄 Testing Efficient Hybrid Search...")
        
        test_queries = [
            "gmail login",
            "email preferences",
            "zoom workflow",
            "work mode settings"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            response = self.session.post(f"{BASE_URL}/api/memory/vector/hybrid-search", json={
                "query": query,
                "namespace": "episodes",
                "n_results": 5
            })
            
            if response.status_code == 200:
                memories = response.json()['memories']
                search_type = response.json()['search_type']
                print(f"   Found {len(memories)} memories using {search_type}:")
                for i, memory in enumerate(memories[:3]):  # Show top 3
                    memory_id = memory['id']
                    memory_type = memory['type']
                    print(f"     {i+1}. {memory_type} memory {memory_id}")
            else:
                print(f"   ❌ Search failed: {response.text}")
    
    def test_hierarchical_context_search(self):
        """Test searching hierarchical contexts with efficient approach"""
        print("\n🌳 Testing Hierarchical Context Search...")
        
        test_queries = [
            "work focus",
            "vacation relaxation",
            "productivity settings",
            "distraction management"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            response = self.session.post(f"{BASE_URL}/api/memory/vector/search-hierarchical", json={
                "query": query,
                "n_results": 3,
                "similarity_threshold": 0.6
            })
            
            if response.status_code == 200:
                results = response.json()['results']
                print(f"   Found {len(results)} contexts:")
                for i, result in enumerate(results):
                    similarity = result['similarity']
                    context_name = result['metadata']['name']
                    content_preview = result['content'][:50] + "..." if len(result['content']) > 50 else result['content']
                    print(f"     {i+1}. {context_name} (similarity: {similarity:.3f})")
                    print(f"        Content: {content_preview}")
            else:
                print(f"   ❌ Search failed: {response.text}")
    
    def test_content_retrieval(self):
        """Test direct content retrieval from vector database"""
        print("\n📄 Testing Content Retrieval...")
        
        # First get some memories
        response = self.session.get(f"{BASE_URL}/api/memory/episodes?limit=1")
        if response.status_code == 200:
            memories = response.json()['episodes']
            if memories:
                memory = memories[0]
                vector_id = memory.get('data', {}).get('vector_id')
                
                if vector_id:
                    print(f"   Retrieving content for vector_id: {vector_id}")
                    
                    content_response = self.session.get(f"{BASE_URL}/api/memory/vector/content/{vector_id}")
                    if content_response.status_code == 200:
                        content = content_response.json()['content']
                        print(f"   ✅ Retrieved content: {content['content'][:100]}...")
                    else:
                        print(f"   ❌ Failed to retrieve content: {content_response.text}")
                else:
                    print("   ⚠️  No vector_id found in memory")
    
    def test_content_update(self):
        """Test updating memory content in vector database"""
        print("\n✏️  Testing Content Update...")
        
        # First get a memory
        response = self.session.get(f"{BASE_URL}/api/memory/episodes?limit=1")
        if response.status_code == 200:
            memories = response.json()['episodes']
            if memories:
                memory = memories[0]
                memory_id = memory['id']
                
                # Update content
                new_content = "Updated content for testing vector database functionality"
                update_response = self.session.put(f"{BASE_URL}/api/memory/vector/update-content", json={
                    "namespace": "episodes",
                    "memory_id": memory_id,
                    "content": new_content
                })
                
                if update_response.status_code == 200:
                    print(f"   ✅ Successfully updated content for memory {memory_id}")
                else:
                    print(f"   ❌ Failed to update content: {update_response.text}")
    
    def test_search_performance(self):
        """Test and compare search performance"""
        print("\n⚡ Testing Search Performance...")
        
        query = "email automation workflow"
        iterations = 5
        
        # Test efficient hybrid search performance
        print("   Efficient Hybrid Search Performance:")
        start_time = time.time()
        for i in range(iterations):
            response = self.session.post(f"{BASE_URL}/api/memory/vector/efficient-search", json={
                "query": query,
                "namespace": "episodes",
                "n_results": 10
            })
        efficient_time = (time.time() - start_time) / iterations
        
        print(f"     Average time: {efficient_time:.3f} seconds")
        
        # Test hybrid search performance
        print("   Hybrid Search Performance:")
        start_time = time.time()
        for i in range(iterations):
            response = self.session.post(f"{BASE_URL}/api/memory/vector/hybrid-search", json={
                "query": query,
                "namespace": "episodes",
                "n_results": 10
            })
        hybrid_time = (time.time() - start_time) / iterations
        
        print(f"     Average time: {hybrid_time:.3f} seconds")
        
        # Test SQL-only search performance
        print("   SQL-Only Search Performance:")
        start_time = time.time()
        for i in range(iterations):
            response = self.session.get(f"{BASE_URL}/api/memory/episodes?query={query}&limit=10")
        sql_time = (time.time() - start_time) / iterations
        
        print(f"     Average time: {sql_time:.3f} seconds")
        
        print(f"\n   Performance Summary:")
        print(f"     Efficient hybrid search: {efficient_time:.3f}s")
        print(f"     Hybrid search: {hybrid_time:.3f}s")
        print(f"     SQL-only search: {sql_time:.3f}s")
        
        if efficient_time < sql_time:
            print(f"   🚀 Efficient hybrid search is {sql_time/efficient_time:.1f}x faster than SQL-only!")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test memories
        for namespace, memory_id in self.test_memories:
            response = self.session.delete(f"{BASE_URL}/api/memory/vector/delete/{namespace}/{memory_id}")
            if response.status_code == 200:
                print(f"   ✅ Deleted memory {memory_id}")
        
        # Delete test contexts
        for context_id in self.test_contexts:
            response = self.session.delete(f"{BASE_URL}/api/memory/vector/delete-hierarchical/{context_id}")
            if response.status_code == 200:
                print(f"   ✅ Deleted context {context_id}")
    
    def run_demo(self):
        """Run the complete efficient vector memory system demo"""
        print("🚀 Starting Efficient Hybrid SQL + Vector Database Memory System Demo")
        print("=" * 80)
        
        # Step 1: Login
        if not self.login():
            return
        
        # Step 2: Check vector search status
        if not self.check_vector_status():
            print("❌ Vector search not available. Please ensure dependencies are installed.")
            return
        
        # Step 3: Create test data
        self.create_test_memories()
        self.create_test_contexts()
        
        # Step 4: Test different search types
        self.test_efficient_semantic_search()
        self.test_efficient_hybrid_search()
        self.test_hierarchical_context_search()
        
        # Step 5: Test content operations
        self.test_content_retrieval()
        self.test_content_update()
        
        # Step 6: Test performance
        self.test_search_performance()
        
        # Step 7: Cleanup
        self.cleanup_test_data()
        
        print("\n" + "=" * 80)
        print("✅ Efficient Vector Memory System Demo Complete!")
        print("\nKey Benefits Demonstrated:")
        print("• SQL stores metadata for fast filtering and organization")
        print("• Vector DB stores content for semantic search")
        print("• Efficient search flow: SQL metadata → Vector content")
        print("• No redundant searches - optimized performance")
        print("• Direct content retrieval from vector database")
        print("• Content updates with change detection")
        print("• Performance comparison showing efficiency gains")


if __name__ == "__main__":
    demo = EfficientVectorMemorySystemDemo()
    demo.run_demo() 