import httpx
from typing import Dict, Any, List
from ..config import get_settings
from ..auth.token_manager import token_manager

class AvailityService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.AVAILITY_API_BASE_URL

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Availity API."""
        token = await token_manager.get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            **kwargs.pop("headers", {})
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

    async def fetch_access_token(self) -> Dict[str, Any]:
        """Fetch a new access token from Availity."""
        url = "https://api.availity.com/availity/v1/token"  # Correct endpoint

        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.AVAILITY_CLIENT_ID,
            "client_secret": self.settings.AVAILITY_CLIENT_SECRET,
            "scope": "hipaa"  # Required scope
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_configurations(self, type: str, subtype_id: str, payer_id: str) -> List[Dict[str, Any]]:
        """Get payer-specific enhanced-claim-status configuration."""
        params = {
            "type": type,
            "subtypeId": subtype_id,
            "payerId": payer_id
        }
        return await self._make_request("GET", "configurations", params=params)

    async def list_claim_statuses(self, payer_id: str, claim_number: str) -> List[Dict[str, Any]]:
        """List claim statuses matching payer ID and claim number."""
        params = {
            "payerId": payer_id,
            "claimNumber": claim_number
        }
        return await self._make_request("GET", "claim-statuses", params=params)

    async def get_claim_status(self, status_id: str) -> Dict[str, Any]:
        """Get a specific claim status by ID."""
        return await self._make_request("GET", f"claim-statuses/{status_id}")

# Create a singleton instance
availity_service = AvailityService() 