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
                agent = self.agent_service.get_agent(agent_id, int(user_id))
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
            user_id=int(user_id),
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
        """Execute the workflow steps using the agent"""
        workflow = execution.workflow
        results = []
        
        # Create the workflow execution prompt
        workflow_prompt = self._create_workflow_prompt(workflow)
        
        # Add initial progress step
        execution.add_progress_step(
            step_number=1,
            action="workflow_started",
            input_data=f"Starting workflow: {workflow.name}",
            output_data=f"Goal: {workflow.goal}",
            status="success"
        )
        
        # Execute the workflow as a single task
        try:
            # Add progress step for agent processing
            execution.add_progress_step(
                step_number=2,
                action="agent_processing",
                input_data=workflow_prompt,
                output_data="Processing workflow instructions...",
                status="success"
            )
            
            # Use the agent service to process the workflow
            final_response, memory_info = self.agent_service.process_message(
                agent_id=agent.id,
                user_id=int(execution.user_id),
                user_message=workflow_prompt,
                thread_id=thread_id,
                tool_choice="auto",
                web_search_enabled=True,
                current_task=None,
                logger=logger
            )
            
            # Add progress step for completion
            execution.add_progress_step(
                step_number=3,
                action="workflow_completed",
                input_data="Final processing",
                output_data=final_response,
                status="success"
            )
            
            # Record the result
            step_result = {
                'step': 1,
                'action': 'workflow_execution',
                'input': workflow_prompt,
                'output': final_response,
                'timestamp': datetime.utcnow().isoformat(),
                'memory_info': memory_info
            }
            results.append(step_result)
            
            # Update execution progress
            execution.current_step = 3
            execution.total_steps = 3
            
        except Exception as e:
            logger.error(f"Error executing workflow step: {str(e)}")
            
            # Add error progress step
            execution.add_progress_step(
                step_number=execution.current_step + 1,
                action="workflow_error",
                input_data="Error occurred during execution",
                output_data=str(e),
                status="error"
            )
            
            execution.errors.append(f"Step execution failed: {str(e)}")
            raise
        
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