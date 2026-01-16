import datetime as dt
from uuid import UUID

from pydantic import BaseModel

from service.database.models.leads import LeadBase


class LeadResponse(LeadBase):
    """Schema for lead response with metadata."""

    id: UUID
    created_at: dt.datetime
    updated_at: dt.datetime


class LeadsListResponse(BaseModel):
    """Schema for paginated leads list response."""

    items: list[LeadResponse]
    total: int
    page_size: int
    page: int
