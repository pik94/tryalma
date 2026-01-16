from uuid import uuid4

import pytest
import sqlalchemy as sa

from service.api import errors as api_errors
from service.database.models.leads import Lead, LeadStatus
from service.services.leads.service import LeadService, LeadCreate, LeadCreateWithResume, LeadUpdate
from service.services.leads.errors import LeadServiceDuplicateLeadError


async def test_create_lead(db_session):
    """Test create_lead method - happy path."""
    # Prepare test data
    lead_data = LeadCreate(
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        resume_url='https://example.com/resume.pdf',
        status=LeadStatus.REGISTERED,
    )

    # Call the method
    created_lead = await LeadService.create_lead(db_session, lead_data)

    # Verify the lead was created
    assert created_lead is not None
    assert created_lead.id is not None
    assert created_lead.first_name == 'John'
    assert created_lead.last_name == 'Doe'
    assert created_lead.email == 'john.doe@example.com'
    assert created_lead.resume_url == 'https://example.com/resume.pdf'
    assert created_lead.status == LeadStatus.REGISTERED
    assert created_lead.created_at is not None
    assert created_lead.updated_at is not None

    # Verify it exists in database
    result = await db_session.execute(sa.select(Lead).where(Lead.id == created_lead.id))
    db_lead = result.scalar_one_or_none()
    assert db_lead is not None
    assert db_lead.first_name == 'John'

    # Cleanup
    await db_session.execute(sa.delete(Lead).where(Lead.id == created_lead.id))
    await db_session.commit()


async def test_create_lead_duplicate_email(db_session, create_lead):
    """Test create_lead method raises exception for duplicate email."""

    await create_lead(
        first_name='John',
        last_name='Doe',
        email='duplicate@example.com',
        resume_url='https://example.com/resume1.pdf',
        status=LeadStatus.REGISTERED,
    )

    # Try to create second lead with same email
    data = LeadCreate(
        first_name='Jane',
        last_name='Smith',
        email='duplicate@example.com',  # Same email
        resume_url='https://example.com/resume2.pdf',
        status=LeadStatus.PENDING,
    )

    # Verify that it raises LeadServiceDuplicateLeadError
    with pytest.raises(LeadServiceDuplicateLeadError) as exc_info:
        await LeadService.create_lead(db_session, data)

    assert 'Lead with email duplicate@example.com already exists' in str(exc_info.value)

    # Verify only one lead exists in database
    result = await db_session.execute(sa.select(Lead).where(Lead.email == 'duplicate@example.com'))
    leads = result.scalars().all()
    assert len(leads) == 1
    assert leads[0].first_name == 'John'  # Original lead should remain


async def test_create_lead_with_resume(db_session):
    """Test create_lead_with_resume method - happy path."""
    # Prepare test data
    resume_data = b'This is a test resume content with some binary data'
    lead_data = LeadCreateWithResume(
        first_name='Jane', last_name='Smith', email='jane.smith@example.com', resume=resume_data
    )

    # Call the method
    created_lead = await LeadService.create_lead_with_resume(db_session, lead_data)

    # Verify the lead was created
    assert created_lead is not None
    assert created_lead.id is not None
    assert created_lead.first_name == 'Jane'
    assert created_lead.last_name == 'Smith'
    assert created_lead.email == 'jane.smith@example.com'
    assert created_lead.status == LeadStatus.REGISTERED
    assert created_lead.resume_url is not None
    assert created_lead.resume_url.startswith('https://blob-storage.example.com/')
    assert created_lead.created_at is not None
    assert created_lead.updated_at is not None

    # Verify it exists in database
    result = await db_session.execute(sa.select(Lead).where(Lead.id == created_lead.id))
    db_lead = result.scalar_one_or_none()
    assert db_lead is not None
    assert db_lead.first_name == 'Jane'
    assert db_lead.status == LeadStatus.REGISTERED
    assert db_lead.resume_url.startswith('https://blob-storage.example.com/')

    # Cleanup
    await db_session.execute(sa.delete(Lead).where(Lead.id == created_lead.id))
    await db_session.commit()


async def test_create_lead_with_resume_empty_bytes(db_session):
    """Test create_lead_with_resume method with empty resume bytes."""
    # Prepare test data with empty resume
    lead_data = LeadCreateWithResume(
        first_name='Empty', last_name='Resume', email='empty.resume@example.com', resume=b''
    )

    # Call the method
    created_lead = await LeadService.create_lead_with_resume(db_session, lead_data)

    # Verify the lead was created with registered status
    assert created_lead is not None
    assert created_lead.status == LeadStatus.REGISTERED
    assert created_lead.resume_url is not None
    assert created_lead.resume_url.startswith('https://blob-storage.example.com/')

    # Cleanup
    await db_session.execute(sa.delete(Lead).where(Lead.id == created_lead.id))
    await db_session.commit()


