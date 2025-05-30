from typing import Dict, Any
from ..services.availity import availity_service

async def summary_search_tool(claim_number: str, payer_id: str) -> Dict[str, Any]:
    """
    Tool for fetching claim summary status without PHI.
    
    Args:
        claim_number: The claim number to look up
        payer_id: The payer ID for the claim
        
    Returns:
        Dict containing claim summary information
    """
    try:
        result = await availity_service.summary_search(
            payer_id=payer_id,
            claim_number=claim_number
        )
        return result
    except Exception as e:
        return {"error": str(e)} 