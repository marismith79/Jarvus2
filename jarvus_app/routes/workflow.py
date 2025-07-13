from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..models.workflow import Workflow
from ..db import db
from ..services.workflow_execution_service import workflow_execution_service
from ..services.pipedream_tool_registry import pipedream_tool_service
from ..config import ALL_PIPEDREAM_APPS

workflow_bp = Blueprint('workflow', __name__)
logger = logging.getLogger(__name__)

@workflow_bp.route('/workflows/available-tools', methods=['GET'])
@login_required
def get_available_tools():
    """Get available tools for workflow creation"""
    try:
        # Ensure tools are discovered for the current user
        pipedream_tool_service.ensure_initialized(str(current_user.id))
        
        # Get all available apps from config
        available_apps = []
        for app in ALL_PIPEDREAM_APPS:
            app_slug = app["slug"]
            app_name = app["name"]
            
            # Get tools for this app
            app_tools = pipedream_tool_service.get_tools_by_app(app_slug)
            
            if app_tools:  # Only include apps that have tools
                available_apps.append({
                    "id": app_slug,
                    "name": app_name,
                    "tools": [
                        {
                            "name": tool.function.name,
                            "description": tool.function.description
                        }
                        for tool in app_tools
                    ]
                })
        
        return jsonify({
            'success': True,
            'available_apps': available_apps
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available tools: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get available tools'}), 500

@workflow_bp.route('/workflows', methods=['GET'])
@login_required
def get_workflows():
    """Get all workflows for the current user"""
    try:
        workflows = Workflow.get_user_workflows(current_user.id)
        return jsonify({
            'workflows': [workflow.to_dict() for workflow in workflows]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch workflows'}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
@login_required
def get_workflow(workflow_id):
    """Get a specific workflow by ID"""
    try:
        workflow = Workflow.get_workflow_by_id(workflow_id, current_user.id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        return jsonify({'workflow': workflow.to_dict()}), 200
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch workflow'}), 500

@workflow_bp.route('/workflows', methods=['POST'])
@login_required
def create_workflow():
    """Create a new workflow"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['name', 'goal', 'instructions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        workflow = Workflow.create_workflow(
            user_id=current_user.id,
            name=data['name'],
            goal=data['goal'],
            instructions=data['instructions'],
            description=data.get('description'),
            notes=data.get('notes'),
            required_tools=data.get('required_tools', []),
            trigger_type=data.get('trigger_type', 'manual'),
            trigger_config=data.get('trigger_config', {})
        )
        
        return jsonify({
            'workflow': workflow.to_dict(),
            'message': 'Workflow created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to create workflow'}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['PUT'])
@login_required
def update_workflow(workflow_id):
    """Update an existing workflow"""
    try:
        workflow = Workflow.get_workflow_by_id(workflow_id, current_user.id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        data = request.get_json() or {}
        
        # Update workflow fields
        workflow.update_workflow(
            name=data.get('name'),
            goal=data.get('goal'),
            instructions=data.get('instructions'),
            description=data.get('description'),
            notes=data.get('notes'),
            is_active=data.get('is_active'),
            required_tools=data.get('required_tools'),
            trigger_type=data.get('trigger_type'),
            trigger_config=data.get('trigger_config')
        )
        
        return jsonify({
            'workflow': workflow.to_dict(),
            'message': 'Workflow updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update workflow'}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['DELETE'])
@login_required
def delete_workflow(workflow_id):
    """Delete a workflow"""
    try:
        workflow = Workflow.get_workflow_by_id(workflow_id, current_user.id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        workflow.delete_workflow()
        
        return jsonify({
            'message': 'Workflow deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to delete workflow'}), 500

# Workflow Execution Routes

@workflow_bp.route('/workflows/<int:workflow_id>/execute', methods=['POST'])
@login_required
def execute_workflow(workflow_id):
    """Execute a workflow"""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')  # Optional: use specific agent
        thread_id = data.get('thread_id')  # Optional: use specific thread
        
        # Execute the workflow
        execution_result = workflow_execution_service.execute_workflow(
            workflow_id=workflow_id,
            user_id=current_user.id,
            agent_id=agent_id,
            thread_id=thread_id
        )
        
        return jsonify({
            'success': True,
            'execution': execution_result,
            'message': 'Workflow execution started successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to execute workflow: {str(e)}'}), 500

@workflow_bp.route('/executions/<execution_id>', methods=['GET'])
@login_required
def get_execution_status(execution_id):
    """Get the status of a workflow execution"""
    try:
        execution = workflow_execution_service.get_execution_status(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        # Check if the execution belongs to the current user
        if execution['user_id'] != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'execution': execution
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting execution status {execution_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get execution status'}), 500

@workflow_bp.route('/executions/<execution_id>/cancel', methods=['POST'])
@login_required
def cancel_execution(execution_id):
    """Cancel a running workflow execution"""
    try:
        # Get execution to check ownership
        execution = workflow_execution_service.get_execution_status(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        if execution['user_id'] != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Cancel the execution
        success = workflow_execution_service.cancel_execution(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Workflow execution cancelled successfully'
            }), 200
        else:
            return jsonify({'error': 'Execution cannot be cancelled'}), 400
        
    except Exception as e:
        logger.error(f"Error cancelling execution {execution_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to cancel execution'}), 500

@workflow_bp.route('/executions', methods=['GET'])
@login_required
def get_user_executions():
    """Get all executions for the current user"""
    try:
        executions = workflow_execution_service.get_user_executions(current_user.id)
        
        return jsonify({
            'success': True,
            'executions': executions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user executions: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get executions'}), 500

@workflow_bp.route('/workflows/status-summary', methods=['GET'])
@login_required
def get_workflow_status_summary():
    """Get workflow status summary for sidebar categories"""
    try:
        # Get all workflows for the user
        workflows = Workflow.get_user_workflows(current_user.id)
        
        # Get recent executions
        executions = workflow_execution_service.get_user_executions(str(current_user.id))
        
        # Categorize workflows
        all_workflows = [workflow.to_dict() for workflow in workflows]
        
        # Get running workflows (executions with status 'running')
        running_executions = [ex for ex in executions if ex.get('status') == 'running']
        running_workflow_ids = [ex.get('workflow_id') for ex in running_executions]
        running_workflows = [w for w in all_workflows if w['id'] in running_workflow_ids]
        
        # Get workflows that require review (completed with errors or specific conditions)
        review_executions = [ex for ex in executions if ex.get('status') == 'failed' or 
                           (ex.get('status') == 'completed' and ex.get('errors'))]
        review_workflow_ids = [ex.get('workflow_id') for ex in review_executions]
        review_workflows = [w for w in all_workflows if w['id'] in review_workflow_ids]
        
        # Get recently ran workflows (completed in last 24 hours)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_executions = [ex for ex in executions 
                           if ex.get('status') == 'completed' and 
                           ex.get('end_time') and 
                           datetime.fromisoformat(ex['end_time'].replace('Z', '+00:00')) > recent_cutoff]
        recent_workflow_ids = [ex.get('workflow_id') for ex in recent_executions]
        recent_workflows = [w for w in all_workflows if w['id'] in recent_workflow_ids]
        
        return jsonify({
            'success': True,
            'summary': {
                'all_workflows': all_workflows,
                'running_workflows': running_workflows,
                'requires_review_workflows': review_workflows,
                'recently_ran_workflows': recent_workflows
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting workflow status summary: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get workflow status summary'}), 500

@workflow_bp.route('/workflows/<int:workflow_id>/executions', methods=['GET'])
@login_required
def get_workflow_executions(workflow_id):
    """Get all executions for a specific workflow"""
    try:
        # Verify workflow belongs to user
        workflow = Workflow.get_workflow_by_id(workflow_id, current_user.id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        # Get executions for this workflow
        executions = workflow_execution_service.get_user_executions(str(current_user.id))
        workflow_executions = [ex for ex in executions if ex.get('workflow_id') == workflow_id]
        
        return jsonify({
            'success': True,
            'executions': workflow_executions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting workflow executions: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get workflow executions'}), 500

@workflow_bp.route('/executions/<execution_id>/feedback', methods=['POST'])
@login_required
def add_execution_feedback(execution_id):
    """Add feedback for a workflow execution"""
    try:
        data = request.get_json() or {}
        feedback = data.get('feedback', '')
        status = data.get('status')  # 'accepted', 'rejected', 'pending'
        
        if not status or status not in ['accepted', 'rejected', 'pending']:
            return jsonify({'error': 'Invalid status. Must be accepted, rejected, or pending'}), 400
        
        # Get execution to check ownership
        execution = workflow_execution_service.get_execution_status(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        if execution['user_id'] != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Add feedback to the execution
        success = workflow_execution_service.add_feedback(execution_id, feedback, status)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Feedback added successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to add feedback'}), 500
        
    except Exception as e:
        logger.error(f"Error adding execution feedback: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to add feedback'}), 500 