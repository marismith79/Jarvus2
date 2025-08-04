"""
Workflow Service: Implements the Workflow Execution Agent Specification

This module provides a clear separation between the Orchestrator (planning, monitoring, coordination)
and the Executor (step execution, result handling) for workflow execution, as described in the provided spec.

- Integrates with agent_service.py for tool execution, orchestration, and memory retrieval.
- Follows the data models and control flow outlined in the spec.
- Extensively commented for clarity and review.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from .agent_service import AgentService

logger = logging.getLogger(__name__)

# --- Data Models ---

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
class WorkflowDefinition:
    """
    Represents a user-provided workflow definition.
    """
    def __init__(self, definition: Dict[str, Any]):
        self.id = definition.get('id')
        self.metadata = definition.get('metadata', {})
        self.parameters = definition.get('parameters', {})
        self.steps = definition.get('steps', [])

class ExecutionContext:
    """
    Context passed to each step execution, including previous results and parameters.
    """
    def __init__(self, workflow_id: str, step_id: str, context: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.context = context
    
    def get_context(self):
        return self.context

class StepResult:
    """
    Result of executing a workflow step.
    """
    def __init__(self, step_id: str, status: str, output: Dict[str, Any], feedback: Optional[str] = None):
        self.step_id = step_id
        self.status = status  # 'success' or 'failure'
        self.output = output
        self.feedback = feedback
        self.context = ExecutionContext()

    def to_dict(self):
        return {
            'step_id': self.step_id,
            'status': self.status,
            'output': self.output,
            'feedback': self.feedback,
            'provided_context': self.context.get_context()
        }

# --- Orchestrator ---

class Orchestrator:
    """
    Responsible for planning, monitoring, and coordinating execution of workflow steps.
    """
    MAX_RETRIES = 3

    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    def execute_workflow(self, workflow_def: WorkflowDefinition, user_id: str) -> Dict[str, Any]:
        """
        Returns a dict with the final output and step results.
        """
        logger.info(f"Starting workflow execution: {workflow_def.id}")
        context = dict(workflow_def.parameters)  # Initial context from workflow parameters
        step_results = []
        all_logs = []

        for step in workflow_def.steps:
            step_id = step.get('id')
            description = step.get('description')
            attempts = 0
            last_result = None
            logger.info(f"Executing step {step_id}: {description}")
            while attempts < self.MAX_RETRIES:
                # Prepare execution context for this step
                exec_context = ExecutionContext(
                    workflow_id=workflow_def.id,
                    step_id=step_id,
                    context=context.copy()  # Pass a copy of the current context
                )
                # Execute the step using the Executor
                result = Executor(self.agent_service).execute_step(step, exec_context, user_id)
                all_logs.append({
                    'step_id': step_id,
                    'attempt': attempts + 1,
                    'result': result.to_dict(),
                    'timestamp': datetime.utcnow().isoformat()
                })
                if self.validate_result(result):
                    logger.info(f"Step {step_id} succeeded on attempt {attempts+1}")
                    last_result = result
                    break
                else:
                    logger.warning(f"Step {step_id} failed on attempt {attempts+1}: {result.feedback}")
                    attempts += 1
                    # Optionally modify the step or context based on feedback
                    step = self.provide_feedback(step, result)
                    last_result = result
            if attempts == self.MAX_RETRIES and (not last_result or last_result.status != 'success'):
                logger.error(f"Step {step_id} failed after {self.MAX_RETRIES} attempts. Aborting workflow.")
                return {
                    'workflow_id': workflow_def.id,
                    'status': 'failed',
                    'failed_step': step_id,
                    'step_results': [r.to_dict() for r in step_results],
                    'logs': all_logs
                }
            # Update context with the output of the successful step
            context.update(last_result.output)
            step_results.append(last_result)
        logger.info(f"Workflow {workflow_def.id} completed successfully.")
        return {
            'workflow_id': workflow_def.id,
            'status': 'success',
            'step_results': [r.to_dict() for r in step_results],
            'final_context': context,
            'logs': all_logs
        }

    def validate_result(self, result: StepResult) -> bool:
        """
        Validates the result of a step. Can be extended with more complex logic.
        """
        return result.status == 'success'

    def provide_feedback(self, step: Dict[str, Any], result: StepResult) -> Dict[str, Any]:
        """
        Optionally modify the step or its parameters based on failure feedback.
        For now, just logs and returns the step unchanged.
        """
        # In a real system, this could use LLMs or heuristics to adjust the step
        logger.info(f"Feedback for step {step.get('id')}: {result.feedback}")
        return step

# --- Executor ---

class Executor:
    """
    Responsible for carrying out individual steps in the workflow.
    Maps step descriptions to tool calls via agent_service.
    """
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    def execute_step(self, step: Dict[str, Any], exec_context: ExecutionContext, user_id: str) -> StepResult:
        """
        Executes a single workflow step using the agent_service.
        Returns a StepResult.
        """
        step_id = step.get('id')
        description = step.get('description')
        try:
            # Here, we assume agent_service has a method to map step descriptions to tool calls.
            # This could be a planning LLM, a registry, or a hardcoded mapping.
            # For now, we use a generic 'execute_tool_step' method (to be implemented in agent_service.py).
            output = self.agent_service.execute_tool_step(
                step_description=description,
                context=exec_context.context,
                user_id=user_id
            )
            return StepResult(step_id=step_id, status='success', output=output)
        except Exception as e:
            logger.error(f"Error executing step {step_id}: {str(e)}", exc_info=True)
            return StepResult(step_id=step_id, status='failure', output={}, feedback=str(e))

# --- Usage Example (for reference/testing) ---

if __name__ == "__main__":
    # Example workflow definition (from spec)
    workflow_json = {
        "id": "workflow_123",
        "metadata": {
            "integrations": ["scraping_ant", "google_sheets"],
            "goal": "Scrape YC companies and compile contacts"
        },
        "parameters": {
            "batches": ["F24","W24","S24","X25","S25"],
            "max_batches": 4
        },
        "steps": [
            {"id": "step1", "description": "Identify most recent batches"},
            {"id": "step2", "description": "Collect company info via scraping_ant"},
            {"id": "step3", "description": "Create and format spreadsheet"},
            {"id": "step4", "description": "Populate spreadsheet with data"},
            {"id": "step5", "description": "Notify user of completion"}
        ]
    }
    workflow_def = WorkflowDefinition(workflow_json)
    agent_service = AgentService()  # Should be properly initialized in real usage
    orchestrator = Orchestrator(agent_service)
    # Simulate a user_id
    user_id = "user_abc"
    result = orchestrator.execute_workflow(workflow_def, user_id)
    print(result) 