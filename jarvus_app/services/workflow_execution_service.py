"""
Workflow Execution Service
Executes user-defined workflows using the existing agent infrastructure.
"""

import uuid
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from flask_login import current_user
from flask import abort

from ..db import db
from ..models.workflow import Workflow
from ..models.history import History
from ..models.memory import ShortTermMemory
from .agent_service import AgentService
from .memory_service import memory_service
from ..llm.client import JarvusAIClient

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowExecution:
    """Represents a workflow execution instance"""
    
    def __init__(self, workflow: Workflow, user_id: str, execution_id: str = None):
        self.workflow = workflow
        self.user_id = user_id
        self.execution_id = execution_id or str(uuid.uuid4())
        self.status = WorkflowStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.results = []
        self.errors = []
        self.current_step = 0
        self.total_steps = 0
        self.progress_steps = []  # Detailed step-by-step progress
        self.user_feedback = None  # User feedback for completed executions
        self.feedback_status = None  # 'accepted', 'rejected', 'pending'
        self.feedback_timestamp = None
        
    def add_progress_step(self, step_number: int, action: str, input_data: str, output_data: str, status: str = 'success'):
        """Add a detailed progress step"""
        step = {
            'step_number': step_number,
            'action': action,
            'input': input_data,
            'output': output_data,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.progress_steps.append(step)
        
    def add_user_feedback(self, feedback: str, status: str):
        """Add user feedback for the execution"""
        self.user_feedback = feedback
        self.feedback_status = status
        self.feedback_timestamp = datetime.utcnow().isoformat()
        
    def to_dict(self):
        """Convert execution to dictionary"""
        return {
            'execution_id': self.execution_id,
            'workflow_id': self.workflow.id,
            'workflow_name': self.workflow.name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'results': self.results,
            'errors': self.errors,
            'progress_steps': self.progress_steps,
            'user_feedback': self.user_feedback,
            'feedback_status': self.feedback_status,
            'feedback_timestamp': self.feedback_timestamp
        }


class WorkflowExecutionService:
    """Service for executing user-defined workflows"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.llm_client = JarvusAIClient()
        self.active_executions: Dict[str, WorkflowExecution] = {}
    
    def execute_workflow(
        self, 
        workflow_id: int, 
        user_id: str, 
        agent_id: Optional[int] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow using the agent infrastructure
        
        Args:
            workflow_id: ID of the workflow to execute
            user_id: ID of the user executing the workflow
            agent_id: Optional agent ID to use for execution (creates temporary agent if not provided)
            thread_id: Optional thread ID for memory context
            
        Returns:
            Dictionary with execution details
        """
        try:
            # Get the workflow
            workflow = Workflow.get_workflow_by_id(workflow_id, user_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found for user {user_id}")
            
            # Create execution instance
            execution = WorkflowExecution(workflow, user_id)
            self.active_executions[execution.execution_id] = execution
            
            # Start execution
            execution.status = WorkflowStatus.RUNNING
            execution.start_time = datetime.utcnow()
            
            logger.info(f"Starting workflow execution {execution.execution_id} for workflow {workflow.name}")
            
            # Create or get agent for execution
            if agent_id:
                agent = self.agent_service.get_agent(agent_id, user_id)
            else:
                # Create a temporary agent for workflow execution
                agent = self._create_workflow_agent(workflow, user_id)
            
            # Execute the workflow
            results = self._execute_workflow_steps(execution, agent, thread_id)
            
            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.utcnow()
            execution.results = results
            
            logger.info(f"Workflow execution {execution.execution_id} completed successfully")
            
            return execution.to_dict()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            
            if execution:
                execution.status = WorkflowStatus.FAILED
                execution.end_time = datetime.utcnow()
                execution.errors.append(str(e))
            
            raise
    
    def _create_workflow_agent(self, workflow: Workflow, user_id: str) -> History:
        """Create a temporary agent for workflow execution"""
        agent_name = f"Workflow Agent - {workflow.name}"
        agent_description = f"Temporary agent for executing workflow: {workflow.name}"
        
        # Use the tools specified in the workflow, or default to web if none specified
        required_tools = workflow.required_tools or ['web']
        
        # Create agent with the specified tools for workflow execution
        agent = self.agent_service.create_agent(
            user_id=user_id,
            name=agent_name,
            tools=required_tools,
            description=agent_description
        )
        
        return agent
    
    def _execute_workflow_steps(
        self, 
        execution: WorkflowExecution, 
        agent: History, 
        thread_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Execute the workflow steps using the agent, step by step"""
        workflow = execution.workflow
        results = []
        
        # Decompose instructions into steps (use agent_service LLM planner or fallback)
        plan_steps = self.agent_service._plan_task_with_llm(
            workflow.instructions, workflow.required_tools or []
        )
        if not plan_steps:
            # Fallback: treat each instruction line as a step with tool 'auto'
            plan_steps = [
                {'tool': 'auto', 'parameters': {'instruction': line.strip()}}
                for line in workflow.instructions.split('\n') if line.strip()
            ]
        execution.total_steps = len(plan_steps)
        
        # Add initial progress step
        execution.add_progress_step(
            step_number=1,
            action="workflow_started",
            input_data=f"Starting workflow: {workflow.name}",
            output_data=f"Goal: {workflow.goal}",
            status="success"
        )
        
        # Step-by-step execution
        for idx, step in enumerate(plan_steps):
            step_num = idx + 1
            instruction = step['parameters'].get('instruction') if isinstance(step.get('parameters'), dict) else str(step.get('parameters'))
            step_prompt = f"Step {step_num}: {instruction}\nPlease execute this step."
            retries = 0
            max_retries = 3
            step_success = False
            last_response = None
            last_memory_info = None
            last_reflection = None
            while retries < max_retries and not step_success:
                try:
                    logger.info(f"[Workflow] Executing step {step_num}: {instruction} (Attempt {retries+1}/{max_retries})")
                    execution.add_progress_step(
                        step_number=step_num,
                        action=f"step_{step_num}_execution",
                        input_data=step_prompt,
                        output_data=f"Executing step {step_num}...",
                        status="running"
                    )
                    # Call the agent to execute this step
                    response, memory_info = self.agent_service.process_message(
                        agent_id=agent.id,
                        user_id=execution.user_id,
                        user_message=step_prompt,
                        thread_id=thread_id,
                        tool_choice="auto",
                        web_search_enabled=True,
                        current_task=None,
                        logger=logger
                    )
                    last_response = response
                    last_memory_info = memory_info
                    # LLM-based reflection/validation
                    reflection_prompt = (
                        "You are an expert workflow validator. "
                        "Given the following step instruction and the agent's response, "
                        "determine if the step was completed successfully. "
                        "If not, suggest what to do next (retry, adapt, escalate, or skip). "
                        "Respond in JSON: {\"success\": true/false, \"reason\": \"...\", \"retry\": true/false, \"suggestion\": \"...\"}\n"
                        f"Step Instruction: {instruction}\n"
                        f"Agent Response: {response}\n"
                    )
                    reflection_messages = [
                        {"role": "system", "content": reflection_prompt}
                    ]
                    try:
                        reflection_response = self.llm_client.create_chat_completion(reflection_messages, logger=logger)
                        import json as _json
                        content = reflection_response['choices'][0]['message']['content']
                        reflection = _json.loads(content)
                        last_reflection = reflection
                        logger.info(f"[Workflow] Step {step_num} reflection: {reflection}")
                        if reflection.get('success', False):
                            step_success = True
                            status = "success"
                        else:
                            status = "failed"
                            retries += 1
                            if not reflection.get('retry', False):
                                logger.info(f"[Workflow] Step {step_num} reflection suggests not to retry. Breaking.")
                                break
                    except Exception as e:
                        logger.warning(f"[Workflow] Step {step_num} LLM reflection failed: {str(e)}. Defaulting to simple validation.")
                        # Fallback: simple validation
                        if response and isinstance(response, str) and response.strip():
                            step_success = True
                            status = "success"
                        else:
                            status = "failed"
                            retries += 1
                except Exception as e:
                    status = "error"
                    last_response = str(e)
                    last_reflection = {'success': False, 'reason': str(e), 'retry': False, 'suggestion': ''}
                    logger.error(f"[Workflow] Step {step_num} execution error: {str(e)}")
                    retries += 1
                if not step_success and retries >= max_retries:
                    logger.error(f"[Workflow] Step {step_num} failed after {max_retries} retries: {last_response}")
                    execution.add_progress_step(
                        step_number=step_num,
                        action=f"step_{step_num}_retry_failed",
                        input_data=step_prompt,
                        output_data=f"Step failed after {max_retries} retries: {last_response}",
                        status="error"
                    )
            # Log result for this step
            step_result = {
                'step': step_num,
                'action': f'step_{step_num}_execution',
                'input': step_prompt,
                'output': last_response,
                'timestamp': datetime.utcnow().isoformat(),
                'memory_info': last_memory_info,
                'status': status,
                'reflection': last_reflection
            }
            results.append(step_result)
            execution.current_step = step_num
        # Add final progress step
        execution.add_progress_step(
            step_number=execution.total_steps + 1,
            action="workflow_completed",
            input_data="Final processing",
            output_data="Workflow execution complete.",
            status="success"
        )
        return results
    
    def _create_workflow_prompt(self, workflow: Workflow) -> str:
        """Create a comprehensive prompt for workflow execution"""
        prompt_parts = [
            f"# Workflow Execution: {workflow.name}",
            "",
            f"## Goal",
            workflow.goal,
            "",
            f"## Instructions",
            workflow.instructions,
            ""
        ]
        
        if workflow.notes:
            prompt_parts.extend([
                f"## Notes",
                workflow.notes,
                ""
            ])
        
        prompt_parts.extend([
            "## Execution Guidelines",
            "1. Follow the instructions step by step exactly as written",
            "2. Use the available tools to accomplish each step",
            "3. Provide clear progress updates as you work",
            "4. If you encounter any issues, explain what happened and try alternative approaches",
            "5. When the workflow is complete, provide a summary of what was accomplished",
            "6. If any steps cannot be completed, explain why and what alternatives were attempted",
            "",
            "Begin executing the workflow now:"
        ])
        
        return "\n".join(prompt_parts)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution"""
        execution = self.active_executions.get(execution_id)
        if execution:
            return execution.to_dict()
        return None
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.utcnow()
            logger.info(f"Workflow execution {execution_id} cancelled")
            return True
        return False
    
    def get_user_executions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all executions for a user"""
        user_executions = [
            execution.to_dict() 
            for execution in self.active_executions.values() 
            if execution.user_id == user_id
        ]
        return user_executions
    
    def cleanup_completed_executions(self, max_age_hours: int = 24):
        """Clean up old completed executions from memory"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        executions_to_remove = []
        for execution_id, execution in self.active_executions.items():
            if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                execution.end_time and execution.end_time.timestamp() < cutoff_time):
                executions_to_remove.append(execution_id)
        
        for execution_id in executions_to_remove:
            del self.active_executions[execution_id]
        
        if executions_to_remove:
            logger.info(f"Cleaned up {len(executions_to_remove)} old workflow executions")
    
    def add_feedback(self, execution_id: str, feedback: str, status: str) -> bool:
        """Add user feedback to an execution"""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                return False
            
            execution.add_user_feedback(feedback, status)
            return True
            
        except Exception as e:
            logger.error(f"Error adding feedback to execution {execution_id}: {str(e)}")
            return False


# Global instance
workflow_execution_service = WorkflowExecutionService() 