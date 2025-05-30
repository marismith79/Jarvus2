import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..config import get_settings

class AvailityService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.AVAILITY_API_BASE_URL
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not self._token or not self._token_expiry or datetime.now() >= self._token_expiry:
            token_data = await self.fetch_access_token()
            self._token = token_data["access_token"]
            # Set expiry to slightly less than the actual expiry to ensure we refresh early
            self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"] - 30)
        return self._token

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Availity API."""
        token = await self._get_valid_token()
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
        url = self.settings.AVAILITY_TOKEN_URL

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

    async def get_configurations(self, type: str, subtype_id: str, payer_id: str) -> Dict[str, Any]:
        """Get payer-specific enhanced-claim-status configuration."""
        params = {
            "type": type,
            "subtypeId": subtype_id,
            "payerId": payer_id
        }
        return await self._make_request("GET", "configurations", params=params)

    async def list_claim_statuses(self, payer_id: str, claim_number: str) -> Dict[str, Any]:
        """List claim statuses matching payer ID and claim number."""
        params = {
            "payerId": payer_id,
            "claimNumber": claim_number
        }
        return await self._make_request("GET", "claim-statuses", params=params)

    async def get_claim_status(self, claim_id: str, payer_id: str) -> Dict[str, Any]:
        """Get a specific claim status by ID."""
        return await self._make_request("GET", f"claim-statuses/{claim_id}")

# Create a singleton instance
availity_service = AvailityService() 