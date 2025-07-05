"""
Memory Management Routes
Provides API endpoints for managing agent memory.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

from ..services.enhanced_agent_service import enhanced_agent_service
from ..services.memory_service import memory_service
from ..db import db

memory_bp = Blueprint('memory', __name__)
logger = logging.getLogger(__name__)


@memory_bp.route('/context/<int:agent_id>', methods=['GET'])
@login_required
def get_memory_context(agent_id):
    """Get memory context for an agent"""
    try:
        thread_id = request.args.get('thread_id')
        if not thread_id:
            return jsonify({'error': 'thread_id parameter is required'}), 400
        
        context = enhanced_agent_service.get_agent_memory_context(
            agent_id=agent_id,
            user_id=current_user.id,
            thread_id=thread_id
        )
        
        return jsonify(context), 200
        
    except Exception as e:
        logger.error(f"Error getting memory context: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/search', methods=['GET'])
@login_required
def search_memories():
    """Search user memories"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 10))
        
        memories = enhanced_agent_service.search_memories(
            user_id=current_user.id,
            query=query,
            limit=limit
        )
        
        return jsonify({'memories': memories}), 200
        
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/store', methods=['POST'])
@login_required
def store_memory():
    """Store a new memory"""
    try:
        data = request.get_json() or {}
        memory_text = data.get('text')
        memory_type = data.get('type', 'fact')
        importance = float(data.get('importance', 1.0))
        
        if not memory_text:
            return jsonify({'error': 'text is required'}), 400
        
        memory_id = enhanced_agent_service.store_user_memory(
            user_id=current_user.id,
            memory_text=memory_text,
            memory_type=memory_type,
            importance=importance
        )
        
        if memory_id:
            return jsonify({'memory_id': memory_id, 'message': 'Memory stored successfully'}), 201
        else:
            return jsonify({'error': 'Failed to store memory'}), 500
        
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/<memory_id>', methods=['DELETE'])
@login_required
def delete_memory(memory_id):
    """Delete a specific memory"""
    try:
        success = memory_service.delete_memory(
            user_id=current_user.id,
            namespace="memories",
            memory_id=memory_id
        )
        
        if success:
            return jsonify({'message': 'Memory deleted successfully'}), 200
        else:
            return jsonify({'error': 'Memory not found or could not be deleted'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/agent/<int:agent_id>/threads', methods=['GET'])
@login_required
def get_agent_threads(agent_id):
    """Get all threads for an agent"""
    try:
        from ..models.memory import ShortTermMemory
        
        threads = ShortTermMemory.query.filter_by(
            agent_id=agent_id,
            user_id=current_user.id
        ).with_entities(ShortTermMemory.thread_id).distinct().all()
        
        thread_ids = [thread.thread_id for thread in threads]
        
        return jsonify({'threads': thread_ids}), 200
        
    except Exception as e:
        logger.error(f"Error getting agent threads: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/thread/<thread_id>', methods=['DELETE'])
@login_required
def delete_thread(thread_id):
    """Delete a thread and all its checkpoints"""
    try:
        success = memory_service.delete_thread(thread_id, current_user.id)
        
        if success:
            return jsonify({'message': 'Thread deleted successfully'}), 200
        else:
            return jsonify({'error': 'Thread not found or could not be deleted'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting thread: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/stats', methods=['GET'])
@login_required
def get_memory_stats():
    """Get memory statistics for the user"""
    try:
        from ..models.memory import ShortTermMemory, LongTermMemory
        
        # Count short-term memories
        short_term_count = ShortTermMemory.query.filter_by(
            user_id=current_user.id
        ).count()
        
        # Count long-term memories
        long_term_count = LongTermMemory.query.filter_by(
            user_id=current_user.id,
            namespace="memories"
        ).count()
        
        # Count unique threads
        thread_count = ShortTermMemory.query.filter_by(
            user_id=current_user.id
        ).with_entities(ShortTermMemory.thread_id).distinct().count()
        
        # Count memories by type
        memory_types = db.session.query(
            LongTermMemory.memory_type,
            db.func.count(LongTermMemory.id)
        ).filter_by(
            user_id=current_user.id,
            namespace="memories"
        ).group_by(LongTermMemory.memory_type).all()
        
        stats = {
            'short_term_memories': short_term_count,
            'long_term_memories': long_term_count,
            'active_threads': thread_count,
            'memory_types': dict(memory_types)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/chrome_action', methods=['POST'])
@login_required
def store_chrome_action():
    """Store a Chrome action as an episodic memory (dummy endpoint)."""
    try:
        data = request.get_json() or {}
        # Example expected fields: action, target, url, result, timestamp
        memory_data = {
            'type': 'chrome_action',
            'action': data.get('action'),
            'target': data.get('target'),
            'url': data.get('url'),
            'result': data.get('result'),
            'timestamp': data.get('timestamp'),
            'details': data.get('details', {})
        }
        memory_id = memory_service.store_memory(
            user_id=current_user.id,
            namespace='memories',
            memory_data=memory_data,
            memory_type='episode',
            importance_score=1.0,
            search_text=f"chrome {data.get('action')} {data.get('target')} {data.get('url')}"
        ).memory_id
        return jsonify({'memory_id': memory_id, 'message': 'Chrome action stored as episodic memory'}), 201
    except Exception as e:
        logger.error(f"Error storing chrome action: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/feedback', methods=['POST'])
@login_required
def store_feedback():
    """Store user feedback as an episodic memory."""
    try:
        data = request.get_json() or {}
        memory_data = {
            'type': 'feedback',
            'suggestion_id': data.get('suggestion_id'),
            'user_response': data.get('user_response'),
            'notes': data.get('notes'),
            'timestamp': data.get('timestamp'),
        }
        memory_id = memory_service.store_memory(
            user_id=current_user.id,
            namespace='memories',
            memory_data=memory_data,
            memory_type='episode',
            importance_score=1.0,
            search_text=f"feedback {data.get('user_response')} {data.get('notes', '')}"
        ).memory_id
        return jsonify({'memory_id': memory_id, 'message': 'Feedback stored as episodic memory'}), 201
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/workflow_execution', methods=['POST'])
@login_required
def store_workflow_execution():
    """Store a workflow execution as an episodic and/or procedural memory."""
    try:
        data = request.get_json() or {}
        # Store as episode
        episode_data = {
            'type': 'workflow_execution',
            'workflow_id': data.get('workflow_id'),
            'steps': data.get('steps'),
            'result': data.get('result'),
            'timestamp': data.get('timestamp'),
            'details': data.get('details', {})
        }
        episode_id = memory_service.store_memory(
            user_id=current_user.id,
            namespace='memories',
            memory_data=episode_data,
            memory_type='episode',
            importance_score=1.0,
            search_text=f"workflow execution {data.get('workflow_id')} {data.get('result')}"
        ).memory_id
        # Optionally store as procedure if new
        if data.get('store_as_procedure'):
            procedure_data = {
                'type': 'workflow',
                'steps': data.get('steps'),
                'description': data.get('description', ''),
                'created_from_execution': True
            }
            procedure_id = memory_service.store_memory(
                user_id=current_user.id,
                namespace='memories',
                memory_data=procedure_data,
                memory_type='procedure',
                importance_score=2.0,
                search_text=f"workflow procedure {data.get('description', '')}"
            ).memory_id
        else:
            procedure_id = None
        return jsonify({'episode_id': episode_id, 'procedure_id': procedure_id, 'message': 'Workflow execution stored'}), 201
    except Exception as e:
        logger.error(f"Error storing workflow execution: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/episodes', methods=['GET'])
@login_required
def get_episodes():
    """Retrieve recent or similar episodic memories."""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        episodes = memory_service.search_memories(
            user_id=current_user.id,
            namespace='memories',
            query=query,
            limit=limit
        )
        # Filter for episodic
        episodes = [m.to_dict() for m in episodes if m.memory_type == 'episode']
        return jsonify({'episodes': episodes}), 200
    except Exception as e:
        logger.error(f"Error retrieving episodes: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/facts', methods=['GET'])
@login_required
def get_facts():
    """Retrieve semantic memories (facts/preferences)."""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        facts = memory_service.search_memories(
            user_id=current_user.id,
            namespace='memories',
            query=query,
            limit=limit
        )
        # Filter for facts/preferences
        facts = [m.to_dict() for m in facts if m.memory_type in ('fact', 'preference')]
        return jsonify({'facts': facts}), 200
    except Exception as e:
        logger.error(f"Error retrieving facts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/procedures', methods=['GET'])
@login_required
def get_procedures():
    """Retrieve procedural memories (workflows/scripts)."""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        procedures = memory_service.search_memories(
            user_id=current_user.id,
            namespace='memories',
            query=query,
            limit=limit
        )
        # Filter for procedures/workflows
        procedures = [m.to_dict() for m in procedures if m.memory_type in ('procedure', 'workflow')]
        return jsonify({'procedures': procedures}), 200
    except Exception as e:
        logger.error(f"Error retrieving procedures: {str(e)}")
        return jsonify({'error': str(e)}), 500 