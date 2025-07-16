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
import os
import re

from flask_login import current_user
from flask import abort

from ..db import db
from ..models.workflow import Workflow
from ..models.history import History
from ..models.memory import ShortTermMemory
from .agent_service import AgentService
from .memory_service import memory_service
from ..llm.client import JarvusAIClient
from jarvus_app.config import Config

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
        self.awaiting_feedback = None  # Track if waiting for user feedback
        self.user_feedback_responses = {}  # Map step_number to user_response
        self.working_memory = {'summaries':[], 'vars':{}, 'suggestions':{}}  # Persistent working memory for facts/results
        self.plan = []  # Store the workflow plan steps
        
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
            'feedback_timestamp': self.feedback_timestamp,
            'working_memory': self.working_memory,
            'plan': self.plan,
        }


class WorkflowExecutionService:
    """Service for executing user-defined workflows"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.llm_client = JarvusAIClient()
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'workflow_logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def execute_workflow(
        self, 
        workflow_id: int, 
        user_id: str, 
        agent_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        procedural_memory_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow using the agent infrastructure
        
        Args:
            workflow_id: ID of the workflow to execute
            user_id: ID of the user executing the workflow
            agent_id: Optional agent ID to use for execution (creates temporary agent if not provided)
            thread_id: Optional thread ID for memory context
            procedural_memory_id: Optional override for which procedural memory to use/update
        
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
                # Use the most recently created agent for the user, or create one if none exist
                from jarvus_app.models.history import History
                agent = History.query.filter_by(user_id=user_id).order_by(History.created_at.desc()).first()
                if not agent:
                    # Fallback: create a temporary agent for workflow execution
                    agent = self._create_workflow_agent(workflow, user_id)
            
            # Execute the workflow, passing the procedural_memory_id (override or workflow default)
            results = self._execute_workflow_steps(
                execution, agent, thread_id,
                procedural_memory_id=procedural_memory_id or getattr(workflow, 'procedural_memory_id', None)
            )
            
            # Mark as completed
            if execution.status == WorkflowStatus.PENDING and execution.awaiting_feedback:
                logger.info(f"Workflow execution {execution.execution_id} paused, awaiting user feedback at step {execution.current_step}")
            else:
                execution.status = WorkflowStatus.COMPLETED
                execution.end_time = datetime.utcnow()
                execution.results = results
                logger.info(f"Workflow execution {execution.execution_id} completed successfully")
            self._log_execution_to_file(execution)
            return execution.to_dict()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            
            if execution:
                execution.status = WorkflowStatus.FAILED
                execution.end_time = datetime.utcnow()
                execution.errors.append(str(e))
                self._log_execution_to_file(execution)
            
            raise
    
    def _create_workflow_agent(self, workflow: Workflow, user_id: str) -> History:
        """Create a temporary agent for workflow execution"""
        agent_name = f"Workflow Agent - {workflow.name}"
        agent_description = f"Temporary agent for executing workflow: {workflow.name}"
        
        # Use the tools specified in the workflow, or default to scrapingant if none specified
        required_tools = workflow.required_tools or ['scrapingant']
        # Always include 'user_feedback' if not present
        if 'user_feedback' not in required_tools:
            required_tools = required_tools + ['user_feedback']
        
        # Create agent with the specified tools for workflow execution
        agent = self.agent_service.create_agent(
            user_id=user_id,
            name=agent_name,
            tools=required_tools,
            description=agent_description
        )
        
        return agent
    
    def resume_after_feedback(self, execution_id: str, user_id: str, feedback: str) -> Dict[str, Any]:
        execution = self.active_executions.get(execution_id)
        if not execution or execution.user_id != user_id:
            raise ValueError("Invalid execution or permission denied")
        # Store feedback
        execution.add_user_feedback(feedback, status='received')
        # Store user_response for the paused step
        if execution.awaiting_feedback:
            step_number = execution.awaiting_feedback['step_number']
            execution.user_feedback_responses[step_number] = feedback
        paused_info = execution.awaiting_feedback
        # Resume execution from the paused step
        agent = self.agent_service.get_agent(execution.workflow.agent_id, user_id) if hasattr(execution.workflow, 'agent_id') else None
        thread_id = None  # If you have thread_id tracking, set it here
        results = self._execute_workflow_steps(
            execution, agent, thread_id,
            procedural_memory_id=None,  # or as before
            start_step=execution.current_step - 1  # Resume from the paused step
        )
        execution.status = WorkflowStatus.RUNNING if results else WorkflowStatus.COMPLETED
        return execution.to_dict()

    def _execute_workflow_steps(
        self, 
        execution: WorkflowExecution, 
        agent: History, 
        thread_id: Optional[str],
        procedural_memory_id: Optional[int] = None,
        start_step: int = 0  # New parameter for resuming
    ) -> List[Dict[str, Any]]:
        """Execute the workflow steps using the agent, step by step, with procedural memory integration"""
        from jarvus_app.models.memory import LongTermMemory
        workflow = execution.workflow
        results = []
        procedural_memory_content = None
        procedural_memory_obj = None
        # Load procedural memory if linked or overridden
        pmem_id = procedural_memory_id or getattr(workflow, 'procedural_memory_id', None)
        if pmem_id:
            procedural_memory_obj = LongTermMemory.query.filter_by(id=pmem_id).first()
            if procedural_memory_obj:
                procedural_memory_content = procedural_memory_obj.memory_data.get('content') if isinstance(procedural_memory_obj.memory_data, dict) else str(procedural_memory_obj.memory_data)
        # Construct memory context for planning
        memory_context_sections = memory_service.get_context_for_conversation(
            user_id=execution.user_id,
            thread_id=thread_id,
            current_message=workflow.instructions,
            as_sections=True
        )
        memory_context_parts = []
        if memory_context_sections.get('episodic'):
            memory_context_parts.append('Episodic Memory:\n' + '\n'.join(memory_context_sections['episodic'][:3]))
        if memory_context_sections.get('semantic'):
            memory_context_parts.append('Semantic Memory:\n' + '\n'.join(memory_context_sections['semantic'][:3]))
        if procedural_memory_content:
            memory_context_parts.append('Procedural Memory:\n' + '\n'.join(procedural_memory_content))
        else:
            if memory_context_sections.get('procedural'):
                memory_context_parts.append('Procedural Memory:\n' + '\n'.join(memory_context_sections['procedural'][:3]))
        memory_context = '\n\n'.join(memory_context_parts)
        # Decompose instructions into steps (use agent_service LLM planner or fallback)
        logger.info(f"Workflow.instructions: {workflow.instructions}")
        logger.info(f"Workflow.required_tools: {workflow.required_tools}")
        # Always include 'user_feedback' in allowed tools for planning/execution
        allowed_tools = list(workflow.required_tools) if workflow.required_tools else ['scrapingant']
        if 'user_feedback' not in allowed_tools:
            allowed_tools.append('user_feedback')
        plan_steps = self.agent_service.planner_agent(
            workflow.instructions, allowed_tools, memory_context=memory_context
        )
        execution.plan = plan_steps  # Store the plan in the execution object
        logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%Plan returned by planner agent:%%%%%%%%%%%%%%%%%%%%%%%%%  {plan_steps}")
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
        idx = start_step
        while idx < len(plan_steps):
            step = plan_steps[idx]
            step_num = idx + 1
            tool = step.get('tool')
            instruction = step.get('instruction') or (step['parameters'].get('instruction') if isinstance(step.get('parameters'), dict) else str(step.get('parameters')))
            # replan_on_feedback = step.get('replan', False)
            step_success = False
            status = None
            last_response = None
            last_memory_info = None
            last_reflection = None
            retries = 0
            max_retries = 3

            # === Data Dependency Injection ===
            # vars = execution.working_memory.setdefault('vars', {})
            # def substitute_vars(text):
            #     if not isinstance(text, str):
            #         return text
            #     def repl(match):
            #         key = match.group(1)
            #         return str(vars.get(key, f'{{{key}}}'))
            #     return re.sub(r'\{(\w+)\}', repl, text)

            # # Substitute in instruction
            # instruction = substitute_vars(instruction)
            # # Substitute in tool parameters if present
            # if 'parameters' in step and isinstance(step['parameters'], dict):
            #     for k, v in step['parameters'].items():
            #         if isinstance(v, str):
            #             step['parameters'][k] = substitute_vars(v)

            # Check for required inputs
            required_inputs = step.get('inputs', [])
            for var in required_inputs:
                if execution.working_memory['vars'][var]:
                    instruction += f"{var}: {execution.working_memory['vars'][var]}"
            
            # Add Suggestions from validation agent if step is retrying
            step_suggestion = execution.working_memory['suggestions'].get(step_num, None)
            if step_suggestion:
                instruction += str(step_suggestion)
            # missing = [var for var in required_inputs if var not in vars]
            # if missing:
            #     execution.current_step = step_num
            #     execution.status = WorkflowStatus.PENDING
            #     execution.awaiting_feedback = {
            #         'step_number': step_num,
            #         'question': f"Please provide the following required information: {', '.join(missing)}"
            #     }
            #     logger.info(f"[Workflow] Pausing for missing required inputs at step {step_num}: {missing}")
            #     self._log_execution_to_file(execution)
            #     return [{
            #         'step': step_num,
            #         'action': 'user_feedback',
            #         'input': instruction,
            #         'output': f"Please provide the following required information: {', '.join(missing)}",
            #         'status': 'pending',
            #         'timestamp': datetime.utcnow().isoformat()
            #     }]

            # === Build context messages with previous step summaries, working memory, and variables ===
            now_iso = datetime.now().isoformat()
            system_prompt = Config.CHATBOT_SYSTEM_PROMPT.strip().replace("{CURRENT_DATETIME}", now_iso)
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            wm_summaries = execution.working_memory.get('summaries', [])
            if wm_summaries:
                messages.append({"role": "assistant", "content": "Summary of previous steps:\n" + '\n'.join(wm_summaries)})
            # if execution.working_memory:
            #     wm_facts = {k: v for k, v in execution.working_memory.items() if k not in ['summaries', 'vars']}
            #     if wm_facts:
            #         messages.append({"role": "assistant", "content": f"Known facts so far: {wm_facts}"})
            # if vars:
            #     messages.append({"role": "assistant", "content": f"Available variables: {vars}"})
            # user_response = execution.user_feedback_responses.pop(step_num, None)
            # --- LOGGING for user_feedback tool ---
            # if tool == 'user_feedback':
            #     logger.info(f"[Workflow] user_feedback tool detected at step {step_num}. user_response: {user_response}, instruction: {instruction}")
            #     # Always call the user_feedback_executor directly
            #     from jarvus_app.services.tool_registry import user_feedback_executor
            #     tool_args = {'question': instruction}
            #     if user_response is not None:
            #         tool_args['user_response'] = user_response
            #     feedback_result = user_feedback_executor(**tool_args)
            #     last_response = feedback_result
            #     if feedback_result.get('action') == 'user_feedback' and user_response is None:
            #         # Pause for user input, show feedback_result['question']
            #         execution.current_step = step_num
            #         execution.status = WorkflowStatus.PENDING
            #         execution.awaiting_feedback = {
            #             'step_number': step_num,
            #             'question': feedback_result['question']
            #         }
            #         logger.info(f"[Workflow] Pausing for user feedback at step {step_num}: {feedback_result['question']}")
            #         self._log_execution_to_file(execution)
            #         logger.info(f"[Workflow] Workflow execution {execution.execution_id} paused, awaiting user feedback at step {step_num}")
            #         return [{
            #             'step': step_num,
            #             'action': 'user_feedback',
            #             'input': instruction,
            #             'output': feedback_result['question'],
            #             'status': 'pending',
            #             'timestamp': datetime.utcnow().isoformat()
            #         }]
            #     # If user_response is present, treat as success and continue
            #     if user_response is not None:
            #         execution.awaiting_feedback = None
            #         step_success = True
            #         status = 'success'
            #         break
            messages.append({"role": "user", "content": instruction})
            tool_choice = 'auto' if tool else 'none'
            while retries < max_retries and not step_success:
                try:
                    logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%[Workflow] Executing step {step_num}: {instruction} (Attempt {retries+1}/{max_retries})%%%%%%%%%%%%%%%%%%%%%%%%%")
                    execution.add_progress_step(
                        step_number=step_num,
                        action=f"step_{step_num}_execution",
                        input_data=instruction,
                        output_data=f"Executing step {step_num}...",
                        status="running"
                    )
                    # ===Prompt Agent===
                    logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%[Workflow] Input: %%%%%%%%%%%%%%%%%%%%%%%%% {messages} ") 
                    _, step_result = self.agent_service.execution_agent(
                        user_id=execution.user_id,
                        allowed_tools=[tool] if tool else None,
                        messages=messages,
                        tool_choice=tool_choice,
                        logger=logger
                    )
                    
                    logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%[Workflow] Output: %%%%%%%%%%%%%%%%%%%%%%%%%") #{step_result} ")

                    # # Handle user_feedback: if the result is a dict with action 'user_feedback', pause and prompt user
                    # if isinstance(step_result, dict) and step_result.get('action') == 'user_feedback' and user_response is None:
                    #     execution.current_step = step_num
                    #     execution.status = WorkflowStatus.PENDING
                    #     execution.awaiting_feedback = {
                    #         'step_number': step_num,
                    #         'question': instruction
                    #     }
                    #     self._log_execution_to_file(execution)
                    #     return [{
                    #         'step': step_num,
                    #         'action': 'user_feedback',
                    #         'input': instruction,
                    #         'output': instruction,
                    #         'status': 'pending',
                    #         'timestamp': datetime.utcnow().isoformat()
                    #     }]
                    # if tool == 'user_feedback' and user_response is not None:
                    #     execution.awaiting_feedback = None
                    last_response = step_result
                    # # For user_feedback, treat as success after user response
                    # if tool == 'user_feedback':
                    #     step_success = True
                    #     status = 'success'
                    #     break
                    # ===LLM-based reflection/validation: check if success criteria was met===
                    if tool != 'user_feedback':
                        # Use agent_service.validation_agent for validation/reflection
                        logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%[Workflow] Prompting Step {step_num} reflection %%%%%%%%%%%%%%%%%%%%%%%%%")
                        reflection = self.agent_service.validation_agent(
                            instruction=instruction,
                            success_criteria=step.get('success_criteria', ''),
                            agent_response=last_response,
                            error_handling=step.get('error_handling', ''),
                            extract=step.get('extract', []),
                            logger=logger
                        )
                        last_reflection = reflection
                        logger.info(f"%%%%%%%%%%%%%%%%%%%%%%%%%[Workflow] Step {step_num} reflection: %%%%%%%%%%%%%%%%%%%%%%%%% \n {reflection}")
                        # Always append summary, regardless of success
                        summary = reflection.get('summary')
                        if summary:
                            summary_str = summary.strip()
                            execution.working_memory['summaries'].append(summary_str)
                        if reflection.get('success', False):
                            step_success = True
                            status = "success"
                        else:
                            status = "failed"
                            retries += 1
                            suggestion = reflection.get('suggestion')
                            if suggestion:
                                execution.working_memory['suggestions'][step_num] = suggestion
                            if not reflection.get('retry', False):
                                logger.info(f"[Workflow] Step {step_num} reflection suggests not to retry. Breaking.")
                                break
                        extracted = reflection.get('extracted')
                        if extracted:
                            for key, value in extracted.items():
                                if 'vars' not in execution.working_memory:
                                    execution.working_memory['vars'] = {}
                                execution.working_memory['vars'][key] = value
                            
                    # Always trigger replanning after two failed attempts
                    if not step_success and retries >= 2:
                        logger.info(f"[Workflow] Step {step_num} failed after {retries} attempts. Triggering replanning for remaining steps.")
                        # Compose a more informative replanning prompt
                        original_instructions = workflow.instructions
                        # Get the remaining steps from the original plan
                        remaining_plan = execution.plan[idx+1:] if hasattr(execution, 'plan') and execution.plan else []
                        remaining_plan_text = '\n'.join([
                            f"Step {i+idx+2}: {step.get('instruction', str(step))}" for i, step in enumerate(remaining_plan)
                        ])
                        replanning_prompt = (
                            f"The workflow failed at step {step_num}: {instruction}. "
                            f"Here is the original workflow description:\n{original_instructions}\n"
                            f"Here are the summary of the steps executed from the original plan:\n{execution.working_memory['summaries']}\n"
                            f"Here are the remaining steps from the original plan:\n{remaining_plan_text}\n"
                            f"Please replan the remaining steps to achieve the overall goal, taking into account what has already been completed and what failed."
                        )
                        new_plan_steps = self.agent_service.planner_agent(
                            replanning_prompt,
                            workflow.required_tools or [],
                            memory_context=memory_context+"Working Memory Variables:"+str(execution.working_memory['vars'])
                        )
                        plan_steps = plan_steps[:idx+1] + new_plan_steps
                        execution.total_steps = len(plan_steps)
                        logger.info(f"[Workflow] Replanned steps: {new_plan_steps}")
                        break  # Exit retry loop and continue with new plan
                    if not step_success and retries >= max_retries:
                        logger.error(f"[Workflow] Step {step_num} failed after {max_retries} retries: {last_response}")
                        execution.add_progress_step(
                            step_number=step_num,
                            action=f"step_{step_num}_retry_failed",
                            input_data=instruction,
                            output_data=f"Step failed after {max_retries} retries: {last_response}",
                            status="error"
                        )
                except Exception as e:
                    status = "error"
                    last_response = str(e)
                    last_reflection = {'success': False, 'reason': str(e), 'retry': False, 'suggestion': ''}
                    logger.error(f"[Workflow] Step {step_num} execution error: {str(e)}")
                    retries += 1

            # Log result for this step
            step_result = {
                'step': step_num,
                'action': f'step_{step_num}_execution',
                'input': instruction,
                'output': last_response,
                'timestamp': datetime.utcnow().isoformat(),
                'memory_info': last_memory_info,
                'status': status,
                'reflection': last_reflection
            }
            results.append(step_result)
            execution.current_step = step_num
            idx += 1
            # Log after every step
            self._log_execution_to_file(execution)
        # Clear awaiting_feedback if workflow completes
        execution.awaiting_feedback = None
        # Add final progress step
        execution.add_progress_step(
            step_number=execution.total_steps + 1,
            action="workflow_completed",
            input_data="Final processing",
            output_data="Workflow execution complete.",
            status="success"
        )
        # After execution, update procedural memory if linked
        if procedural_memory_obj:
            try:
                # Summarize new learnings/reflection from this run
                all_reflections = [r['reflection'] for r in results if r.get('reflection')]
                # Include user feedback if available
                user_feedback = execution.user_feedback if hasattr(execution, 'user_feedback') else None
                if user_feedback:
                    all_reflections.append({'user_feedback': user_feedback})
                improved_content = self.agent_service.procedural_memory_update_agent(
                    previous_procedural_memory=procedural_memory_content,
                    new_reflections_feedback=all_reflections,
                    logger=logger
                )
                # Update the procedural memory entry
                if isinstance(procedural_memory_obj.memory_data, dict):
                    procedural_memory_obj.memory_data['content'] = improved_content
                else:
                    procedural_memory_obj.memory_data = {'content': improved_content}
                procedural_memory_obj.updated_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"[Workflow] Procedural memory updated for workflow {workflow.id}")
            except Exception as e:
                logger.error(f"[Workflow] Failed to update procedural memory: {str(e)}")
        return results
    
    # def _create_workflow_prompt(self, workflow: Workflow) -> str:
    #     """Create a comprehensive prompt for workflow execution"""
    #     prompt_parts = [
    #         f"# Workflow Execution: {workflow.name}",
    #         "",
    #         f"## Goal",
    #         workflow.goal,
    #         "",
    #         f"## Instructions",
    #         workflow.instructions,
    #         ""
    #     ]
        
    #     if workflow.notes:
    #         prompt_parts.extend([
    #             f"## Notes",
    #             workflow.notes,
    #             ""
    #         ])
        
    #     prompt_parts.extend([
    #         "## Execution Guidelines",
    #         "1. Follow the instructions step by step exactly as written",
    #         "2. Use the available tools to accomplish each step",
    #         "3. Provide clear progress updates as you work",
    #         "4. If you encounter any issues, explain what happened and try alternative approaches",
    #         "5. When the workflow is complete, provide a summary of what was accomplished",
    #         "6. If any steps cannot be completed, explain why and what alternatives were attempted",
    #         "",
    #         "Begin executing the workflow now:"
    #     ])
        
    #     return "\n".join(prompt_parts)
    
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
            self._log_execution_to_file(execution)
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
    
    def get_awaiting_feedback_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Return a list of workflows for the user that are awaiting user feedback."""
        awaiting = []
        for execution in self.active_executions.values():
            if execution.user_id == user_id and execution.awaiting_feedback:
                awaiting.append({
                    'execution_id': execution.execution_id,
                    'workflow_name': execution.workflow.name,
                    'step_number': execution.awaiting_feedback['step_number'],
                    'clarification_question': execution.awaiting_feedback['question'],
                    'timestamp': execution.progress_steps[-1]['timestamp'] if execution.progress_steps else None
                })
        return awaiting
    
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

    def _log_execution_to_file(self, execution: WorkflowExecution):
        """Write the workflow execution log to a JSON file in workflow_logs/"""
        log_data = execution.to_dict()
        log_data['step_summaries'] = getattr(execution, 'step_summaries', [])
        log_data['user_feedback_responses'] = getattr(execution, 'user_feedback_responses', {})
        log_data['awaiting_feedback'] = getattr(execution, 'awaiting_feedback', None)
        log_data['plan'] = getattr(execution, 'plan', [])
        # Convert any non-serializable objects in results and progress_steps
        def make_json_safe(obj):
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(i) for i in obj]
            elif hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif hasattr(obj, '__dict__'):
                # For objects like AssistantMessage, ToolMessage, etc.
                return {k: make_json_safe(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            else:
                try:
                    json.dumps(obj)
                    return obj
                except Exception:
                    return str(obj)
        log_data['results'] = make_json_safe(log_data.get('results', []))
        log_data['progress_steps'] = make_json_safe(log_data.get('progress_steps', []))
        log_file = os.path.join(self.log_dir, f"execution_{execution.execution_id}.json")
        try:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2, sort_keys=True)
        except Exception as e:
            logger.error(f"Failed to write workflow execution log to file: {e}")


# Global instance
workflow_execution_service = WorkflowExecutionService() 



    # def execute_workflow(self, workflow, user_id: str, logger=None):
    #     """
    #     Execute a workflow definition step-by-step using agentic orchestration.
    #     Args:
    #         workflow: Workflow model instance (with goal, instructions, required_tools, etc.)
    #         user_id: The user executing the workflow
    #         logger: Optional logger
    #     Returns:
    #         dict: Workflow execution result, including status, outputs, and logs
    #     """
    #     if logger is None:
    #         logger = logging.getLogger(__name__)
        
    #     # 1. Parse workflow definition
    #     goal = workflow.goal
    #     instructions = workflow.instructions
    #     notes = workflow.notes
    #     required_tools = workflow.required_tools or []
    #     trigger_type = workflow.trigger_type or 'manual'
    #     trigger_config = workflow.trigger_config or {}
        
    #     # 2. Decompose instructions into steps (use LLM or fallback to splitting by lines)
    #     # Get memory context for planning
    #     agent, allowed_tools, memory_info, messages, current_state = self._get_context_for_message(
    #         agent_id=workflow.agent_id if hasattr(workflow, 'agent_id') else None,
    #         user_id=user_id,
    #         user_message=instructions,
    #         thread_id=None,
    #         web_search_enabled=True,
    #         current_task=None
    #     )
    #     # Summarize memory context for planning
    #     memory_context_parts = []
    #     from jarvus_app.services.memory_service import memory_service
    #     memory_sections = memory_service.get_context_for_conversation(user_id=user_id, thread_id=None, as_sections=True)
    #     if memory_sections.get('episodic'):
    #         memory_context_parts.append('Episodic Memory:\n' + '\n'.join(memory_sections['episodic'][:3]))
    #     if memory_sections.get('semantic'):
    #         memory_context_parts.append('Semantic Memory:\n' + '\n'.join(memory_sections['semantic'][:3]))
    #     if memory_sections.get('procedural'):
    #         memory_context_parts.append('Procedural Memory:\n' + '\n'.join(memory_sections['procedural'][:3]))
    #     # Add recent working memory (last 3 messages)
    #     if current_state and 'messages' in current_state:
    #         recent_msgs = current_state['messages'][-3:]
    #         wm = '\n'.join([f"{m['role']}: {m['content']}" for m in recent_msgs if m.get('content')])
    #         if wm:
    #             memory_context_parts.append('Recent Working Memory:\n' + wm)
    #     memory_context = '\n\n'.join(memory_context_parts)
    #     plan_steps = self.planner_agent(instructions, required_tools, memory_context=memory_context)
    #     if not plan_steps:
    #         # Fallback: treat each instruction line as a step with tool 'auto'
    #         plan_steps = [
    #             {'tool': 'auto', 'parameters': {'instruction': line.strip()}}
    #             for line in instructions.split('\n') if line.strip()
    #         ]
        
    #     logger.info(f"[Workflow] Decomposed into {len(plan_steps)} steps.")
        
    #     # 3. Execute each step, track state, handle retries/reflection
    #     step_results = []
    #     workflow_state = {}
    #     for idx, step in enumerate(plan_steps):
    #         tool_name = step.get('tool', 'auto')
    #         parameters = step.get('parameters', {})
    #         retries = 0
    #         max_retries = 3
    #         step_success = False
    #         last_error = None
    #         while retries < max_retries and not step_success:
    #             try:
    #                 logger.info(f"[Workflow] Step {idx+1}/{len(plan_steps)}: Executing tool '{tool_name}' with parameters {parameters}")
    #                 # Use tool registry to execute the tool
    #                 # (If tool_name is 'auto', use LLM to select tool)
    #                 if tool_name == 'auto':
    #                     # Use LLM to select tool based on instruction
    #                     allowed_tools = required_tools
    #                     selected_tools = self._select_tools_with_llm(parameters.get('instruction', ''), allowed_tools)
    #                     tool_name = selected_tools[0] if selected_tools else None
    #                     if not tool_name:
    #                         raise Exception("No suitable tool found for step.")
    #                 # Get tool metadata
    #                 tool_meta = tool_registry.get_tool(tool_name)
    #                 if not tool_meta:
    #                     raise Exception(f"Tool '{tool_name}' not found in registry.")
    #                 # Execute tool
    #                 jwt_token = None  # Add JWT if needed for auth
    #                 result = tool_registry.execute_tool(tool_name, parameters, jwt_token)
    #                 step_results.append({
    #                     'step': idx+1,
    #                     'tool': tool_name,
    #                     'parameters': parameters,
    #                     'result': result,
    #                     'success': True
    #                 })
    #                 workflow_state[f'step_{idx+1}'] = result
    #                 step_success = True
    #             except Exception as e:
    #                 last_error = str(e)
    #                 logger.error(f"[Workflow] Step {idx+1} failed: {last_error}")
    #                 retries += 1
    #                 if retries >= max_retries:
    #                     step_results.append({
    #                         'step': idx+1,
    #                         'tool': tool_name,
    #                         'parameters': parameters,
    #                         'result': last_error,
    #                         'success': False
    #                     })
        
    #     # 4. Reflection: Optionally review results and retry failed steps (future extension)
    #     # (For now, just log failures)
    #     failed_steps = [r for r in step_results if not r['success']]
    #     if failed_steps:
    #         logger.warning(f"[Workflow] {len(failed_steps)} steps failed. See step_results for details.")
        
    #     # 5. Output results (e.g., return, write to sheet, send message)
    #     # (For now, just return the results)
    #     return {
    #         'workflow_id': workflow.id,
    #         'status': 'completed' if not failed_steps else 'partial_failure',
    #         'step_results': step_results,
    #         'final_state': workflow_state,
    #         'failed_steps': failed_steps
    #     }

    # def execute_comprehensive_workflow(self, workflow, user_id: str, logger=None, context_memory_id: str = None):
    #     """
    #     Execute a workflow using a comprehensive agentic architecture with full memory integration.
    #     Args:
    #         workflow: Workflow model instance
    #         user_id: The user executing the workflow
    #         logger: Optional logger
    #         context_memory_id: Optional hierarchical memory context
    #     Returns:
    #         dict: Comprehensive workflow execution report
    #     """
    #     import networkx as nx
    #     if logger is None:
    #         logger = logging.getLogger(__name__)
        
    #     # 1. Retrieve relevant long-term memories for context
    #     ltm_context = memory_service.get_context_for_conversation(
    #         user_id=user_id,
    #         current_message=workflow.goal + "\n" + workflow.instructions,
    #         as_sections=True
    #     )
    #     logger.info(f"[Memory] Retrieved LTM context for workflow: {ltm_context}")
        
    #     # 2. Optionally retrieve hierarchical/contextual memory
    #     hierarchical_context = None
    #     if context_memory_id:
    #         hierarchical_context = memory_service.get_context_influence(context_memory_id, user_id)
    #         logger.info(f"[Memory] Retrieved hierarchical context: {hierarchical_context}")
        
    #     # 3. Parse workflow into DAG of steps (LLM-driven)
    #     dag_steps = self._parse_workflow_to_dag(
    #         workflow.instructions,
    #         workflow.required_tools or [],
    #         ltm_context=ltm_context,
    #         hierarchical_context=hierarchical_context
    #     )
    #     if not dag_steps:
    #         dag_steps = [
    #             {'id': f'step_{i+1}', 'tool': 'auto', 'parameters': {'instruction': line.strip()}, 'deps': []}
    #             for i, line in enumerate(workflow.instructions.split('\n')) if line.strip()
    #         ]
        
    #     # Build DAG
    #     G = nx.DiGraph()
    #     for step in dag_steps:
    #         G.add_node(step['id'], **step)
    #         for dep in step.get('deps', []):
    #             G.add_edge(dep, step['id'])
        
    #     # 4. Initialize memory and logs
    #     workflow_memory = {}
    #     step_results = {}
    #     logs = []
    #     failed_steps = []
    #     thread_id = f"workflow_{workflow.id}_{user_id}_{int(datetime.utcnow().timestamp())}"
    #     agent_id = None  # Optionally associate with an agent
        
    #     # 5. Execute steps in topological order
    #     for step_id in nx.topological_sort(G):
    #         step = G.nodes[step_id]
    #         tool_name = step.get('tool', 'auto')
    #         parameters = step.get('parameters', {}).copy()
    #         # Inject outputs from dependencies if needed
    #         for dep in step.get('deps', []):
    #             dep_result = step_results.get(dep, {})
    #             parameters[f'dep_{dep}'] = dep_result
    #         retries = 0
    #         max_retries = 3
    #         step_success = False
    #         last_error = None
    #         while retries < max_retries and not step_success:
    #             try:
    #                 logs.append(f"[Workflow] Step {step_id}: Executing tool '{tool_name}' with parameters {parameters}")
    #                 if tool_name == 'auto':
    #                     allowed_tools = workflow.required_tools or []
    #                     selected_tools = self._select_tools_with_llm(parameters.get('instruction', ''), allowed_tools)
    #                     tool_name = selected_tools[0] if selected_tools else None
    #                     if not tool_name:
    #                         raise Exception("No suitable tool found for step.")
    #                 tool_meta = tool_registry.get_tool(tool_name)
    #                 if not tool_meta:
    #                     raise Exception(f"Tool '{tool_name}' not found in registry.")
    #                 jwt_token = None
    #                 result = tool_registry.execute_tool(tool_name, parameters, jwt_token)
    #                 # Reflection: Use LLM to review result
    #                 reflection = self._reflect_on_step(step, result, workflow_memory, logger, ltm_context=ltm_context)
    #                 logs.append(f"[Workflow] Step {step_id} reflection: {reflection}")
    #                 if reflection.get('retry'):
    #                     retries += 1
    #                     logs.append(f"[Workflow] Step {step_id} reflection requested retry ({retries}/{max_retries})")
    #                     continue
    #                 step_results[step_id] = result
    #                 workflow_memory[step_id] = result
    #                 step_success = True
    #                 # --- Short-term memory: checkpoint after each step ---
    #                 memory_service.save_checkpoint(
    #                     thread_id=thread_id,
    #                     user_id=user_id,
    #                     agent_id=agent_id or 0,
    #                     state_data={
    #                         'step_id': step_id,
    #                         'parameters': parameters,
    #                         'result': result,
    #                         'workflow_memory': workflow_memory.copy(),
    #                         'logs': logs.copy()
    #                     }
    #                 )
    #             except Exception as e:
    #                 last_error = str(e)
    #                 logs.append(f"[Workflow] Step {step_id} failed: {last_error}")
    #                 retries += 1
    #                 if retries >= max_retries:
    #                     failed_steps.append({
    #                         'step': step_id,
    #                         'tool': tool_name,
    #                         'parameters': parameters,
    #                         'result': last_error,
    #                         'success': False
    #                     })
        
    #     # 6. Final reflection (LLM-driven)
    #     final_reflection = self._final_reflection(
    #         workflow, step_results, workflow_memory, logs, logger, ltm_context=ltm_context
    #     )
    #     logs.append(f"[Workflow] Final reflection: {final_reflection}")
        
    #     # 7. Long-term memory: extract and store memories from workflow run
    #     try:
    #         # Compose conversation/messages for memory extraction
    #         conversation_messages = [
    #             {'role': 'system', 'content': workflow.goal},
    #             {'role': 'system', 'content': workflow.instructions}
    #         ]
    #         for step_id, result in step_results.items():
    #             conversation_messages.append({'role': 'assistant', 'content': f"Step {step_id} result: {result}"})
    #         # Store episodic, semantic, and procedural memories
    #         stored_memories = memory_service.extract_and_store_memories(
    #             user_id=user_id,
    #             conversation_messages=conversation_messages,
    #             agent_id=agent_id,
    #             tool_call=None,  # Optionally pass tool call info
    #             feedback=final_reflection.get('notes') if isinstance(final_reflection, dict) else str(final_reflection),
    #             user_goal=workflow.goal
    #         )
    #         logs.append(f"[Memory] Stored memories: {[m.memory_id for m in stored_memories if hasattr(m, 'memory_id')]}")
    #     except Exception as e:
    #         logs.append(f"[Memory] Failed to store long-term memories: {str(e)}")
        
    #     # 8. Output results
    #     return {
    #         'workflow_id': workflow.id,
    #         'status': 'completed' if not failed_steps else 'partial_failure',
    #         'step_results': step_results,
    #         'memory': workflow_memory,
    #         'logs': logs,
    #         'failed_steps': failed_steps,
    #         'final_reflection': final_reflection
    #     }

    # def _parse_workflow_to_dag(self, instructions, required_tools, ltm_context=None, hierarchical_context=None):
    #     """
    #     Use LLM to parse instructions into a list of steps with dependencies (DAG).
    #     Each step: {'id': str, 'tool': str, 'parameters': dict, 'deps': list[str]}
    #     Incorporate LTM and hierarchical context for better planning.
    #     """
    #     # Use LLM to parse instructions into a DAG
    #     planning_prompt = (
    #         "You are an expert workflow planner. Given the following workflow instructions, "
    #         "decompose them into a list of steps with dependencies. "
    #         "Each step should have: 'id', 'tool', 'parameters', and 'deps' (list of step ids it depends on).\n"
    #         f"Instructions:\n{instructions}\n"
    #         f"Relevant facts/context:\n{json.dumps(ltm_context)}\n"
    #         f"Hierarchical context:\n{json.dumps(hierarchical_context) if hierarchical_context else 'None'}\n"
    #         "Respond with a JSON list of steps."
    #     )
    #     planning_messages = [
    #         {"role": "system", "content": planning_prompt}
    #     ]
    #     try:
    #         response = self.llm_client.create_chat_completion(planning_messages, logger=logger)
    #         content = response['choices'][0]['message']['content']
    #         import json as _json
    #         steps = _json.loads(content)
    #         # Validate structure
    #         filtered_steps = []
    #         for step in steps:
    #             if all(k in step for k in ('id', 'tool', 'parameters', 'deps')):
    #                 filtered_steps.append(step)
    #         return filtered_steps
    #     except Exception as e:
    #         if logger:
    #             logger.warning(f"LLM DAG parsing failed: {str(e)}. Falling back to sequential steps.")
    #         return []

    # def _reflect_on_step(self, step, result, memory, logger, ltm_context=None):
    #     """
    #     Use LLM to review the result of a step and decide whether to retry, continue, or escalate.
    #     Returns: dict, e.g., {'retry': false, 'notes': 'Looks good.'}
    #     """
    #     reflection_prompt = (
    #         "You are an expert agentic workflow critic. Review the following step, its result, and context. "
    #         "If the result is incomplete, incorrect, or unsatisfactory, suggest a retry.\n"
    #         f"Step: {json.dumps(step)}\n"
    #         f"Result: {json.dumps(result)}\n"
    #         f"Workflow memory: {json.dumps(memory)}\n"
    #         f"Relevant facts/context: {json.dumps(ltm_context)}\n"
    #         "Respond with a JSON object: {'retry': true/false, 'notes': '...'}"
    #     )
    #     reflection_messages = [
    #         {"role": "system", "content": reflection_prompt}
    #     ]
    #     try:
    #         response = self.llm_client.create_chat_completion(reflection_messages, logger=logger)
    #         content = response['choices'][0]['message']['content']
    #         import json as _json
    #         reflection = _json.loads(content)
    #         if 'retry' in reflection and 'notes' in reflection:
    #             return reflection
    #         return {'retry': False, 'notes': str(reflection)}
    #     except Exception as e:
    #         if logger:
    #             logger.warning(f"LLM reflection failed: {str(e)}. Defaulting to continue.")
    #         return {'retry': False, 'notes': 'Step completed.'}

    # def _final_reflection(self, workflow, step_results, memory, logs, logger, ltm_context=None):
    #     """
    #     Use LLM to review the entire workflow execution for improvement or summary.
    #     Returns: dict or str
    #     """
    #     final_prompt = (
    #         "You are an expert agentic workflow reviewer. Summarize the workflow execution, "
    #         "highlight successes, failures, and suggest improvements.\n"
    #         f"Goal: {workflow.goal}\n"
    #         f"Instructions: {workflow.instructions}\n"
    #         f"Step results: {json.dumps(step_results)}\n"
    #         f"Workflow memory: {json.dumps(memory)}\n"
    #         f"Logs: {json.dumps(logs[-10:])}\n"
    #         f"Relevant facts/context: {json.dumps(ltm_context)}\n"
    #         "Respond with a JSON object: {'summary': '...', 'notes': '...'}"
    #     )
    #     final_messages = [
    #         {"role": "system", "content": final_prompt}
    #     ]
    #     try:
    #         response = self.llm_client.create_chat_completion(final_messages, logger=logger)
    #         content = response['choices'][0]['message']['content']
    #         import json as _json
    #         summary = _json.loads(content)
    #         if 'summary' in summary:
    #             return summary
    #         return {'summary': str(summary)}
    #     except Exception as e:
    #         if logger:
    #             logger.warning(f"LLM final reflection failed: {str(e)}. Returning basic summary.")
    #         return {'summary': 'Workflow execution complete.'}