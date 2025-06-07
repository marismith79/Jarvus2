from typing import Dict, List, Any
import os
import json
import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class MCPService:
    def __init__(self):
        # Initialize with environment variables first
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_endpoint = os.getenv('OPENAI_ENDPOINT')
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        # Try to use Azure Key Vault if configured
        try:
            self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
            if self.key_vault_url:
                self.azure_credential = DefaultAzureCredential()
                self.secret_client = SecretClient(vault_url=self.key_vault_url, credential=self.azure_credential)
                
                # Override with Key Vault secrets if available
                try:
                    self.openai_api_key = self.secret_client.get_secret('openai-api-key').value
                    self.openai_endpoint = self.secret_client.get_secret('openai-endpoint').value
                    self.google_client_id = self.secret_client.get_secret('google-client-id').value
                    self.google_client_secret = self.secret_client.get_secret('google-client-secret').value
                except Exception as e:
                    print(f"Warning: Could not fetch secrets from Key Vault: {str(e)}")
        except Exception as e:
            print(f"Warning: Azure Key Vault not configured: {str(e)}")
        
        # MCP server configuration
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
    
    def process_with_azure_openai(self, user_input: str) -> Dict[str, Any]:
        """Process user input using Azure OpenAI and Google Workspace MCP server."""
        try:
            # First, get the available Google Workspace tools from MCP server
            tools = self.get_available_tools()
            
            # Prepare the request to Azure OpenAI
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.openai_api_key
            }
            
            data = {
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful assistant that can use Google Workspace tools to help users.'},
                    {'role': 'user', 'content': user_input}
                ],
                'tools': tools,
                'temperature': 0.7,
                'max_tokens': 800
            }
            
            # Make request to Azure OpenAI
            response = requests.post(
                f"{self.openai_endpoint}/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Azure OpenAI API error: {response.text}'
                }
            
            result = response.json()
            return {
                'success': True,
                'response': result['choices'][0]['message']['content']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing request: {str(e)}'
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get the list of available Google Workspace MCP tools."""
        try:
            # The Google Workspace MCP server exposes tools for Gmail, Calendar, Drive, etc.
            response = requests.get(f"{self.mcp_server_url}/api/tools")
            if response.status_code == 200:
                tools = response.json()
                # Add Google OAuth configuration to each tool
                for tool in tools:
                    tool['auth'] = {
                        'type': 'oauth2',
                        'client_id': self.google_client_id,
                        'client_secret': self.google_client_secret,
                        'scopes': self._get_scopes_for_tool(tool['name'])
                    }
                return tools
            return []
        except Exception as e:
            print(f"Error getting tools: {str(e)}")
            return []
    
    def _get_scopes_for_tool(self, tool_name: str) -> List[str]:
        """Get the required OAuth scopes for a specific Google Workspace tool."""
        scopes = {
            'gmail': [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.modify'
            ],
            'calendar': [
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.events'
            ],
            'drive': [
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.file'
            ],
            'docs': [
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/documents'
            ],
            'sheets': [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
        }
        return scopes.get(tool_name, [])

# Create a singleton instance
mcp_service = MCPService() 