from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT

from service.api.errors import HttpServiceException
from service.api.v1.leads.schemas import (
    LeadResponse,
    LeadsListResponse,
)
from service.services.leads.errors import LeadServiceDuplicateLeadError
from service.services.leads.service import LeadCreateWithResume, LeadUpdate
from service.container import MainContainer
from service.deps import get_container, get_database_session
from service.general.auth import auth_jwt

router = APIRouter(prefix='/internal', tags=['Internal leads'])
public_router = APIRouter(prefix='/leads', tags=['Leads'])


@public_router.post(
    '',
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lead(
    lead_data: LeadCreateWithResume,
    db_session: AsyncSession = Depends(get_database_session),
    container: MainContainer = Depends(get_container),
):
    """Create a new lead with resume (public endpoint, no auth required)."""
    try:
        lead = await container.lead_service.create_lead_with_resume(db_session, lead_data)
    except LeadServiceDuplicateLeadError:
        raise HttpServiceException(status_code=HTTP_409_CONFLICT, message='Application already exists')
    return LeadResponse.model_validate(lead)


@router.get(
    '/leads',
    response_model=LeadsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_leads(
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(10, ge=1, le=100, description='Number of items per page'),
    db_session: AsyncSession = Depends(get_database_session),
    container: MainContainer = Depends(get_container),
    user_id: str = Depends(auth_jwt),
):
    """Get paginated list of leads (requires authentication)."""
    total, leads = await container.lead_service.get_leads_paginated(db_session, page, page_size)

    # Convert to response models
    lead_responses = [LeadResponse.model_validate(lead) for lead in leads]

    return LeadsListResponse(
        items=lead_responses,
        total=total,
        page_size=page_size,
        page=page,
    )


@router.get(
    '/leads/{lead_id}',
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
async def get_lead_by_id(
    lead_id: UUID,
    db_session: AsyncSession = Depends(get_database_session),
    container: MainContainer = Depends(get_container),
    user_id: str = Depends(auth_jwt),
):
    """Get a single lead by ID (requires authentication)."""
    lead = await container.lead_service.get_lead_by_id(db_session, lead_id)
    if not lead:
        raise HttpServiceException(
            status_code=status.HTTP_404_NOT_FOUND,
            message='Lead not found',
        )

    return LeadResponse.model_validate(lead)


@router.patch(
    '/leads/{lead_id}',
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
async def update_lead_status(
    lead_id: UUID,
    update_data: LeadUpdate,
    db_session: AsyncSession = Depends(get_database_session),
    container: MainContainer = Depends(get_container),
    user_id: str = Depends(auth_jwt),
):
    """Update lead status and reach out information (requires authentication)."""
    lead = await container.lead_service.update_lead(db_session, lead_id, update_data)
    return LeadResponse.model_validate(lead)
