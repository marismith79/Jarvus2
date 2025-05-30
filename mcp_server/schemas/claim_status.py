from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Link(BaseModel):
    href: str

class Links(BaseModel):
    self: Link

class Payer(BaseModel):
    id: str
    name: Optional[str] = None

class Submitter(BaseModel):
    lastName: str
    firstName: str
    id: str

class Provider(BaseModel):
    lastName: str
    firstName: str
    npi: str

class Subscriber(BaseModel):
    lastName: str
    memberId: str

class Patient(BaseModel):
    lastName: str
    birthDate: str
    gender: str
    genderCode: str
    accountNumber: str
    subscriberRelationship: str
    subscriberRelationshipCode: str

class StatusDetail(BaseModel):
    category: str
    categoryCode: str
    status: str
    statusCode: str
    effectiveDate: str
    claimAmount: str
    claimAmountUnits: str
    paymentAmount: str
    paymentAmountUnits: str

class ClaimStatusItem(BaseModel):
    traceId: str
    fromDate: str
    toDate: str
    statusDetails: List[StatusDetail]

class ClaimStatus(BaseModel):
    links: Links
    id: str
    customerId: str
    controlNumber: str
    userId: str
    status: str
    statusCode: str
    createdDate: str
    updatedDate: str
    expirationDate: str
    payer: Payer
    submitter: Submitter
    providers: List[Provider]
    subscriber: Subscriber
    patient: Patient
    claimStatuses: List[ClaimStatusItem]
    claimCount: str

class ClaimStatusList(BaseModel):
    totalCount: int
    count: int
    offset: int
    limit: int
    links: Dict[str, Link]
    claimStatuses: List[ClaimStatus]

class ClaimStatusDetail(ClaimStatus):
    """Detailed claim status response."""
    pass 