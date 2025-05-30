from typing import Dict, Any
from ..services.availity import availity_service

async def detail_search_tool(claim_number: str, payer_id: str) -> Dict[str, Any]:
    """
    Tool for fetching detailed claim status information.
    
    Args:
        claim_number: The claim number to look up
        payer_id: The payer ID for the claim
        
    Returns:
        Dict containing detailed claim information including service lines and adjustments
    """
    try:
        result = await availity_service.detail_search(
            payer_id=payer_id,
            claim_number=claim_number
        )
        return result
    except Exception as e:
        return {"error": str(e)} 