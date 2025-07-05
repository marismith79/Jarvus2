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


@memory_bp.route('/api/memory/chrome-action', methods=['POST'])
@login_required
def store_chrome_action():
    """Store a Chrome action as episodic memory"""
    try:
        data = request.get_json()
        action_data = {
            'action': data.get('action'),
            'target': data.get('target'),
            'url': data.get('url'),
            'result': data.get('result', 'success'),
            'details': data.get('details', {})
        }
        
        memory = memory_service.store_episodic_memory(
            user_id=current_user.id,
            episode_type='chrome_action',
            episode_data=action_data,
            importance_score=data.get('importance', 1.0)
        )
        
        return jsonify({
            'success': True,
            'memory_id': memory.memory_id,
            'message': 'Chrome action stored successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to store Chrome action: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/feedback', methods=['POST'])
@login_required
def store_feedback():
    """Store user feedback as episodic memory"""
    try:
        data = request.get_json()
        feedback_data = {
            'feedback_type': data.get('type', 'general'),
            'rating': data.get('rating'),
            'comment': data.get('comment'),
            'context': data.get('context', {})
        }
        
        memory = memory_service.store_episodic_memory(
            user_id=current_user.id,
            episode_type='feedback',
            episode_data=feedback_data,
            importance_score=data.get('importance', 1.5)
        )
        
        return jsonify({
            'success': True,
            'memory_id': memory.memory_id,
            'message': 'Feedback stored successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to store feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/workflow-execution', methods=['POST'])
@login_required
def store_workflow_execution():
    """Store workflow execution as episodic memory"""
    try:
        data = request.get_json()
        workflow_data = {
            'workflow_name': data.get('name'),
            'steps': data.get('steps', []),
            'result': data.get('result'),
            'duration': data.get('duration'),
            'success': data.get('success', True)
        }
        
        memory = memory_service.store_episodic_memory(
            user_id=current_user.id,
            episode_type='workflow_execution',
            episode_data=workflow_data,
            importance_score=data.get('importance', 2.0)
        )
        
        return jsonify({
            'success': True,
            'memory_id': memory.memory_id,
            'message': 'Workflow execution stored successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to store workflow execution: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/episodic', methods=['GET'])
@login_required
def get_episodic_memories():
    """Get episodic memories"""
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 10))
        
        memories = memory_service.search_memories(
            user_id=current_user.id,
            namespace='episodes',
            query=query,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'memories': [memory.to_dict() for memory in memories]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get episodic memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/semantic', methods=['GET'])
@login_required
def get_semantic_memories():
    """Get semantic memories (facts, preferences)"""
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 10))
        
        memories = memory_service.search_memories(
            user_id=current_user.id,
            namespace='semantic',
            query=query,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'memories': [memory.to_dict() for memory in memories]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get semantic memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/procedural', methods=['GET'])
@login_required
def get_procedural_memories():
    """Get procedural memories (workflows, how-to)"""
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 10))
        
        memories = memory_service.search_memories(
            user_id=current_user.id,
            namespace='procedures',
            query=query,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'memories': [memory.to_dict() for memory in memories]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get procedural memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


# --- Hierarchical Memory Endpoints ---

@memory_bp.route('/api/memory/hierarchical/context', methods=['POST'])
@login_required
def create_hierarchical_context():
    """Create a hierarchical context that can influence other memories"""
    try:
        data = request.get_json()
        
        context = memory_service.create_hierarchical_context(
            user_id=current_user.id,
            name=data.get('name'),
            description=data.get('description', ''),
            context_data=data.get('context_data', {}),
            parent_id=data.get('parent_id'),
            influence_rules=data.get('influence_rules', {}),
            memory_type=data.get('memory_type', 'context'),
            priority=data.get('priority', 0)
        )
        
        return jsonify({
            'success': True,
            'context': context.to_dict(),
            'message': 'Hierarchical context created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create hierarchical context: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/contexts', methods=['GET'])
@login_required
def get_hierarchical_contexts():
    """Get all active hierarchical contexts for the user"""
    try:
        contexts = memory_service.get_active_contexts(current_user.id)
        
        return jsonify({
            'success': True,
            'contexts': [context.to_dict() for context in contexts]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get hierarchical contexts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/context/<memory_id>', methods=['GET'])
@login_required
def get_context_influence(memory_id):
    """Get the influence context from a specific memory and its ancestors"""
    try:
        influence = memory_service.get_context_influence(memory_id, current_user.id)
        
        return jsonify({
            'success': True,
            'influence': influence
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get context influence: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/context/<memory_id>', methods=['PUT'])
@login_required
def update_hierarchical_context(memory_id):
    """Update a hierarchical context"""
    try:
        data = request.get_json()
        
        context = memory_service.update_context(
            user_id=current_user.id,
            memory_id=memory_id,
            context_data=data.get('context_data'),
            influence_rules=data.get('influence_rules'),
            is_active=data.get('is_active'),
            priority=data.get('priority')
        )
        
        if context:
            return jsonify({
                'success': True,
                'context': context.to_dict(),
                'message': 'Context updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Context not found'}), 404
        
    except Exception as e:
        logger.error(f"Failed to update hierarchical context: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/context/<memory_id>', methods=['DELETE'])
@login_required
def delete_hierarchical_context(memory_id):
    """Delete a hierarchical context and all its descendants"""
    try:
        success = memory_service.delete_context(current_user.id, memory_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Context deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Context not found'}), 404
        
    except Exception as e:
        logger.error(f"Failed to delete hierarchical context: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/contextualized/<namespace>', methods=['GET'])
@login_required
def get_contextualized_memories(namespace):
    """Get memories with contextual influence applied"""
    try:
        query = request.args.get('query')
        context_memory_id = request.args.get('context_id')
        limit = int(request.args.get('limit', 10))
        
        memories, context_influence = memory_service.get_contextualized_memories(
            user_id=current_user.id,
            namespace=namespace,
            query=query,
            context_memory_id=context_memory_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'memories': [memory.to_dict() for memory in memories],
            'context_influence': context_influence
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get contextualized memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/decision-context', methods=['POST'])
@login_required
def get_decision_context():
    """Get combined context for a specific decision type"""
    try:
        data = request.get_json()
        decision_type = data.get('decision_type', 'general')
        
        combined_context = memory_service.get_combined_context_for_decision(
            user_id=current_user.id,
            decision_type=decision_type
        )
        
        return jsonify({
            'success': True,
            'context': combined_context
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get decision context: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/example/vacation', methods=['POST'])
@login_required
def create_vacation_example():
    """Create an example vacation context that influences all decisions"""
    try:
        vacation_context = memory_service.create_vacation_context_example(current_user.id)
        
        return jsonify({
            'success': True,
            'context': vacation_context.to_dict(),
            'message': 'Vacation context example created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create vacation example: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/root-contexts', methods=['GET'])
@login_required
def get_root_contexts():
    """Get all root-level contexts"""
    try:
        contexts = memory_service.get_root_contexts(current_user.id)
        
        return jsonify({
            'success': True,
            'contexts': [context.to_dict() for context in contexts]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get root contexts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/hierarchical/context/<memory_id>/children', methods=['GET'])
@login_required
def get_context_children(memory_id):
    """Get all children of a specific context"""
    try:
        children = memory_service.get_context_children(memory_id, current_user.id)
        
        return jsonify({
            'success': True,
            'children': [child.to_dict() for child in children]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get context children: {str(e)}")
        return jsonify({'error': str(e)}), 500 