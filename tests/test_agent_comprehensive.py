import pytest
from jarvus_app.services.agent_service import agent_service
from jarvus_app.services.memory_service import memory_service
from jarvus_app.models.user import User
from jarvus_app.models.history import History
from jarvus_app.models.memory import LongTermMemory, ShortTermMemory
from tests.test_result_logger import log_test_result_to_stdout
import uuid
from jarvus_app.models.history import InteractionHistory

@pytest.mark.usefixtures('session')
def test_agent_memory_system(session, app):
    try:
        # 1. Create a user
        user_id = str(uuid.uuid4())
        user = User(id=user_id, name="Test User", email=f"test_{user_id}@example.com")
        session.add(user)
        session.commit()
        log_test_result_to_stdout("create_user", "pass", response={"user_id": user_id})

        # 2. Create an agent for the user
        agent = agent_service.create_agent(user_id=user_id, name="Test Agent")
        agent_id = agent.id
        log_test_result_to_stdout("create_agent", "pass", response={"agent_id": agent_id})

        # 3. Send a message to the agent (store semantic/episodic memory)
        msg1 = "My favorite color is blue."
        assistant_message, memory_info = agent_service.process_message_with_memory(
            agent_id=agent_id,
            user_id=user_id,
            user_message=msg1
        )
        log_test_result_to_stdout("send_first_message", "pass", response={"assistant": assistant_message, "memory_info": memory_info})

        # 4. Check and print stored episodic and semantic memories
        semantic_memories = LongTermMemory.query.filter_by(user_id=user_id, namespace="semantic").all()
        episodic_memories = LongTermMemory.query.filter_by(user_id=user_id, namespace="episodes").all()
        log_test_result_to_stdout("semantic_memory_content", "pass", response=[m.to_dict() for m in semantic_memories])
        log_test_result_to_stdout("episodic_memory_content", "pass", response=[m.to_dict() for m in episodic_memories])
        print("Semantic Memories:", [m.to_dict() for m in semantic_memories])
        print("Episodic Memories:", [m.to_dict() for m in episodic_memories])

        # 5. Simulate a tool call and user feedback (procedural memory)
        tool_call = {"name": "mock_tool", "args": {"param": "value"}}
        feedback = "The tool worked perfectly."
        conversation_messages = [
            {"role": "user", "content": "Please run the tool.", "feedback": feedback},
            {"role": "assistant", "content": "Tool executed.", "tool_call": tool_call}
        ]
        # Directly call extract_and_store_memories to simulate this
        memory_service.extract_and_store_memories(
            user_id=user_id,
            conversation_messages=conversation_messages,
            agent_id=agent_id,
            tool_call=tool_call,
            feedback=feedback
        )
        procedural_memories = LongTermMemory.query.filter_by(user_id=user_id, namespace="procedures").all()
        log_test_result_to_stdout("procedural_memory_content", "pass", response=[m.to_dict() for m in procedural_memories])
        print("Procedural Memories:", [m.to_dict() for m in procedural_memories])

        # 6. Send a follow-up message to test memory recall
        msg2 = "What is my favorite color?"
        assistant_message2, memory_info2 = agent_service.process_message_with_memory(
            agent_id=agent_id,
            user_id=user_id,
            user_message=msg2
        )
        log_test_result_to_stdout("send_recall_message", "pass", response={"assistant": assistant_message2, "memory_info": memory_info2})
        print("Recall Response:", assistant_message2)

        # 7. Test retrieval: get context for a new message and print it
        context = memory_service.get_context_for_conversation(user_id=user_id, thread_id=None, current_message="What is my favorite color?")
        log_test_result_to_stdout("retrieved_context", "pass", response=context)
        print("Retrieved Context for LLM:", context)
        assert "blue" in context.lower(), "Relevant semantic memory not found in context."
        assert any("mock_tool" in str(m.memory_data) for m in procedural_memories), "Procedural memory not stored."

        # 8. Check short-term memory (working memory)
        checkpoints = ShortTermMemory.query.filter_by(user_id=user_id, agent_id=agent_id).all()
        assert checkpoints, "No short-term memory checkpoints stored."
        log_test_result_to_stdout("short_term_memory_stored", "pass", response=[c.to_dict() for c in checkpoints])

        # 9. Clean up
        # Delete related interaction history rows first
        interaction_histories = session.query(InteractionHistory).filter_by(user_id=user_id).all()
        for ih in interaction_histories:
            session.delete(ih)
        session.delete(agent)
        session.delete(user)
        session.commit()
        log_test_result_to_stdout("cleanup", "pass")

    except Exception as e:
        log_test_result_to_stdout("test_agent_memory_system", "fail", error=str(e))
        raise 
    