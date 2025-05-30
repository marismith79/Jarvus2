from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class Link(BaseModel):
    href: str

class Links(BaseModel):
    self: Link

class Element(BaseModel):
    type: str
    label: str
    order: int
    allowed: bool
    required: bool
    errorMessage: str
    pattern: Optional[str] = None
    maxLength: Optional[int] = None
    defaultValue: Optional[Any] = None
    min: Optional[str] = None
    max: Optional[str] = None
    mode: Optional[str] = None
    values: Optional[List[Dict[str, str]]] = None

class Configuration(BaseModel):
    type: str
    categoryId: str
    categoryValue: str
    payerId: str
    version: str
    elements: Dict[str, Element]
    requiredFieldCombinations: Optional[Dict[str, List[List[str]]]] = None

class ConfigurationList(BaseModel):
    totalCount: int
    count: int
    offset: int
    limit: int
    links: Links
    configurations: List[Configuration] 