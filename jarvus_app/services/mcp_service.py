import os
import json
import requests
import openai
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class MCPService:
    def __init__(self):
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:8000')
        
        # Configure OpenAI for Azure
        openai.api_type = "azure"
        openai.api_base = os.getenv("OPENAI_API_BASE")
        openai.api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.deployment_name = os.getenv('OPENAI_DEPLOYMENT_NAME')

    def get_available_tools(self) -> Dict[str, Any]:
        """Get the list of available tools from the MCP server."""
        response = requests.get(f"{self.mcp_server_url}/tools")
        return response.json()

    def execute_mcp_command(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command on the MCP server."""
        payload = {
            "method": method,
            "params": params
        }
        response = requests.post(
            f"{self.mcp_server_url}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return response.json()

    def process_with_azure_openai(self, user_input: str) -> Dict[str, Any]:
        """Process user input with Azure OpenAI and execute MCP commands."""
        # Get available tools
        tools = self.get_available_tools()
        
        # Create system message with available tools
        system_message = f"""You are an AI assistant that can control a web browser using the following tools:
        {json.dumps(tools, indent=2)}
        
        When the user asks you to perform a web task, you should:
        1. Break down the task into steps
        2. Use the appropriate tools in sequence
        3. Return the results of each step
        
        Your response should be a JSON array of commands to execute, where each command has a 'method' and 'params' field.
        Example response format:
        [
            {{
                "method": "navigate",
                "params": {{ "url": "https://www.merriam-webster.com" }}
            }},
            {{
                "method": "findElement",
                "params": {{ "using": "css selector", "value": "#search" }}
            }}
        ]
        """
        
        try:
            # Get completion from Azure OpenAI
            response = openai.ChatCompletion.create(
                model="jarvusagents6029438036",
                engine=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Extract the JSON response from the AI's message
            ai_response = response.choices[0].message.content
            commands = json.loads(ai_response)
            
            results = []
            for command in commands:
                method = command.get('method')
                params = command.get('params', {})
                result = self.execute_mcp_command(method, params)
                results.append({
                    'command': command,
                    'result': result
                })
            
            return {
                'success': True,
                'results': results
            }
            
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Failed to parse AI response as JSON',
                'ai_response': ai_response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Create a singleton instance
mcp_service = MCPService() 