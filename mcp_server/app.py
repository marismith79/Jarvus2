from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from mcp_server.config import get_settings
from mcp_server.services.availity import AvailityService

settings = get_settings()
availity_service = AvailityService()

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.MCP_SERVER_NAME,
    version=settings.MCP_SERVER_VERSION,
    description=settings.MCP_SERVER_DESCRIPTION
)

@mcp.tool()
async def get_claim_status(claim_id: str, payer_id: str) -> Dict[str, Any]:
    """Get the status of a specific claim.
    
    Args:
        claim_id: The ID of the claim to check
        payer_id: The ID of the payer
    """
    return await availity_service.get_claim_status(claim_id, payer_id)

@mcp.tool()
async def list_claim_statuses(payer_id: str, claim_number: str) -> Dict[str, Any]:
    """List all claim statuses for a payer and claim number.
    
    Args:
        payer_id: The ID of the payer
        claim_number: The claim number to search for
    """
    return await availity_service.list_claim_statuses(payer_id, claim_number)

@mcp.tool()
async def get_configurations(type: str, subtype_id: str, payer_id: str) -> Dict[str, Any]:
    """Get payer configurations.
    
    Args:
        type: The type of configuration
        subtype_id: The subtype ID
        payer_id: The ID of the payer
    """
    return await availity_service.get_configurations(type, subtype_id, payer_id)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')