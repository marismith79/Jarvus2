from fastapi import APIRouter, HTTPException
from ..services.availity import availity_service
from ..schemas.configurations import ConfigurationList

router = APIRouter()

@router.get("/configurations", response_model=ConfigurationList)
async def get_configurations(type: str, subtype_id: str, payer_id: str):
    """Get payer-specific configurations."""
    try:
        return await availity_service.get_configurations(type, subtype_id, payer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 