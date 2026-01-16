import base64
from uuid import uuid4

import sqlalchemy as sa
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from service.database.models.leads import LeadStatus, Lead


async def test_create_lead_success(db_session, not_auth_test_client: AsyncClient):
    """Test successful lead creation with resume."""
    # Prepare test data similar to LeadCreateWithResume
    resume_data = b'This is a test resume content with some binary data'
    lead_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
        'resume': base64.b64encode(resume_data).decode('utf-8'),  # Base64 encode for JSON
    }

    # Make request to create lead
    response = await not_auth_test_client.post('/api/v1/leads', json=lead_data)

    # Verify response
    assert response.status_code == HTTP_201_CREATED
    response_data = response.json()

    # Verify response structure
    assert 'id' in response_data
    assert response_data['first_name'] == 'Jane'
    assert response_data['last_name'] == 'Smith'
    assert response_data['email'] == 'jane.smith@example.com'
    assert response_data['status'] == LeadStatus.REGISTERED.value
    assert response_data['resume_url'] is not None
    assert response_data['resume_url'].startswith('https://blob-storage.example.com/')
    assert 'created_at' in response_data
    assert 'updated_at' in response_data

    # Verify it exists in database
    result = await db_session.execute(sa.select(Lead).where(Lead.id == response_data['id']))
    db_lead = result.scalar_one_or_none()
    assert db_lead is not None
    assert db_lead.email == 'jane.smith@example.com'

    # Cleanup
    await db_session.execute(sa.delete(Lead).where(Lead.id == response_data['id']))
    await db_session.commit()


async def test_create_lead_duplicate_error(not_auth_test_client: AsyncClient, create_lead):
    """Test duplicate lead creation returns 409 error."""

    await create_lead(
        first_name='John',
        last_name='Doe',
        email='duplicate@example.com',
        resume_url='https://example.com/resume1.pdf',
        status=LeadStatus.REGISTERED,
    )

    # Try to create second lead with same email
    resume_data = b'Second resume content'
    data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'duplicate@example.com',  # Same email
        'resume': base64.b64encode(resume_data).decode('utf-8'),
    }

    response2 = await not_auth_test_client.post('/api/v1/leads', json=data)

    # Verify duplicate error
    assert response2.status_code == HTTP_409_CONFLICT
    response_data = response2.json()
    assert response_data['message'] == 'Application already exists'


async def test_get_leads_success(auth_jwt_test_client: AsyncClient, create_lead):
    """Test successful retrieval of leads list with authentication."""
    # Create test leads using fixture
    await create_lead(first_name='Alice', last_name='Johnson')
    await create_lead(first_name='Bob', last_name='Wilson')
    await create_lead(first_name='Charlie', last_name='Brown')

    # Make authenticated request
    response = await auth_jwt_test_client.get('/api/v1/internal/leads?page=1&page_size=2')

    # Verify response
    assert response.status_code == HTTP_200_OK
    response_data = response.json()

    # Verify response structure
    assert 'items' in response_data
    assert 'total' in response_data
    assert 'page_size' in response_data
    assert 'page' in response_data

    # Verify pagination
    assert response_data['total'] == 3
    assert response_data['page_size'] == 2
    assert response_data['page'] == 1
    assert len(response_data['items']) == 2

    # Verify lead structure
    for lead in response_data['items']:
        assert 'id' in lead
        assert 'first_name' in lead
        assert 'last_name' in lead
        assert 'email' in lead
        assert 'status' in lead
        assert 'created_at' in lead
        assert 'updated_at' in lead


async def test_get_leads_auth_error(not_auth_test_client: AsyncClient):
    """Test get leads without authentication returns 401 error."""
    # Make unauthenticated request
    response = await not_auth_test_client.get('/api/v1/internal/leads')

    # Verify authentication error
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_get_lead_by_id_success(auth_jwt_test_client: AsyncClient, create_lead):
    """Test successful retrieval of single lead by ID with authentication."""
    # Create test lead using fixture
    created_lead = await create_lead(first_name='Test', last_name='User', email='test.user@example.com')

    # Make authenticated request
    response = await auth_jwt_test_client.get(f'/api/v1/internal/leads/{created_lead.id}')

    # Verify response
    assert response.status_code == HTTP_200_OK
    response_data = response.json()

    # Verify lead data
    assert response_data['id'] == str(created_lead.id)
    assert response_data['first_name'] == 'Test'
    assert response_data['last_name'] == 'User'
    assert response_data['email'] == 'test.user@example.com'
    assert 'status' in response_data
    assert 'created_at' in response_data
    assert 'updated_at' in response_data


