from fastapi import APIRouter, HTTPException
from ..schemas.request import ClaimStatusRequest
from ..schemas.response import ClaimStatusSummary, ClaimStatusDetail
from ..services.availity import availity_service

router = APIRouter()

@router.post("/claim-statuses/summarySearch", response_model=ClaimStatusSummary)
async def summary_search(request: ClaimStatusRequest):
    """Get summary claim status information."""
    try:
        result = await availity_service.summary_search(
            payer_id=request.payer_id,
            claim_number=request.claim_number
        )
        return ClaimStatusSummary(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/claim-statuses/detailSearch", response_model=ClaimStatusDetail)
async def detail_search(request: ClaimStatusRequest):
    """Get detailed claim status information."""
    try:
        result = await availity_service.detail_search(
            payer_id=request.payer_id,
            claim_number=request.claim_number
        )
        return ClaimStatusDetail(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 