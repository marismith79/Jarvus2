"""
Vector Memory Service for Efficient Hybrid Search
Implements SQL (metadata) + Vector DB (content) hybrid system for optimal performance.
"""

import chromadb
import numpy as np
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer

from ..db import db
from ..models.memory import LongTermMemory, HierarchicalMemory

logger = logging.getLogger(__name__)


class VectorMemoryService:
    """Service for efficient hybrid search using SQL metadata + Vector DB content"""
    
    def __init__(self, persist_directory="./chroma_db", model_name="all-MiniLM-L6-v2"):
        """Initialize vector memory service with ChromaDB and embedding model"""
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.encoder = SentenceTransformer(model_name)
            self.model_name = model_name
            
            # Single collection for all memory content
            self.memory_collection = self.client.get_or_create_collection("memory_content")
            self.context_collection = self.client.get_or_create_collection("context_content")
            
            logger.info(f"Vector memory service initialized with model {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector memory service: {str(e)}")
            raise
    
    def store_memory_content(
        self, 
        memory: LongTermMemory, 
        content_text: str
    ) -> str:
        """Store memory content in vector DB and return vector_id"""
        try:
            # Generate embedding
            embedding = self.encoder.encode(content_text).tolist()
            
            # Create unique vector ID
            vector_id = f"mem_{memory.user_id}_{memory.memory_id}"
            
            # Store in vector database
            self.memory_collection.add(
                embeddings=[embedding],
                documents=[content_text],
                metadatas=[{
                    'memory_id': memory.memory_id,
                    'user_id': memory.user_id,
                    'namespace': memory.namespace,
                    'memory_type': memory.memory_type,
                    'content_hash': hash(content_text)  # For content change detection
                }],
                ids=[vector_id]
            )
            
            logger.info(f"Stored memory content for {memory.memory_id} with vector_id {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Failed to store memory content: {str(e)}")
            raise
    
    def store_context_content(
        self, 
        context: HierarchicalMemory, 
        content_text: str
    ) -> str:
        """Store hierarchical context content in vector DB"""
        try:
            # Generate embedding
            embedding = self.encoder.encode(content_text).tolist()
            
            # Create unique vector ID
            vector_id = f"ctx_{context.user_id}_{context.memory_id}"
            
            # Store in context collection
            self.context_collection.add(
                embeddings=[embedding],
                documents=[content_text],
                metadatas=[{
                    'memory_id': context.memory_id,
                    'user_id': context.user_id,
                    'level': context.level,
                    'path': context.path,
                    'name': context.name,
                    'is_active': context.is_active,
                    'priority': context.priority,
                    'content_hash': hash(content_text)
                }],
                ids=[vector_id]
            )
            
            logger.info(f"Stored context content for {context.memory_id} with vector_id {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Failed to store context content: {str(e)}")
            raise
    
    def efficient_hybrid_search(
        self, 
        query: str, 
        user_id: int, 
        namespace: str, 
        n_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Efficient hybrid search: SQL metadata filtering + Vector content search"""
        try:
            # Step 1: Query SQL database for relevant metadata/categories
            sql_candidates = self._get_sql_candidates(user_id, namespace, query)
            
            if not sql_candidates:
                logger.info("No SQL candidates found, returning empty results")
                return []
            
            # Step 2: Extract memory IDs from SQL results
            memory_ids = [candidate['memory_id'] for candidate in sql_candidates]
            
            # Step 3: Search vector database only for relevant content
            vector_results = self._search_vector_content(
                query, memory_ids, n_results, similarity_threshold
            )
            
            # Step 4: Combine SQL metadata with vector results
            combined_results = self._combine_sql_vector_results(
                sql_candidates, vector_results
            )
            
            logger.info(f"Efficient hybrid search returned {len(combined_results)} results")
            return combined_results
            
        except Exception as e:
            logger.error(f"Failed to perform efficient hybrid search: {str(e)}")
            return []
    
    def search_contexts_efficient(
        self, 
        query: str, 
        user_id: int, 
        n_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Efficient context search using SQL filtering + Vector content search"""
        try:
            # Step 1: Get active contexts from SQL
            active_contexts = self._get_active_contexts_sql(user_id)
            
            if not active_contexts:
                return []
            
            # Step 2: Extract context IDs
            context_ids = [ctx['memory_id'] for ctx in active_contexts]
            
            # Step 3: Search vector database for context content
            vector_results = self._search_context_content(
                query, context_ids, n_results, similarity_threshold
            )
            
            # Step 4: Combine results
            combined_results = self._combine_context_results(
                active_contexts, vector_results
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Failed to search contexts efficiently: {str(e)}")
            return []
    
    def get_memory_by_vector_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get memory content by vector ID"""
        try:
            results = self.memory_collection.get(ids=[vector_id])
            if results['documents']:
                return {
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'vector_id': vector_id
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory by vector ID: {str(e)}")
            return None
    
    def update_memory_content(
        self, 
        memory: LongTermMemory, 
        new_content: str
    ) -> bool:
        """Update memory content in vector database"""
        try:
            vector_id = f"mem_{memory.user_id}_{memory.memory_id}"
            
            # Check if content has changed
            new_hash = hash(new_content)
            
            # Get existing content
            existing = self.get_memory_by_vector_id(vector_id)
            if existing and existing['metadata']['content_hash'] == new_hash:
                logger.info(f"Content unchanged for {memory.memory_id}")
                return True
            
            # Update content
            embedding = self.encoder.encode(new_content).tolist()
            
            self.memory_collection.update(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[new_content],
                metadatas=[{
                    'memory_id': memory.memory_id,
                    'user_id': memory.user_id,
                    'namespace': memory.namespace,
                    'memory_type': memory.memory_type,
                    'content_hash': new_hash
                }]
            )
            
            logger.info(f"Updated memory content for {memory.memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory content: {str(e)}")
            return False
    
    def delete_memory_content(self, user_id: int, memory_id: str) -> bool:
        """Delete memory content from vector database"""
        try:
            vector_id = f"mem_{user_id}_{memory_id}"
            self.memory_collection.delete(ids=[vector_id])
            logger.info(f"Deleted memory content for {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory content: {str(e)}")
            return False
    
    def delete_context_content(self, user_id: int, memory_id: str) -> bool:
        """Delete context content from vector database"""
        try:
            vector_id = f"ctx_{user_id}_{memory_id}"
            self.context_collection.delete(ids=[vector_id])
            logger.info(f"Deleted context content for {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete context content: {str(e)}")
            return False
    
    def _get_sql_candidates(
        self, 
        user_id: int, 
        namespace: str, 
        query: str
    ) -> List[Dict[str, Any]]:
        """Get relevant memory candidates from SQL database using metadata"""
        try:
            # Use SQL to filter by metadata (namespace, type, importance, etc.)
            # This is much faster than searching all content
            memories = LongTermMemory.query.filter_by(
                user_id=user_id,
                namespace=namespace
            ).order_by(
                LongTermMemory.importance_score.desc(),
                LongTermMemory.last_accessed.desc()
            ).limit(100).all()  # Get top candidates
            
            # Simple keyword matching on search_text for initial filtering
            candidates = []
            query_lower = query.lower()
            
            for memory in memories:
                if memory.search_text and query_lower in memory.search_text.lower():
                    candidates.append({
                        'memory_id': memory.memory_id,
                        'namespace': memory.namespace,
                        'memory_type': memory.memory_type,
                        'importance_score': memory.importance_score,
                        'last_accessed': memory.last_accessed,
                        'search_text': memory.search_text
                    })
            
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to get SQL candidates: {str(e)}")
            return []
    
    def _get_active_contexts_sql(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active contexts from SQL database"""
        try:
            contexts = HierarchicalMemory.query.filter_by(
                user_id=user_id,
                is_active=True
            ).order_by(
                HierarchicalMemory.priority.desc(),
                HierarchicalMemory.last_accessed.desc()
            ).all()
            
            return [{
                'memory_id': ctx.memory_id,
                'name': ctx.name,
                'level': ctx.level,
                'path': ctx.path,
                'priority': ctx.priority,
                'is_active': ctx.is_active
            } for ctx in contexts]
            
        except Exception as e:
            logger.error(f"Failed to get active contexts from SQL: {str(e)}")
            return []
    
    def _search_vector_content(
        self, 
        query: str, 
        memory_ids: List[str], 
        n_results: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Search vector database for specific memory content"""
        try:
            if not memory_ids:
                return []
            
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search only in the memory collection
            results = self.memory_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"memory_id": {"$in": memory_ids}}
            )
            
            # Process results
            processed_results = []
            for i in range(len(results['ids'][0])):
                memory_id = results['metadatas'][0][i]['memory_id']
                distance = results['distances'][0][i]
                similarity = 1.0 / (1.0 + distance)
                
                if similarity >= similarity_threshold:
                    processed_results.append({
                        'memory_id': memory_id,
                        'similarity': similarity,
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to search vector content: {str(e)}")
            return []
    
    def _search_context_content(
        self, 
        query: str, 
        context_ids: List[str], 
        n_results: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Search vector database for context content"""
        try:
            if not context_ids:
                return []
            
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search in context collection
            results = self.context_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"memory_id": {"$in": context_ids}}
            )
            
            # Process results
            processed_results = []
            for i in range(len(results['ids'][0])):
                memory_id = results['metadatas'][0][i]['memory_id']
                distance = results['distances'][0][i]
                similarity = 1.0 / (1.0 + distance)
                
                if similarity >= similarity_threshold:
                    processed_results.append({
                        'memory_id': memory_id,
                        'similarity': similarity,
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to search context content: {str(e)}")
            return []
    
    def _combine_sql_vector_results(
        self, 
        sql_candidates: List[Dict[str, Any]], 
        vector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine SQL metadata with vector search results"""
        try:
            # Create lookup for SQL candidates
            sql_lookup = {c['memory_id']: c for c in sql_candidates}
            
            # Combine results
            combined_results = []
            for vector_result in vector_results:
                memory_id = vector_result['memory_id']
                sql_data = sql_lookup.get(memory_id, {})
                
                combined_results.append({
                    'memory_id': memory_id,
                    'similarity': vector_result['similarity'],
                    'content': vector_result['content'],
                    'metadata': {
                        **sql_data,
                        **vector_result['metadata']
                    }
                })
            
            # Sort by similarity
            combined_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Failed to combine SQL-vector results: {str(e)}")
            return []
    
    def _combine_context_results(
        self, 
        sql_contexts: List[Dict[str, Any]], 
        vector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine SQL context metadata with vector search results"""
        try:
            # Create lookup for SQL contexts
            sql_lookup = {c['memory_id']: c for c in sql_contexts}
            
            # Combine results
            combined_results = []
            for vector_result in vector_results:
                memory_id = vector_result['memory_id']
                sql_data = sql_lookup.get(memory_id, {})
                
                combined_results.append({
                    'memory_id': memory_id,
                    'similarity': vector_result['similarity'],
                    'content': vector_result['content'],
                    'metadata': {
                        **sql_data,
                        **vector_result['metadata']
                    }
                })
            
            # Sort by similarity
            combined_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Failed to combine context results: {str(e)}")
            return [] 