"""
Test script for verifying the OpenAI client functionality.
Run this script directly to test the client: python -m jarvus_app.llm.test_client
"""

from .client import OpenAIClient

def test_basic_chat():
    """Test basic chat functionality with the OpenAI client."""
    try:
        # Initialize the client
        client = OpenAIClient()
        
        # Create a simple conversation
        messages = [
            client.format_message("system", "You are a helpful assistant."),
            client.format_message("user", "Hello! Can you tell me what 2+2 is?")
        ]
        
        # Get response from OpenAI
        response = client.create_chat_completion(messages)
        
        # Print the response
        print("\nTest Results:")
        print("-------------")
        print("User: Hello! Can you tell me what 2+2 is?")
        print(f"Assistant: {response.choices[0].message.content}")
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        raise

if __name__ == "__main__":
    test_basic_chat() 