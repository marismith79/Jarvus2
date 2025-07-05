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


# --- Memory Editing & Improvement Endpoints ---

@memory_bp.route('/api/memory/find-mergeable', methods=['GET'])
@login_required
def find_mergeable_memories():
    """Find memories that can be merged based on similarity"""
    try:
        namespace = request.args.get('namespace', 'episodes')
        similarity_threshold = float(request.args.get('similarity', 0.85))
        
        mergeable_groups = memory_service.find_mergeable_memories(
            user_id=current_user.id,
            namespace=namespace,
            similarity_threshold=similarity_threshold
        )
        
        # Convert to serializable format
        groups_data = []
        for group in mergeable_groups:
            groups_data.append({
                'memories': [memory.to_dict() for memory in group],
                'group_size': len(group),
                'average_similarity': sum(
                    memory_service._calculate_memory_similarity(group[0], memory) 
                    for memory in group[1:]
                ) / (len(group) - 1) if len(group) > 1 else 1.0
            })
        
        return jsonify({
            'success': True,
            'mergeable_groups': groups_data,
            'total_groups': len(groups_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to find mergeable memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/merge', methods=['POST'])
@login_required
def merge_memories():
    """Merge multiple memories into a single, improved memory"""
    try:
        data = request.get_json()
        memory_ids = data.get('memory_ids', [])
        merge_type = data.get('merge_type', 'episodic')
        
        if len(memory_ids) < 2:
            return jsonify({'error': 'At least 2 memories required for merging'}), 400
        
        merged_memory = memory_service.merge_memories(
            user_id=current_user.id,
            memory_ids=memory_ids,
            merge_type=merge_type
        )
        
        if merged_memory:
            return jsonify({
                'success': True,
                'merged_memory': merged_memory.to_dict(),
                'message': f'Successfully merged {len(memory_ids)} memories'
            }), 201
        else:
            return jsonify({'error': 'Failed to merge memories'}), 500
        
    except Exception as e:
        logger.error(f"Failed to merge memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/improve/<memory_id>', methods=['POST'])
@login_required
def improve_memory(memory_id):
    """Improve a specific memory with enhanced content"""
    try:
        data = request.get_json() or {}
        improvement_type = data.get('improvement_type', 'auto')
        
        improved_memory = memory_service.improve_memory(
            user_id=current_user.id,
            memory_id=memory_id,
            improvement_type=improvement_type
        )
        
        if improved_memory:
            return jsonify({
                'success': True,
                'improved_memory': improved_memory.to_dict(),
                'message': f'Successfully improved memory {memory_id}'
            }), 200
        else:
            return jsonify({'error': 'Memory not found or improvement failed'}), 404
        
    except Exception as e:
        logger.error(f"Failed to improve memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/assess-quality/<memory_id>', methods=['GET'])
@login_required
def assess_memory_quality(memory_id):
    """Assess the quality of a memory across multiple dimensions"""
    try:
        quality_scores = memory_service.assess_memory_quality(
            user_id=current_user.id,
            memory_id=memory_id
        )
        
        if quality_scores:
            # Calculate overall quality score
            overall_score = sum(quality_scores.values()) / len(quality_scores)
            
            # Generate improvement suggestions
            suggestions = []
            if quality_scores.get('completeness', 0) < 0.7:
                suggestions.append("Add missing context and details")
            if quality_scores.get('accuracy', 0) < 0.7:
                suggestions.append("Verify information and add confidence levels")
            if quality_scores.get('usefulness', 0) < 0.7:
                suggestions.append("Add actionable insights and recommendations")
            if quality_scores.get('clarity', 0) < 0.7:
                suggestions.append("Improve clarity and reduce ambiguity")
            if quality_scores.get('consistency', 0) < 0.7:
                suggestions.append("Check for conflicts with other memories")
            
            return jsonify({
                'success': True,
                'memory_id': memory_id,
                'quality_scores': quality_scores,
                'overall_score': overall_score,
                'suggested_improvements': suggestions
            }), 200
        else:
            return jsonify({'error': 'Memory not found'}), 404
        
    except Exception as e:
        logger.error(f"Failed to assess memory quality: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/detect-conflicts', methods=['GET'])
@login_required
def detect_memory_conflicts():
    """Detect conflicts between memories"""
    try:
        namespace = request.args.get('namespace', 'episodes')
        
        conflicts = memory_service.detect_memory_conflicts(
            user_id=current_user.id,
            namespace=namespace
        )
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'total_conflicts': len(conflicts)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to detect memory conflicts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/resolve-conflicts', methods=['POST'])
@login_required
def resolve_memory_conflicts():
    """Resolve detected memory conflicts"""
    try:
        data = request.get_json()
        conflicts = data.get('conflicts', [])
        
        if not conflicts:
            return jsonify({'error': 'No conflicts provided'}), 400
        
        resolutions = memory_service.resolve_memory_conflicts(
            user_id=current_user.id,
            conflicts=conflicts
        )
        
        return jsonify({
            'success': True,
            'resolutions': resolutions,
            'resolved_count': len(resolutions)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to resolve memory conflicts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/evolution/<memory_id>', methods=['GET'])
@login_required
def get_memory_evolution(memory_id):
    """Get the evolution history of a memory"""
    try:
        evolution = memory_service.get_memory_evolution(
            user_id=current_user.id,
            memory_id=memory_id
        )
        
        return jsonify({
            'success': True,
            'memory_id': memory_id,
            'evolution': evolution,
            'total_changes': len(evolution)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get memory evolution: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/bulk-improve', methods=['POST'])
@login_required
def bulk_improve_memories():
    """Improve multiple memories in batch"""
    try:
        data = request.get_json()
        memory_ids = data.get('memory_ids', [])
        improvement_type = data.get('improvement_type', 'auto')
        
        if not memory_ids:
            return jsonify({'error': 'No memory IDs provided'}), 400
        
        improved_count = 0
        failed_count = 0
        results = []
        
        for memory_id in memory_ids:
            try:
                improved_memory = memory_service.improve_memory(
                    user_id=current_user.id,
                    memory_id=memory_id,
                    improvement_type=improvement_type
                )
                
                if improved_memory:
                    improved_count += 1
                    results.append({
                        'memory_id': memory_id,
                        'status': 'success',
                        'improved_memory': improved_memory.to_dict()
                    })
                else:
                    failed_count += 1
                    results.append({
                        'memory_id': memory_id,
                        'status': 'failed',
                        'error': 'Memory not found or improvement failed'
                    })
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    'memory_id': memory_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_processed': len(memory_ids),
            'improved_count': improved_count,
            'failed_count': failed_count,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to bulk improve memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/auto-consolidate', methods=['POST'])
@login_required
def auto_consolidate_memories():
    """Automatically consolidate similar memories"""
    try:
        data = request.get_json()
        namespace = request.args.get('namespace', 'episodes')
        similarity_threshold = float(request.args.get('similarity', 0.85))
        
        # Find mergeable groups
        mergeable_groups = memory_service.find_mergeable_memories(
            user_id=current_user.id,
            namespace=namespace,
            similarity_threshold=similarity_threshold
        )
        
        consolidated_count = 0
        results = []
        
        for group in mergeable_groups:
            try:
                memory_ids = [memory.memory_id for memory in group]
                merged_memory = memory_service.merge_memories(
                    user_id=current_user.id,
                    memory_ids=memory_ids,
                    merge_type='episodic'
                )
                
                if merged_memory:
                    consolidated_count += 1
                    results.append({
                        'group_size': len(group),
                        'merged_memory_id': merged_memory.memory_id,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'group_size': len(group),
                        'status': 'failed',
                        'error': 'Merge failed'
                    })
                    
            except Exception as e:
                results.append({
                    'group_size': len(group),
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_groups': len(mergeable_groups),
            'consolidated_count': consolidated_count,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to auto-consolidate memories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/memory/quality-report', methods=['GET'])
@login_required
def get_memory_quality_report():
    """Get a comprehensive quality report for all memories"""
    try:
        namespace = request.args.get('namespace', 'episodes')
        limit = int(request.args.get('limit', 50))
        
        memories = memory_service.search_memories(
            user_id=current_user.id,
            namespace=namespace,
            limit=limit
        )
        
        quality_report = {
            'total_memories': len(memories),
            'average_scores': {
                'completeness': 0.0,
                'accuracy': 0.0,
                'usefulness': 0.0,
                'clarity': 0.0,
                'consistency': 0.0
            },
            'low_quality_memories': [],
            'high_quality_memories': [],
            'improvement_recommendations': []
        }
        
        total_scores = {'completeness': 0, 'accuracy': 0, 'usefulness': 0, 'clarity': 0, 'consistency': 0}
        
        for memory in memories:
            quality_scores = memory_service.assess_memory_quality(
                user_id=current_user.id,
                memory_id=memory.memory_id
            )
            
            if quality_scores:
                # Accumulate scores
                for metric, score in quality_scores.items():
                    total_scores[metric] += score
                
                # Categorize memories
                overall_score = sum(quality_scores.values()) / len(quality_scores)
                
                if overall_score < 0.6:
                    quality_report['low_quality_memories'].append({
                        'memory_id': memory.memory_id,
                        'overall_score': overall_score,
                        'quality_scores': quality_scores
                    })
                elif overall_score > 0.8:
                    quality_report['high_quality_memories'].append({
                        'memory_id': memory.memory_id,
                        'overall_score': overall_score,
                        'quality_scores': quality_scores
                    })
        
        # Calculate averages
        if memories:
            for metric in total_scores:
                quality_report['average_scores'][metric] = total_scores[metric] / len(memories)
        
        # Generate recommendations
        if quality_report['low_quality_memories']:
            quality_report['improvement_recommendations'].append(
                f"Consider improving {len(quality_report['low_quality_memories'])} low-quality memories"
            )
        
        if quality_report['average_scores']['completeness'] < 0.7:
            quality_report['improvement_recommendations'].append(
                "Overall memory completeness is low - consider adding more context"
            )
        
        return jsonify({
            'success': True,
            'quality_report': quality_report
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to generate quality report: {str(e)}")
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