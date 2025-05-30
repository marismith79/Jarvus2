from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.availity import availity_service


router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str

@router.post("/oauth/token", response_model=TokenResponse)
async def get_token():
    """Get an OAuth token from Availity."""
    try:
        token_data = await availity_service.fetch_access_token()
        return TokenResponse(
            access_token=token_data["access_token"],
            expires_in=token_data["expires_in"],
            token_type=token_data["token_type"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 