async def test_create_lead_with_resume_duplicate_email(db_session, create_lead):
    """Test create_lead_with_resume method raises exception for duplicate email."""

    await create_lead(
        first_name='John',
        last_name='Doe',
        email='duplicate@example.com',
        resume_url='https://example.com/resume1.pdf',
        status=LeadStatus.REGISTERED,
    )

    # Try to create second lead with same email
    resume_data = b'Second resume content'
    data = LeadCreateWithResume(
        first_name='Jane',
        last_name='Smith',
        email='duplicate@example.com',  # Same email
        resume=resume_data,
    )

    # Verify that it raises LeadServiceDuplicateLeadError
    with pytest.raises(LeadServiceDuplicateLeadError) as exc_info:
        await LeadService.create_lead_with_resume(db_session, data)

    assert 'Lead with email duplicate@example.com already exists' in str(exc_info.value)

    # Verify only one lead exists in database
    result = await db_session.execute(sa.select(Lead).where(Lead.email == 'duplicate@example.com'))
    leads = result.scalars().all()
    assert len(leads) == 1
    assert leads[0].first_name == 'John'  # Original lead should remain
    assert leads[0].status == LeadStatus.REGISTERED


async def test_get_leads_paginated(db_session, create_lead):
    """Test get_leads_paginated method with multiple lead objects."""
    # Create multiple leads using the fixture
    await create_lead(first_name='Alice', last_name='Smith')
    await create_lead(first_name='Bob', last_name='Johnson')
    await create_lead(first_name='Charlie', last_name='Brown')

    # Test pagination - first page
    total, leads = await LeadService.get_leads_paginated(db_session, page=1, page_size=2)

    # Verify results
    assert total == 3
    assert len(leads) == 2
    # Results should be ordered by created_at DESC, so newest first
    assert all(isinstance(lead, Lead) for lead in leads)

    # Test pagination - second page
    total, leads_page2 = await LeadService.get_leads_paginated(db_session, page=2, page_size=2)

    # Verify second page
    assert total == 3
    assert len(leads_page2) == 1

    # Test empty page
    total, leads_empty = await LeadService.get_leads_paginated(db_session, page=3, page_size=2)
    assert total == 3
    assert len(leads_empty) == 0


async def test_get_lead_by_id(db_session, create_lead):
    """Test get_lead_by_id method using create_lead fixture."""
    # Create a lead using the fixture
    created_lead = await create_lead(first_name='Jane', last_name='Doe', email='jane.doe@example.com')

    # Call get_lead_by_id
    retrieved_lead = await LeadService.get_lead_by_id(db_session, created_lead.id)

    # Verify the retrieved lead
    assert retrieved_lead is not None
    assert retrieved_lead.id == created_lead.id
    assert retrieved_lead.first_name == 'Jane'
    assert retrieved_lead.last_name == 'Doe'
    assert retrieved_lead.email == 'jane.doe@example.com'


async def test_get_lead_by_id_not_found(db_session):
    """Test get_lead_by_id method when lead doesn't exist."""
    # Use a random UUID that doesn't exist
    non_existent_id = uuid4()

    # Verify that it returns None
    result = await LeadService.get_lead_by_id(db_session, non_existent_id)
    assert result is None


@pytest.mark.parametrize(
    'field_to_update,new_value',
    [
        ('status', LeadStatus.REACHED_OUT),
    ],
)
async def test_update_lead_single_field(db_session, create_lead, field_to_update, new_value):
    """Test update_lead method for individual fields."""
    # Create a lead using the fixture
    created_lead = await create_lead(first_name='Test', last_name='User', status=LeadStatus.PENDING)

    # Prepare update data
    update_data = LeadUpdate(**{field_to_update: new_value})

    # Call update_lead
    updated_lead = await LeadService.update_lead(db_session, created_lead.id, update_data)

    # Verify the update
    assert updated_lead is not None
    assert updated_lead.id == created_lead.id
    assert getattr(updated_lead, field_to_update) == new_value

    # Verify updated_at was changed
    assert updated_lead.updated_at > created_lead.updated_at

    # Verify the change persisted in database
    result = await db_session.execute(sa.select(Lead).where(Lead.id == created_lead.id))
    db_lead = result.scalar_one_or_none()
    assert db_lead is not None
    assert getattr(db_lead, field_to_update) == new_value


async def test_update_lead_multiple_fields(db_session, create_attorney, create_lead):
    """Test update_lead method with multiple fields."""
    created_attorney = await create_attorney(email='attorney@company.com')

    created_lead = await create_lead(first_name='Multi', last_name='Update', status=LeadStatus.EMAIL_SENT)

    # Prepare update data with multiple fields
    update_data = LeadUpdate(status=LeadStatus.REACHED_OUT, reached_out_by=created_attorney.id)

    # Call update_lead
    updated_lead = await LeadService.update_lead(db_session, created_lead.id, update_data)

    # Verify all updates
    assert updated_lead.status == LeadStatus.REACHED_OUT
    assert updated_lead.reached_out_by == created_attorney.id
    assert updated_lead.updated_at > created_lead.updated_at


async def test_update_lead_not_found(db_session):
    """Test update_lead method when lead doesn't exist."""
    # Use a random UUID that doesn't exist
    non_existent_id = uuid4()
    update_data = LeadUpdate(status=LeadStatus.REACHED_OUT)

    # Verify that it raises the correct exception
    with pytest.raises(api_errors.HttpServiceException) as exc_info:
        await LeadService.update_lead(db_session, non_existent_id, update_data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == 'Lead not found'