async def test_get_lead_by_id_not_found(auth_jwt_test_client: AsyncClient):
    """Test get lead by non-existent ID returns 404 error."""
    # Use random UUID that doesn't exist
    non_existent_id = uuid4()

    # Make authenticated request
    response = await auth_jwt_test_client.get(f'/api/v1/internal/leads/{non_existent_id}')

    # Verify not found error
    assert response.status_code == HTTP_404_NOT_FOUND
    response_data = response.json()
    assert response_data['message'] == 'Lead not found'


async def test_get_lead_by_id_auth_error(not_auth_test_client: AsyncClient):
    """Test get lead by ID without authentication returns 401 error."""
    # Use any UUID
    lead_id = uuid4()

    # Make unauthenticated request
    response = await not_auth_test_client.get(f'/api/v1/internal/leads/{lead_id}')

    # Verify authentication error
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_update_lead_status_success(auth_jwt_test_client: AsyncClient, create_attorney, create_lead):
    """Test successful lead status update with authentication."""
    # Create test attorney
    attorney = await create_attorney(email='recruiter@company.com')

    # Create test lead using fixture
    created_lead = await create_lead(
        first_name='Update', last_name='Test', email='update.test@example.com', status=LeadStatus.PENDING
    )

    # Prepare update data similar to LeadUpdate
    update_data = {'status': LeadStatus.REACHED_OUT.value, 'reached_out_by': str(attorney.id)}

    # Make authenticated request
    response = await auth_jwt_test_client.patch(f'/api/v1/internal/leads/{created_lead.id}', json=update_data)

    # Verify response
    assert response.status_code == HTTP_200_OK
    response_data = response.json()

    # Verify updated data
    assert response_data['id'] == str(created_lead.id)
    assert response_data['status'] == LeadStatus.REACHED_OUT.value
    assert response_data['reached_out_by'] == str(attorney.id)
    assert response_data['first_name'] == 'Update'  # Unchanged
    assert response_data['last_name'] == 'Test'  # Unchanged


async def test_update_lead_status_partial_update(auth_jwt_test_client: AsyncClient, create_lead):
    """Test partial lead update (only status)."""
    # Create test lead using fixture
    created_lead = await create_lead(
        first_name='Partial', last_name='Update', email='partial.update@example.com', status=LeadStatus.REGISTERED
    )

    # Prepare partial update data
    update_data = {'status': LeadStatus.EMAIL_SENT.value}

    # Make authenticated request
    response = await auth_jwt_test_client.patch(f'/api/v1/internal/leads/{created_lead.id}', json=update_data)

    # Verify response
    assert response.status_code == HTTP_200_OK
    response_data = response.json()

    # Verify only status was updated
    assert response_data['status'] == LeadStatus.EMAIL_SENT.value
    assert response_data['reached_out_by'] is None  # Should remain unchanged


async def test_update_lead_status_not_found(auth_jwt_test_client: AsyncClient):
    """Test update lead with non-existent ID returns 404 error."""
    # Use random UUID that doesn't exist
    non_existent_id = uuid4()

    update_data = {'status': LeadStatus.REACHED_OUT.value}

    # Make authenticated request
    response = await auth_jwt_test_client.patch(f'/api/v1/internal/leads/{non_existent_id}', json=update_data)

    # Verify not found error
    assert response.status_code == HTTP_404_NOT_FOUND
    response_data = response.json()
    assert response_data['message'] == 'Lead not found'


async def test_update_lead_status_auth_error(not_auth_test_client: AsyncClient):
    """Test update lead status without authentication returns 401 error."""
    # Use any UUID
    lead_id = uuid4()

    update_data = {'status': LeadStatus.REACHED_OUT.value}

    # Make unauthenticated request
    response = await not_auth_test_client.patch(f'/api/v1/internal/leads/{lead_id}', json=update_data)

    # Verify authentication error
    assert response.status_code == HTTP_401_UNAUTHORIZED
