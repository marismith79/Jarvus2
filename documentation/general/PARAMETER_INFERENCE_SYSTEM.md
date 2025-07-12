# Parameter Inference System

## Overview

The Parameter Inference System is designed to reduce clarification questions in production by intelligently inferring missing tool parameters using semantic memory and user preferences. This system addresses the common problem where AI agents ask too many clarifying questions, creating a poor user experience.

## Problem Statement

### Current Issues
1. **Excessive Clarification Questions**: Agents frequently ask users for missing parameters even when they could be reasonably inferred
2. **Poor User Experience**: Users expect the agent to "just work" without constant interruptions
3. **Inconsistent Behavior**: Different agents handle missing parameters differently
4. **No Learning**: The system doesn't learn from user preferences over time

### Goals
- Reduce clarification questions by 70-80%
- Improve user experience in production environments
- Learn and adapt to user preferences over time
- Maintain accuracy and safety for critical parameters

## Architecture

### Core Components

#### 1. Parameter Inference Service (`parameter_inference_service.py`)
- **Purpose**: Infer missing parameters using semantic memory and user preferences
- **Key Features**:
  - Pre-defined parameter rules for common tools
  - Semantic memory lookup for user preferences
  - Default value fallbacks
  - Integration with existing agent service

#### 2. Orchestrating Agent (`orchestrating_agent.py`)
- **Purpose**: Make intelligent decisions about when to ask vs. when to infer
- **Key Features**:
  - Confidence-based decision making
  - Parameter importance classification
  - Natural language clarification question generation
  - Multi-strategy inference approach

#### 3. Onboarding Service (`onboarding_service.py`)
- **Purpose**: Initialize user preferences during onboarding
- **Key Features**:
  - Default preference population
  - Custom preference overrides
  - Preference detection from conversations
  - Preference management and updates

### Data Flow

```
User Message → Agent Service → Parameter Inference → Orchestrating Agent
     ↓              ↓              ↓                    ↓
Tool Selection → Missing Params → Memory Lookup → Decision: Ask vs Infer
     ↓              ↓              ↓                    ↓
Tool Execution ← Inferred Params ← User Preferences ← Clarification Question
```

## Implementation Details

### Parameter Inference Strategies

#### 1. Semantic Memory Lookup (Highest Confidence)
- Searches user's semantic memory for stored preferences
- Confidence: 0.95 (very high)
- Example: User's timezone preference, meeting duration preference

#### 2. Context-Based LLM Inference (Medium Confidence)
- Uses LLM to infer parameters from conversation context
- Confidence: 0.3-0.8 (variable based on context clarity)
- Example: Inferring meeting location from conversation about "the conference room"

#### 3. Default Values (Low Confidence)
- Uses sensible defaults for optional parameters
- Confidence: 0.3 (low)
- Example: 60-minute default meeting duration

### Parameter Importance Classification

#### Critical Parameters (Confidence Threshold: 0.9)
- **Calendar**: summary, start_time, end_time
- **Email**: to, subject, body
- **Documents**: content

#### Important Parameters (Confidence Threshold: 0.7)
- **Calendar**: attendees, duration, timezone
- **Email**: cc, bcc, priority
- **Documents**: title, folder

#### Optional Parameters (Confidence Threshold: 0.5)
- **Calendar**: location, description, reminder
- **Email**: signature
- **Documents**: template

### Memory Storage Structure

```json
{
  "preference_type": "meeting_duration_preference",
  "value": "90",
  "source": "onboarding",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Usage Examples

### Example 1: Calendar Event Creation

**User Message**: "Schedule a meeting with the team"

**Without Parameter Inference**:
```
Agent: I'd be happy to schedule a meeting for you. What time would you like it to start and end, and who should I invite?
```

**With Parameter Inference**:
```
Agent: I've scheduled a 90-minute team meeting for tomorrow at 2:00 PM in your timezone (America/Los_Angeles). I'll send invites to the team and set a 30-minute reminder.
```

**Inferred Parameters**:
- `duration`: "90" (from user preference)
- `timezone`: "America/Los_Angeles" (from user preference)
- `reminder`: "30" (from user preference)
- `start_time`: "tomorrow 2:00 PM" (from context)

### Example 2: Email Creation

**User Message**: "Send an email to john@example.com about the project update"

**Without Parameter Inference**:
```
Agent: I'll help you send that email. What would you like the subject line to be, and what should I include in the body?
```

**With Parameter Inference**:
```
Agent: I've sent an email to john@example.com with the subject "Project Update" and included your standard signature. The email has been sent with normal priority.
```

**Inferred Parameters**:
- `subject`: "Project Update" (from context)
- `signature`: "Best regards,\nTest User\nSoftware Engineer" (from user preference)
- `priority`: "normal" (from user preference)

## Integration with Existing System

### Agent Service Integration

The parameter inference is integrated into the existing `_orchestrate_tool_calls` method:

```python
# Before tool execution
inferred_args = parameter_inference_service.infer_missing_parameters(
    user_id=user_id,
    tool_name=tool_name,
    provided_params=tool_args,
    user_message=user_message
)

