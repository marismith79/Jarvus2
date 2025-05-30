from datetime import datetime, timedelta
from typing import Optional
import httpx
from ..config import get_settings

class TokenManager:
    def __init__(self):
        self.settings = get_settings()
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_valid():
            return self._access_token
            
        return await self._refresh_token()
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid."""
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.utcnow() < self._token_expiry
    
    async def _refresh_token(self) -> str:
        """Obtain a new access token from Availity."""
        token_url = self.settings.AVAILITY_TOKEN_URL
        print(f"[TM DEBUG] Refreshing token from: {token_url}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_url,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json"
                    },
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.settings.AVAILITY_CLIENT_ID,
                        "client_secret": self.settings.AVAILITY_CLIENT_SECRET,
                        "scope": "hipaa"  # Required scope
                    }
                )
                response.raise_for_status()
                token_data = response.json()
                
                self._access_token = token_data["access_token"]
                # Set expiry 5 minutes before actual expiry to ensure we refresh in time
                self._token_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"] - 300)
                
                return self._access_token
            except httpx.HTTPError as e:
                if e.response is not None:
                    error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
                else:
                    error_detail = str(e)
                raise Exception(f"Failed to obtain token from Availity: {error_detail}")

# Create a singleton instance
token_manager = TokenManager() 