from unittest.mock import AsyncMock

from service.database.models.leads import LeadStatus
from service.tasks.send_email import send_emails_to_leads


async def test_send_emails_to_leads_success(container, create_lead, create_attorney):
    """Test successful email sending to registered leads."""
    # Create test data
    attorney = await create_attorney(email='attorney@test.com', is_active=True)
    lead1 = await create_lead(
        first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.REGISTERED
    )
    lead2 = await create_lead(
        first_name='Jane', last_name='Smith', email='jane.smith@test.com', status=LeadStatus.REGISTERED
    )
    # Create a lead with different status that should be ignored
    await create_lead(first_name='Bob', last_name='Wilson', email='bob.wilson@test.com', status=LeadStatus.PENDING)

    # Mock the services
    container.attorney_service.get_least_busy_attorney = AsyncMock(return_value=attorney)
    container.email_service.send = AsyncMock()
    container.lead_service.update_lead = AsyncMock()

    # Execute the task
    await send_emails_to_leads(container)

    # Verify attorney service was called twice (for each registered lead)
    assert container.attorney_service.get_least_busy_attorney.call_count == 2

    # Verify email service was called twice
    assert container.email_service.send.call_count == 2

    # Verify email calls
    email_calls = container.email_service.send.call_args_list
    assert len(email_calls) == 2

    # Check first email call
    first_call = email_calls[0]
    assert first_call.kwargs['sender'] == attorney.email
    assert first_call.kwargs['receiver'] in [lead1.email, lead2.email]
    assert 'Thank you for submitting your resume' in first_call.kwargs['text']

    # Check second email call
    second_call = email_calls[1]
    assert second_call.kwargs['sender'] == attorney.email
    assert second_call.kwargs['receiver'] in [lead1.email, lead2.email]
    assert 'Thank you for submitting your resume' in second_call.kwargs['text']

    # Verify lead service was called twice to update status
    assert container.lead_service.update_lead.call_count == 2

    # Verify lead update calls
    update_calls = container.lead_service.update_lead.call_args_list
    assert len(update_calls) == 2

    for call in update_calls:
        lead_data = call.kwargs['lead_data']
        assert lead_data.status == LeadStatus.REACHED_OUT
        assert lead_data.reached_out_by == attorney.id


async def test_send_emails_to_leads_no_registered_leads(container, create_lead):
    """Test when no leads have REGISTERED status."""
    # Create leads with different statuses
    await create_lead(first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.PENDING)
    await create_lead(first_name='Jane', last_name='Smith', email='jane.smith@test.com', status=LeadStatus.REACHED_OUT)

    # Mock the services
    container.attorney_service.get_least_busy_attorney = AsyncMock()
    container.email_service.send = AsyncMock()
    container.lead_service.update_lead = AsyncMock()

    # Execute the task
    await send_emails_to_leads(container)

    # Verify no services were called since no registered leads exist
    container.attorney_service.get_least_busy_attorney.assert_not_called()
    container.email_service.send.assert_not_called()
    container.lead_service.update_lead.assert_not_called()


async def test_send_emails_to_leads_attorney_service_error(container, create_lead, create_attorney):
    """Test error handling when attorney service fails."""
    # Create test data
    await create_lead(first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.REGISTERED)

    # Mock attorney service to raise an exception
    container.attorney_service.get_least_busy_attorney = AsyncMock(side_effect=Exception('Attorney service error'))
    container.email_service.send = AsyncMock()
    container.lead_service.update_lead = AsyncMock()

    # Execute the task - should not raise exception due to error handling
    await send_emails_to_leads(container)

    # Verify attorney service was called
    container.attorney_service.get_least_busy_attorney.assert_called_once()

    # Verify email and lead update services were not called due to error
    container.email_service.send.assert_not_called()
    container.lead_service.update_lead.assert_not_called()


async def test_send_emails_to_leads_email_service_error(container, create_lead, create_attorney):
    """Test error handling when email service fails."""
    # Create test data
    attorney = await create_attorney(email='attorney@test.com', is_active=True)
    await create_lead(first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.REGISTERED)

    # Mock services
    container.attorney_service.get_least_busy_attorney = AsyncMock(return_value=attorney)
    container.email_service.send = AsyncMock(side_effect=Exception('Email service error'))
    container.lead_service.update_lead = AsyncMock()

    # Execute the task - should not raise exception due to error handling
    await send_emails_to_leads(container)

    # Verify services were called appropriately
    container.attorney_service.get_least_busy_attorney.assert_called_once()
    container.email_service.send.assert_called_once()

    # Verify lead update was not called due to email error
    container.lead_service.update_lead.assert_not_called()


async def test_send_emails_to_leads_lead_update_error(container, create_lead, create_attorney):
    """Test error handling when lead update fails."""
    # Create test data
    attorney = await create_attorney(email='attorney@test.com', is_active=True)
    await create_lead(first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.REGISTERED)

    # Mock services
    container.attorney_service.get_least_busy_attorney = AsyncMock(return_value=attorney)
    container.email_service.send = AsyncMock()
    container.lead_service.update_lead = AsyncMock(side_effect=Exception('Lead update error'))

    # Execute the task - should not raise exception due to error handling
    await send_emails_to_leads(container)

    # Verify all services were called
    container.attorney_service.get_least_busy_attorney.assert_called_once()
    container.email_service.send.assert_called_once()
    container.lead_service.update_lead.assert_called_once()


async def test_send_emails_to_leads_multiple_leads_partial_failure(container, create_lead, create_attorney):
    """Test processing multiple leads where some fail and others succeed."""
    # Create test data
    attorney = await create_attorney(email='attorney@test.com', is_active=True)
    await create_lead(first_name='John', last_name='Doe', email='john.doe@test.com', status=LeadStatus.REGISTERED)
    await create_lead(first_name='Jane', last_name='Smith', email='jane.smith@test.com', status=LeadStatus.REGISTERED)

    # Mock services - first call succeeds, second fails
    container.attorney_service.get_least_busy_attorney = AsyncMock(return_value=attorney)
    container.email_service.send = AsyncMock(side_effect=[None, Exception('Email failed for second lead')])
    container.lead_service.update_lead = AsyncMock()

    # Execute the task
    await send_emails_to_leads(container)

    # Verify attorney service was called twice
    assert container.attorney_service.get_least_busy_attorney.call_count == 2

    # Verify email service was called twice (once successful, once failed)
    assert container.email_service.send.call_count == 2

    # Verify lead update was called only once (for the successful email)
    assert container.lead_service.update_lead.call_count == 1
