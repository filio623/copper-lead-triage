from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

class CopperEmail(BaseModel):
    email: str
    category: Optional[str] = None

class CopperPhoneNumber(BaseModel):
    number: str
    category: Optional[str] = None

class CopperWebsite(BaseModel):
    url: str
    category: Optional[str] = None

class CopperAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class CopperCustomField(BaseModel):
    custom_field_definition_id: int
    value: Any = None


class LeadSnapshot(BaseModel):
    id: int
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    status_id: Optional[int] = None
    customer_source_id: Optional[int] = None
    interaction_count: Optional[int] = None

    address: Optional[CopperAddress] = None
    email: Optional[CopperEmail] = None
    phone_numbers: list[CopperPhoneNumber] = Field(default_factory=list)
    websites: list[CopperWebsite] = Field(default_factory=list)
    custom_fields: list[CopperCustomField] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    date_last_contacted: Optional[datetime] = None


class NormalizedLead(BaseModel):
    copper_lead_id: int
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    title: Optional[str] = None
    primary_email: Optional[str] = None
    phone_numbers: Optional[list[str]] = None
    websites: Optional[list[str]] = None
    city: Optional[str] = None
    source: Optional[str] = None
