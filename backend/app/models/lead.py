from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class CopperEmail(BaseModel):
    email: str
    category: str | None = None

class CopperPhoneNumber(BaseModel):
    number: str
    category: str | None = None

class CopperWebsite(BaseModel):
    url: str
    category: str | None = None

class CopperAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class CopperCustomField(BaseModel):
    custom_field_definition_id: int
    value: Any = None


class LeadSnapshot(BaseModel):
    id: int
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    status: str | None = None
    status_id: int | None = None
    customer_source_id: int | None = None
    interaction_count: int | None = None

    address: CopperAddress | None = None
    email: CopperEmail | None = None
    phone_numbers: list[CopperPhoneNumber] = Field(default_factory=list)
    websites: list[CopperWebsite] = Field(default_factory=list)
    custom_fields: list[CopperCustomField] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    date_created: datetime | None = None
    date_modified: datetime | None = None
    date_last_contacted: datetime | None = None


class NormalizedLead(BaseModel):
    copper_lead_id: int
    full_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    primary_email: str | None = None
    phone_numbers: list[str] | None = None
    websites: list[str] | None = None
    city: str | None = None
    source: str | None = None
