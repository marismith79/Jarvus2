from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ConfigurationResponse(BaseModel):
    version: str = Field(..., description="The configuration version")
    supported_versions: List[str] = Field(..., description="List of supported versions")

class ClaimStatusSummary(BaseModel):
    claim_number: str
    status: str
    payment_amount: Optional[float]
    denial_codes: Optional[List[str]]
    additional_info: Optional[Dict[str, Any]]

class ClaimStatusDetail(BaseModel):
    claim_number: str
    status: str
    service_lines: List[Dict[str, Any]]
    adjustments: Optional[List[Dict[str, Any]]]
    patient_liability: Optional[float]
    copay: Optional[float]
    remarks: Optional[List[str]]
    additional_info: Optional[Dict[str, Any]] 