# Execute tool with inferred parameters
tool_result = pipedream_tool_service.execute_tool(
    external_user_id=external_user_id,
    app_slug=app_slug,
    tool_name=tool_name,
    tool_args=inferred_args,  # Use inferred args instead of original
    jwt_token=jwt_token
)
```

### Memory Service Integration

The system leverages the existing semantic memory infrastructure:

```python
# Store user preferences
memory_service.store_semantic_memory(
    user_id=user_id,
    fact_type="user_preference",
    fact_data=memory_data,
    importance_score=3.0
)

# Retrieve preferences for inference
memories = memory_service.search_memories(
    user_id=user_id,
    namespace='semantic',
    query=param_name,
    limit=5
)
```

## Configuration

### Parameter Rules Configuration

```python
self.parameter_rules = {
    "create_calendar_event": {
        "duration": {"default": "60", "memory_key": "meeting_duration_preference"},
        "timezone": {"default": "UTC", "memory_key": "timezone_preference"},
        "reminder": {"default": "15", "memory_key": "reminder_preference"}
    },
    "send_email": {
        "signature": {"default": "", "memory_key": "email_signature"},
        "priority": {"default": "normal", "memory_key": "email_priority_preference"}
    }
}
```

### Confidence Thresholds

```python
self.confidence_thresholds = {
    "critical": 0.9,    # High confidence needed for critical parameters
    "important": 0.7,   # Medium confidence for important parameters
    "optional": 0.5     # Lower confidence for optional parameters
}
```

## Testing

### Running the Test Suite

```bash
python test_parameter_inference.py
```

### Test Scenarios

1. **Basic Parameter Inference**: Tests basic parameter inference with user preferences
2. **Critical Parameter Handling**: Tests when critical parameters are missing
3. **Optional Parameter Handling**: Tests when optional parameters are missing
4. **Clarification Question Generation**: Tests natural language question generation

### Expected Output

```
🧪 Testing Parameter Inference System
==================================================

📋 Step 1: Initializing User Preferences
----------------------------------------
✅ Stored 15 user preferences

🔍 Step 2: Testing Parameter Inference
----------------------------------------

📅 Test Case 1: Calendar Event Creation
User message: Schedule a meeting with the team
Tool: create_calendar_event
Provided params: {'summary': 'Team Meeting'}
✅ Inferred params: {'summary': 'Team Meeting', 'duration': '90', 'timezone': 'America/Los_Angeles', 'reminder': '30'}

🎯 Step 3: Testing Orchestrating Agent
----------------------------------------

⚠️  Test Case 3: Critical Missing Parameters
User message: Create a calendar event
Missing params: ['summary', 'start_time', 'end_time']
Should ask for clarification: True
Params to ask for: ['summary', 'start_time', 'end_time']
🤔 Clarification question: I'd be happy to schedule that meeting for you. What would you like to call it, and what time should it start and end?
```

## Benefits

### For Users
- **Reduced Friction**: Fewer interruptions during task completion
- **Faster Workflows**: Tasks complete more quickly with fewer back-and-forth exchanges
- **Personalized Experience**: System learns and adapts to individual preferences
- **Consistent Behavior**: Predictable parameter handling across different tools

### For Developers
- **Maintainable Code**: Centralized parameter inference logic
- **Extensible System**: Easy to add new tools and parameters
- **Configurable Behavior**: Adjustable confidence thresholds and importance levels
- **Testable Components**: Isolated services with clear interfaces

### For Business
- **Improved User Satisfaction**: Better user experience leads to higher retention
- **Reduced Support Load**: Fewer clarification questions mean fewer support tickets
- **Faster Onboarding**: Users can be productive more quickly
- **Scalable Solution**: System works across multiple tools and use cases

## Future Enhancements

### Planned Features

1. **Dynamic Parameter Learning**: Learn new parameters from successful tool executions
2. **Context-Aware Inference**: Use more sophisticated context analysis
3. **Multi-User Pattern Recognition**: Learn from patterns across similar users
4. **A/B Testing Framework**: Test different inference strategies
5. **Parameter Validation**: Validate inferred parameters before use
6. **User Feedback Integration**: Learn from user corrections and feedback

### Advanced Capabilities

1. **Temporal Context**: Consider time-based patterns (e.g., "morning meetings")
2. **Geographic Context**: Use location-based inference
3. **Collaborative Filtering**: Learn from similar users' preferences
4. **Predictive Inference**: Anticipate user needs based on patterns
5. **Cross-Tool Learning**: Apply learnings from one tool to others

## Conclusion

The Parameter Inference System provides a comprehensive solution to the clarification question problem while maintaining accuracy and user safety. By combining semantic memory, intelligent inference, and configurable decision-making, it significantly improves the user experience while providing a foundation for future enhancements.

The system is designed to be:
- **Safe**: Critical parameters still require high confidence or user input
- **Adaptive**: Learns from user preferences and behavior
- **Extensible**: Easy to add new tools and parameters
- **Maintainable**: Clear separation of concerns and well-documented code

This approach balances automation with user control, providing the best of both worlds for production AI agent systems. 