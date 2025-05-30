from fastapi import APIRouter, HTTPException
from ..schemas.request import ConfigurationRequest
from ..schemas.response import ConfigurationResponse
from ..services.availity import availity_service

router = APIRouter()

@router.get("/configurations", response_model=ConfigurationResponse)
async def get_configurations(
    type: str,
    subtype_id: str,
    payer_id: str
):
    """Get payer-specific enhanced-claim-status configuration."""
    try:
        result = await availity_service.get_configurations(
            type=type,
            subtype_id=subtype_id,
            payer_id=payer_id
        )
        return ConfigurationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 