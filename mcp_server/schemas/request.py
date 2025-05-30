from pydantic import BaseModel, Field
from typing import Optional, Literal

class ClaimStatusRequest(BaseModel):
    payer_id: str = Field(..., description="The payer ID for the claim")
    claim_number: str = Field(..., description="The claim number to look up")

class ConfigurationRequest(BaseModel):
    type: Literal["enhanced-claim-status"] = Field(..., description="The configuration type")
    subtype_id: Literal["SUMMARY", "DETAIL"] = Field(..., description="The subtype of configuration")
    payer_id: str = Field(..., description="The payer ID to get configurations for") 