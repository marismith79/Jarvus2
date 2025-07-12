"""
Parameter Inference Service
Handles intelligent parameter inference for tool calls to reduce clarification questions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..db import db
from ..models.memory import LongTermMemory
from .memory_service import memory_service
from ..llm.client import JarvusAIClient

logger = logging.getLogger(__name__)


class ParameterInferenceService:
    """Service for inferring tool parameters from user memory and preferences"""
    
    def __init__(self):
        self.llm_client = JarvusAIClient()
        
        # Pre-defined parameter inference rules for common tools
        self.parameter_rules = {
            # Calendar tools
            "create_calendar_event": {
                "duration": {
                    "default": "60",
                    "inference_prompt": "What is the typical meeting duration for this user?",
                    "memory_key": "meeting_duration_preference"
                },
                "timezone": {
                    "default": "UTC",
                    "inference_prompt": "What timezone does this user typically use?",
                    "memory_key": "timezone_preference"
                },
                "reminder": {
                    "default": "15",
                    "inference_prompt": "What reminder time does this user prefer?",
                    "memory_key": "reminder_preference"
                }
            },
            "update_calendar_event": {
                "timezone": {
                    "default": "UTC",
                    "inference_prompt": "What timezone does this user typically use?",
                    "memory_key": "timezone_preference"
                }
            },
            # Email tools
            "send_email": {
                "signature": {
                    "default": "",
                    "inference_prompt": "What email signature does this user use?",
                    "memory_key": "email_signature"
                },
                "priority": {
                    "default": "normal",
                    "inference_prompt": "What priority level does this user typically use for emails?",
                    "memory_key": "email_priority_preference"
                }
            },
            # Document tools
            "create_document": {
                "title": {
                    "default": "Untitled Document",
                    "inference_prompt": "What would be an appropriate title for this document based on the context?",
                    "memory_key": "document_naming_pattern"
                },
                "folder": {
                    "default": "root",
                    "inference_prompt": "What folder does this user typically use for documents?",
                    "memory_key": "document_folder_preference"
                }
            },
            # Web search tools
            "google_web_search": {
                "num_results": {
                    "default": "10",
                    "inference_prompt": "How many search results does this user typically want?",
                    "memory_key": "search_results_preference"
                }
            }
        }
    
    def infer_missing_parameters(
        self, 
        user_id: int, 
        tool_name: str, 
        provided_params: Dict[str, Any],
        user_message: str,
        conversation_context: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Infer missing parameters for a tool call using semantic memory and user preferences.
        
        Args:
            user_id: User ID
            tool_name: Name of the tool being called
            provided_params: Parameters already provided
            user_message: Current user message
            conversation_context: Recent conversation context
            
        Returns:
            Dict with inferred parameters merged with provided parameters
        """
        try:
            logger.info(f"🔍 Parameter inference called for tool: {tool_name}")
            logger.info(f"🔍 Provided params: {provided_params}")
            logger.info(f"🔍 User message: {user_message[:100]}...")
            
            # Get tool parameter rules
            tool_rules = self.parameter_rules.get(tool_name, {})
            if not tool_rules:
                logger.info(f"⚠️  No parameter rules found for tool: {tool_name}")
                return provided_params
            
            # Get tool schema to understand required parameters
            tool_schema = self._get_tool_schema(tool_name)
            if not tool_schema:
                return provided_params
            
            inferred_params = provided_params.copy()
            
            # Check each parameter that has inference rules
            for param_name, param_rules in tool_rules.items():
                # Skip if parameter is already provided
                if param_name in provided_params:
                    logger.info(f"ℹ️  Parameter {param_name} already provided, skipping inference")
                    continue
                
                logger.info(f"🔍 Checking parameter: {param_name}")
                
                # Check if parameter is required in tool schema
                if self._is_parameter_required(tool_schema, param_name):
                    inferred_value = self._infer_parameter_value(
                        user_id=user_id,
                        param_name=param_name,
                        param_rules=param_rules,
                        user_message=user_message,
                        conversation_context=conversation_context,
                        tool_name=tool_name
                    )
                    if inferred_value is not None:
                        inferred_params[param_name] = inferred_value
                        logger.info(f"✅ Inferred parameter {param_name}={inferred_value} for tool {tool_name}")
                    else:
                        logger.info(f"❌ Could not infer parameter {param_name} for tool {tool_name}")
                else:
                    logger.info(f"ℹ️  Parameter {param_name} not required, skipping inference")
            
            logger.info(f"🔍 Final inferred params: {inferred_params}")
            return inferred_params
            
        except Exception as e:
            logger.error(f"Error inferring parameters for tool {tool_name}: {str(e)}")
            return provided_params
    
    def _infer_parameter_value(
        self,
        user_id: int,
        param_name: str,
        param_rules: Dict[str, Any],
        user_message: str,
        conversation_context: List[Dict[str, str]] = None,
        tool_name: str = None
    ) -> Any:
        """
        Infer a specific parameter value using multiple strategies.
        
        Returns:
            Inferred value or None if no inference possible
        """
        # Strategy 1: Check semantic memory for user preferences
        memory_value = self._get_parameter_from_memory(user_id, param_rules.get('memory_key'))
        if memory_value is not None:
            return memory_value
        
        # Strategy 2: Use LLM to infer from conversation context
        if conversation_context:
            llm_value = self._infer_from_conversation_context(
                param_name, param_rules, user_message, conversation_context, tool_name
            )
            if llm_value is not None:
                return llm_value
        
        # Strategy 3: Use default value
        return param_rules.get('default')
    
    def _get_parameter_from_memory(self, user_id: int, memory_key: str) -> Any:
        """Get parameter value from user's semantic memory."""
        if not memory_key:
            logger.info(f"❌ No memory key provided for parameter lookup")
            return None
        
        try:
            logger.info(f"🔍 Searching memory for key: {memory_key}")
            memories = memory_service.search_memories(
                user_id=user_id,
                namespace='semantic',
                query=memory_key,
                limit=5
            )
            
            logger.info(f"🔍 Found {len(memories)} memories for key: {memory_key}")
            
            for memory in memories:
                memory_data = memory.memory_data.get('data', {})
                if memory_key in memory_data:
                    value = memory_data[memory_key]
                    logger.info(f"✅ Found parameter value in memory: {memory_key}={value}")
                    return value
                
                # Also check preference_type field
                if memory_data.get('preference_type') == memory_key:
                    value = memory_data.get('value')
                    logger.info(f"✅ Found parameter value in preference: {memory_key}={value}")
                    return value
            
            logger.info(f"❌ No parameter value found in memory for key: {memory_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting parameter from memory: {str(e)}")
            return None
    
    def _infer_from_conversation_context(
        self,
        param_name: str,
        param_rules: Dict[str, Any],
        user_message: str,
        conversation_context: List[Dict[str, str]],
        tool_name: str
    ) -> Any:
        """Use LLM to infer parameter value from conversation context."""
        try:
            # Build context for the LLM
            context_text = ""
            if conversation_context:
                # Include recent conversation context
                recent_context = conversation_context[-4:] if len(conversation_context) > 4 else conversation_context
                for msg in recent_context:
                    if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                        context_text += f"{msg['role']}: {msg['content']}\n"
            
            inference_prompt = param_rules.get('inference_prompt', f"What is the appropriate value for {param_name}?")
            
            prompt = f"""
You are helping to infer a parameter value for a tool call. 

Tool: {tool_name}
Parameter: {param_name}
Inference question: {inference_prompt}

Recent conversation context:
{context_text}

Current user message: {user_message}

Based on the conversation context and user message, what would be the most appropriate value for the {param_name} parameter?

Respond with ONLY the value, no explanation. If you cannot determine a value, respond with "UNKNOWN".
"""
            
            # Get LLM analysis
            analysis_messages = [
                {"role": "system", "content": "You are a parameter inference expert. Respond with only the value."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = self.llm_client.create_chat_completion(analysis_messages)
                analysis_result = response['choices'][0]['message']['content'].strip()
            except Exception as e:
                logger.warning(f"LLM analysis failed: {str(e)}")
                return None
            
            if analysis_result.upper() == "UNKNOWN" or not analysis_result:
                return None
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation context with LLM: {str(e)}")
            return None
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a tool to understand its parameters."""
        try:
            # This would need to be implemented based on your tool registry
            # For now, return None to use the parameter rules
            return None
        except Exception as e:
            logger.error(f"Error getting tool schema: {str(e)}")
            return None
    
    def _is_parameter_required(self, tool_schema: Optional[Dict[str, Any]], param_name: str) -> bool:
        """Check if a parameter is required in the tool schema."""
        if not tool_schema:
            # If no schema available, assume all parameters in rules are important
            return True
        
        try:
            required_params = tool_schema.get('required', [])
            return param_name in required_params
        except Exception:
            return True
    
    def store_parameter_preference(
        self,
        user_id: int,
        tool_name: str,
        parameter_name: str,
        value: Any,
        context: str = None
    ):
        """Store a user's parameter preference for future inference."""
        try:
            memory_data = {
                "tool_name": tool_name,
                "parameter_name": parameter_name,
                "value": value,
                "context": context,
                "stored_at": datetime.utcnow().isoformat()
            }
            
            memory_service.store_semantic_memory(
                user_id=user_id,
                fact_type="parameter_preference",
                fact_data=memory_data,
                importance_score=2.0
            )
            
            logger.info(f"Stored parameter preference: {tool_name}.{parameter_name}={value}")
            
        except Exception as e:
            logger.error(f"Error storing parameter preference: {str(e)}")
    
    def learn_from_tool_execution(
        self,
        user_id: int,
        tool_name: str,
        parameters: Dict[str, Any],
        success: bool,
        user_feedback: str = None
    ):
        """Learn from tool execution to improve future parameter inference."""
        try:
            if success:
                # Store successful parameter combinations
                for param_name, param_value in parameters.items():
                    self.store_parameter_preference(
                        user_id=user_id,
                        tool_name=tool_name,
                        parameter_name=param_name,
                        value=param_value,
                        context=f"Successful execution with user feedback: {user_feedback}"
                    )
            else:
                # Store failed parameter combinations to avoid them
                for param_name, param_value in parameters.items():
                    memory_data = {
                        "tool_name": tool_name,
                        "parameter_name": param_name,
                        "value": param_value,
                        "context": f"Failed execution: {user_feedback}",
                        "avoid_in_future": True,
                        "stored_at": datetime.utcnow().isoformat()
                    }
                    
                    memory_service.store_semantic_memory(
                        user_id=user_id,
                        fact_type="parameter_avoidance",
                        fact_data=memory_data,
                        importance_score=3.0  # Higher importance for avoiding failures
                    )
            
        except Exception as e:
            logger.error(f"Error learning from tool execution: {str(e)}")


# Global parameter inference service instance
parameter_inference_service = ParameterInferenceService() 