import base64
import datetime as dt
import uuid
from uuid import UUID

import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, field_validator
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from service.api import errors as api_errors
from service.api.errors import HttpServiceException
from service.database.helpers import AscDescEnum, get_list_with_count, get_model_by_id_or_none
from service.database.models.leads import Lead, LeadBase, LeadStatus
from service.services.blob_storage.service import BlobStorageService
from service.services.leads.errors import LeadServiceDuplicateLeadError


class LeadCreate(LeadBase):
    """Schema for creating a new lead (public endpoint)."""

    pass


class LeadCreateWithResume(BaseModel):
    """Schema for creating a new lead with resume bytes."""

    first_name: str
    last_name: str
    email: EmailStr
    resume: bytes

    @field_validator('resume', mode='before')
    @classmethod
    def decode_base64_resume(cls, v):
        """Decode base64 string to bytes if needed."""
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError('Invalid base64 encoded resume data')
        return v


class LeadUpdate(BaseModel):
    """Schema for updating lead status and reach out information."""

    status: LeadStatus | None = None
    reached_out_by: UUID | None = None


class LeadService:
    @classmethod
    async def _check_lead_exists(cls, db_session: AsyncSession, email: str | EmailStr) -> bool:
        # Check if lead with this email already exists
        existing_lead_query = sa.select(Lead).where(Lead.email == email)
        cnt, _ = await get_list_with_count(db_session, existing_lead_query)
        return cnt > 0

    @classmethod
    async def create_lead(cls, db_session: AsyncSession, lead_data: LeadCreate) -> Lead:
        """Create a new lead and persist to database."""

        lead_exists = await cls._check_lead_exists(db_session, lead_data.email)
        if lead_exists:
            raise LeadServiceDuplicateLeadError(f'Lead with email {lead_data.email} already exists')

        # Create new lead instance
        lead = Lead(**lead_data.model_dump(), id=uuid.uuid4())

        # Add to database
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)

        return lead

    @classmethod
    async def create_lead_with_resume(cls, db_session: AsyncSession, lead_data: LeadCreateWithResume) -> Lead:
        """Create a new lead with resume bytes and persist to database."""

        lead_exists = await cls._check_lead_exists(db_session, lead_data.email)
        if lead_exists:
            raise LeadServiceDuplicateLeadError(f'Lead with email {lead_data.email} already exists')

        # Upload resume to blob storage
        resume_url = await BlobStorageService.upload(lead_data.resume)
        if not resume_url:
            raise HttpServiceException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, message='Cannot upload the document')

        # Create new lead instance with uploaded resume URL and registered status
        lead = Lead(
            id=uuid.uuid4(),
            first_name=lead_data.first_name,
            last_name=lead_data.last_name,
            email=lead_data.email,
            resume_url=resume_url,
            status=LeadStatus.REGISTERED,
        )

        # Add to database
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)

        return lead

    @classmethod
    async def get_leads_paginated(cls, db_session: AsyncSession, page: int, page_size: int) -> tuple[int, list[Lead]]:
        """Get paginated list of leads."""
        # Calculate offset
        offset = (page - 1) * page_size

        # Build query
        statement = sa.select(Lead)

        # Get paginated results
        total, leads = await get_list_with_count(
            db_session=db_session,
            statement=statement,
            offset=offset,
            limit=page_size,
            order_by=(sm.col(Lead.created_at), AscDescEnum.DESC),
        )

        return total, leads

    @classmethod
    async def get_lead_by_id(cls, db_session: AsyncSession, lead_id: UUID) -> Lead | None:
        """Get a single lead by ID."""
        return await get_model_by_id_or_none(
            db_session=db_session,
            db_model_class=Lead,
            id_value=lead_id,
        )

    @classmethod
    async def update_lead(cls, db_session: AsyncSession, lead_id: UUID, update_data: LeadUpdate) -> Lead:
        """Update lead status and reach out information."""
        lead = await get_model_by_id_or_none(
            db_session=db_session,
            db_model_class=Lead,
            id_value=lead_id,
        )

        if not lead:
            raise api_errors.HttpServiceException(
                status_code=404,
                message='Lead not found',
            )

        # Update only the allowed fields
        update_dict = update_data.model_dump(exclude_unset=True)

        patched_fields = {'status', 'reached_out_by'}
        for field, value in update_dict.items():
            if field in patched_fields:
                setattr(lead, field, value)

        # Update the updated_at timestamp
        lead.updated_at = dt.datetime.now(dt.UTC)

        await db_session.commit()
        await db_session.refresh(lead)

        return lead
