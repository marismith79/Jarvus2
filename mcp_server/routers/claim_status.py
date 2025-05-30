from fastapi import APIRouter, HTTPException
from typing import List
from ..services.availity import availity_service
from ..schemas.claim_status import ClaimStatusList, ClaimStatusDetail

router = APIRouter()

@router.get("/claim-statuses", response_model=ClaimStatusList)
async def list_claim_statuses(payer_id: str, claim_number: str):
    """List claim statuses matching payer ID and claim number."""
    try:
        return await availity_service.list_claim_statuses(payer_id, claim_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/claim-statuses/{status_id}", response_model=ClaimStatusDetail)
async def get_claim_status(status_id: str):
    """Get a specific claim status by ID."""
    try:
        return await availity_service.get_claim_status(status_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 