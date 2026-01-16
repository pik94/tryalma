import uuid

import pytest

from service.database.models.leads import LeadStatus
from service.services.attorneys.service import AttorneyService


async def test_get_attorney_by_id_success(db_session, create_attorney):
    """Test successful attorney retrieval by ID."""
    # Create an attorney
    attorney = await create_attorney()

    # Get attorney by ID
    result = await AttorneyService.get_attorney_by_id(db_session, attorney.id)

    # Verify result
    assert result is not None
    assert result.id == attorney.id
    assert result.email == attorney.email
    assert result.is_active == attorney.is_active


async def test_get_attorney_by_id_not_found(db_session):
    """Test attorney retrieval with non-existent ID."""
    # Try to get non-existent attorney
    non_existent_id = uuid.uuid4()
    result = await AttorneyService.get_attorney_by_id(db_session, non_existent_id)

    # Verify result is None
    assert result is None


async def test_get_least_busy_attorney_single_attorney_no_leads(db_session, create_attorney):
    """Test getting least busy attorney when there's one attorney with no reached out leads."""
    # Create an attorney
    attorney = await create_attorney()

    # Get least busy attorney
    result = await AttorneyService.get_least_busy_attorney(db_session)

    # Verify result
    assert result is not None
    assert result.id == attorney.id
    assert result.email == attorney.email


async def test_get_least_busy_attorney_multiple_attorneys_no_leads(db_session, create_attorney):
    """Test getting least busy attorney when there are multiple attorneys with no reached out leads."""
    # Create multiple attorneys
    attorney1 = await create_attorney(email='attorney1@example.com')
    attorney2 = await create_attorney(email='attorney2@example.com')

    # Get least busy attorney (should return one of them)
    result = await AttorneyService.get_least_busy_attorney(db_session)

    # Verify result is one of the attorneys
    assert result is not None
    assert result.id in [attorney1.id, attorney2.id]


async def test_get_least_busy_attorney_with_reached_out_leads(db_session, create_attorney, create_lead):
    """Test getting least busy attorney when attorneys have different numbers of reached out leads."""
    # Create attorneys
    attorney1 = await create_attorney(email='attorney1@example.com')
    attorney2 = await create_attorney(email='attorney2@example.com')
    attorney3 = await create_attorney(email='attorney3@example.com')

    # Create leads with different statuses and reached_out_by assignments
    # Attorney1: 2 reached out leads
    await create_lead(email='lead1@example.com', status=LeadStatus.REACHED_OUT, reached_out_by=attorney1.id)
    await create_lead(email='lead2@example.com', status=LeadStatus.REACHED_OUT, reached_out_by=attorney1.id)

    # Attorney2: 1 reached out lead
    await create_lead(email='lead3@example.com', status=LeadStatus.REACHED_OUT, reached_out_by=attorney2.id)

    # Attorney3: 0 reached out leads (but has other status leads)
    await create_lead(email='lead4@example.com', status=LeadStatus.REGISTERED, reached_out_by=attorney3.id)

    # Get least busy attorney
    result = await AttorneyService.get_least_busy_attorney(db_session)

    # Should return attorney3 (0 reached out leads)
    assert result is not None
    assert result.id == attorney3.id


async def test_get_least_busy_attorney_ignores_non_reached_out_status(db_session, create_attorney, create_lead):
    """Test that get_least_busy_attorney only counts REACHED_OUT status leads."""
    # Create attorneys
    attorney1 = await create_attorney(email='attorney1@example.com')
    attorney2 = await create_attorney(email='attorney2@example.com')

    # Attorney1: 1 reached out lead + 2 other status leads
    await create_lead(email='lead1@example.com', status=LeadStatus.REACHED_OUT, reached_out_by=attorney1.id)
    await create_lead(email='lead2@example.com', status=LeadStatus.REGISTERED, reached_out_by=attorney1.id)
    await create_lead(email='lead3@example.com', status=LeadStatus.PENDING, reached_out_by=attorney1.id)

    # Attorney2: 0 reached out leads + 1 other status lead
    await create_lead(email='lead4@example.com', status=LeadStatus.EMAIL_SENT, reached_out_by=attorney2.id)

    # Get least busy attorney
    result = await AttorneyService.get_least_busy_attorney(db_session)

    # Should return attorney2 (0 reached out leads)
    assert result is not None
    assert result.id == attorney2.id


async def test_get_least_busy_attorney_only_active_attorneys(db_session, create_attorney, create_lead):
    """Test that get_least_busy_attorney only considers active attorneys."""
    # Create attorneys
    active_attorney = await create_attorney(email='active@example.com', is_active=True)
    inactive_attorney = await create_attorney(email='inactive@example.com', is_active=False)  # noqa: F841

    # Inactive attorney has fewer reached out leads
    await create_lead(email='lead1@example.com', status=LeadStatus.REACHED_OUT, reached_out_by=active_attorney.id)

    # Get least busy attorney
    result = await AttorneyService.get_least_busy_attorney(db_session)

    # Should return active attorney, not inactive one
    assert result is not None
    assert result.id == active_attorney.id
    assert result.is_active is True


async def test_get_least_busy_attorney_no_active_attorneys(db_session, create_attorney):
    """Test get_least_busy_attorney when no active attorneys exist."""
    # Create only inactive attorneys
    await create_attorney(email='inactive1@example.com', is_active=False)
    await create_attorney(email='inactive2@example.com', is_active=False)

    # Should raise ValueError
    with pytest.raises(ValueError, match='No active attorneys found'):
        await AttorneyService.get_least_busy_attorney(db_session)
