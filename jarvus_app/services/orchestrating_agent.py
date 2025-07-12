"""
Orchestrating Agent Service
Makes intelligent decisions about when to ask for clarification vs. when to infer parameters.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..llm.client import JarvusAIClient
from .parameter_inference_service import parameter_inference_service
from .memory_service import memory_service

logger = logging.getLogger(__name__)


class OrchestratingAgent:
    """Agent that orchestrates tool calls and decides when to ask for clarification"""
    
    def __init__(self):
        self.llm_client = JarvusAIClient()
        
        # Confidence thresholds for different types of parameters
        self.confidence_thresholds = {
            "critical": 0.9,    # High confidence needed for critical parameters
            "important": 0.7,   # Medium confidence for important parameters
            "optional": 0.5     # Lower confidence for optional parameters
        }
        
        # Parameter importance levels
        self.parameter_importance = {
            "create_calendar_event": {
                "summary": "critical",
                "start_time": "critical", 
                "end_time": "critical",
                "attendees": "important",
                "location": "optional",
                "description": "optional",
                "duration": "important",
                "timezone": "important",
                "reminder": "optional"
            },
            "send_email": {
                "to": "critical",
                "subject": "critical",
                "body": "critical",
                "cc": "optional",
                "bcc": "optional",
                "priority": "optional",
                "signature": "optional"
            },
            "create_document": {
                "title": "important",
                "content": "critical",
                "folder": "optional",
                "template": "optional"
            }
        }
    
    def should_ask_for_clarification(
        self,
        user_id: int,
        tool_name: str,
        missing_params: List[str],
        user_message: str,
        conversation_context: List[Dict[str, str]] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Decide whether to ask for clarification or infer parameters.
        
        Args:
            user_id: User ID
            tool_name: Name of the tool being called
            missing_params: List of missing parameter names
            user_message: Current user message
            conversation_context: Recent conversation context
            
        Returns:
            Tuple of (should_ask, params_to_ask_for, inferred_params)
        """
        try:
            if not missing_params:
                return False, [], {}
            
            # Get parameter importance levels for this tool
            importance_levels = self.parameter_importance.get(tool_name, {})
            
            # Analyze each missing parameter
            params_to_ask_for = []
            inferred_params = {}
            
            for param_name in missing_params:
                importance = importance_levels.get(param_name, "optional")
                confidence_threshold = self.confidence_thresholds.get(importance, 0.5)
                
                # Try to infer the parameter
                inferred_value, confidence = self._infer_parameter_with_confidence(
                    user_id=user_id,
                    tool_name=tool_name,
                    param_name=param_name,
                    user_message=user_message,
                    conversation_context=conversation_context
                )
                
                if inferred_value is not None and confidence >= confidence_threshold:
                    # High confidence inference - use it
                    inferred_params[param_name] = inferred_value
                    logger.info(f"High confidence inference for {param_name}: {inferred_value} (confidence: {confidence})")
                else:
                    # Low confidence or no inference - ask for clarification
                    params_to_ask_for.append(param_name)
                    logger.info(f"Low confidence for {param_name} (confidence: {confidence}), will ask for clarification")
            
            should_ask = len(params_to_ask_for) > 0
            
            return should_ask, params_to_ask_for, inferred_params
            
        except Exception as e:
            logger.error(f"Error in should_ask_for_clarification: {str(e)}")
            # Default to asking for clarification on error
            return True, missing_params, {}
    
    def _infer_parameter_with_confidence(
        self,
        user_id: int,
        tool_name: str,
        param_name: str,
        user_message: str,
        conversation_context: List[Dict[str, str]] = None
    ) -> Tuple[Any, float]:
        """
        Infer a parameter value and return confidence score.
        
        Returns:
            Tuple of (inferred_value, confidence_score)
        """
        try:
            # Strategy 1: Check semantic memory (highest confidence)
            memory_value = self._get_parameter_from_memory(user_id, param_name)
            if memory_value is not None:
                return memory_value, 0.95  # High confidence for stored preferences
            
            # Strategy 2: Use LLM to infer from context
            if conversation_context:
                llm_value, confidence = self._infer_from_context_with_llm(
                    tool_name, param_name, user_message, conversation_context
                )
                if llm_value is not None:
                    return llm_value, confidence
            
            # Strategy 3: Use default values (low confidence)
            default_value = self._get_default_value(tool_name, param_name)
            if default_value is not None:
                return default_value, 0.3  # Low confidence for defaults
            
            return None, 0.0
            
        except Exception as e:
            logger.error(f"Error inferring parameter with confidence: {str(e)}")
            return None, 0.0
    
    def _get_parameter_from_memory(self, user_id: int, param_name: str) -> Any:
        """Get parameter value from user's semantic memory."""
        try:
            memories = memory_service.search_memories(
                user_id=user_id,
                namespace='semantic',
                query=param_name,
                limit=5
            )
            
            for memory in memories:
                memory_data = memory.memory_data.get('data', {})
                if param_name in memory_data:
                    return memory_data[param_name]
                
                # Also check preference_type field
                if memory_data.get('preference_type') == param_name:
                    return memory_data.get('value')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting parameter from memory: {str(e)}")
            return None
    
    def _infer_from_context_with_llm(
        self,
        tool_name: str,
        param_name: str,
        user_message: str,
        conversation_context: List[Dict[str, str]]
    ) -> Tuple[Any, float]:
        """Use LLM to infer parameter value from context with confidence scoring."""
        try:
            # Build context for the LLM
            context_text = ""
            if conversation_context:
                recent_context = conversation_context[-4:] if len(conversation_context) > 4 else conversation_context
                for msg in recent_context:
                    if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                        context_text += f"{msg['role']}: {msg['content']}\n"
            
            prompt = f"""
You are helping to infer a parameter value for a tool call. 

Tool: {tool_name}
Parameter: {param_name}

Recent conversation context:
{context_text}

Current user message: {user_message}

Based on the conversation context and user message, what would be the most appropriate value for the {param_name} parameter?

Respond with ONLY the value, no explanation. If you cannot determine a value, respond with "UNKNOWN".

After the value, on a new line, provide a confidence score from 0.0 to 1.0, where:
- 0.0 = No confidence, completely guessing
- 0.5 = Some confidence, reasonable inference
- 1.0 = High confidence, very clear from context

Example response:
meeting room A
0.8
"""
            
            response = self.llm_client.create_chat_completion([
                {"role": "system", "content": "You are a parameter inference expert. Respond with the value and confidence score."},
                {"role": "user", "content": prompt}
            ])
            
            content = response['choices'][0]['message']['content'].strip()
            lines = content.split('\n')
            
            if not lines or lines[0].upper() == "UNKNOWN":
                return None, 0.0
            
            value = lines[0].strip()
            confidence = 0.5  # Default confidence
            
            if len(lines) > 1:
                try:
                    confidence = float(lines[1].strip())
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                except ValueError:
                    pass
            
            return value, confidence
            
        except Exception as e:
            logger.error(f"Error inferring from context with LLM: {str(e)}")
            return None, 0.0
    
    def _get_default_value(self, tool_name: str, param_name: str) -> Any:
        """Get default value for a parameter."""
        # This could be enhanced with a more comprehensive default value system
        defaults = {
            "create_calendar_event": {
                "duration": "60",
                "timezone": "UTC",
                "reminder": "15"
            },
            "send_email": {
                "priority": "normal",
                "signature": ""
            },
            "create_document": {
                "title": "Untitled Document",
                "folder": "root"
            }
        }
        
        return defaults.get(tool_name, {}).get(param_name)
    
    def generate_clarification_question(
        self,
        tool_name: str,
        params_to_ask_for: List[str],
        user_message: str,
        conversation_context: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a natural clarification question for missing parameters.
        
        Args:
            tool_name: Name of the tool being called
            params_to_ask_for: List of parameter names to ask for
            user_message: Current user message
            conversation_context: Recent conversation context
            
        Returns:
            Natural language clarification question
        """
        try:
            if not params_to_ask_for:
                return ""
            
            # Build context for the LLM
            context_text = ""
            if conversation_context:
                recent_context = conversation_context[-2:] if len(conversation_context) > 2 else conversation_context
                for msg in recent_context:
                    if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                        context_text += f"{msg['role']}: {msg['content']}\n"
            
            prompt = f"""
You are helping to ask for clarification from a user. 

Tool: {tool_name}
Missing parameters: {', '.join(params_to_ask_for)}

Recent conversation context:
{context_text}

Current user message: {user_message}

Generate a natural, conversational question to ask the user for the missing information. 
Make it sound natural and helpful, not robotic. Ask for all missing parameters in one question if possible.

Example: "I'd be happy to schedule that meeting for you. What time would you like it to start and end, and who should I invite?"

Respond with ONLY the question, no additional text.
"""
            
            response = self.llm_client.create_chat_completion([
                {"role": "system", "content": "You are a helpful assistant asking for clarification. Be natural and conversational."},
                {"role": "user", "content": prompt}
            ])
            
            question = response['choices'][0]['message']['content'].strip()
            return question
            
        except Exception as e:
            logger.error(f"Error generating clarification question: {str(e)}")
            # Fallback to simple question
            return f"I need a few more details to help you with that. Could you please provide: {', '.join(params_to_ask_for)}?"


# Global orchestrating agent instance
orchestrating_agent = OrchestratingAgent() 