import asyncio
from mcp_server.app import mcp
from mcp_server.services.availity import availity_service
import time
from mcp_server2.services.browser_service import BrowserService

async def test_tools():
    # Test get_claim_status
    print("\nTesting get_claim_status...")
    try:
        result = await availity_service.get_claim_status(claim_id="123", payer_id="BCBSF")
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test list_claim_statuses
    print("\nTesting list_claim_statuses...")
    try:
        result = await availity_service.list_claim_statuses(payer_id="BCBSF", claim_number="ABC123456")
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test get_configurations
    print("\nTesting get_configurations...")
    try:
        result = await availity_service.get_configurations(type="claim-status", subtype_id="276", payer_id="BCBSF")
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))
