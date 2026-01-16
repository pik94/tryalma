import datetime as dt

import pytest

from service.database.models.healthchecks import ServiceType
from service.services.healthcheck.service import HealthCheckService


@pytest.mark.asyncio
async def test_get_last_healthchecks_per_type(create_healthcheck, db_session_factory):
    # Create test data using the fixture
    now = dt.datetime.now(dt.UTC)

    # Create multiple healthchecks with different timestamps for each type
    api_time = now - dt.timedelta(minutes=10)
    await create_healthcheck(type=ServiceType.API, timestamp=api_time)

    scheduler_time = now - dt.timedelta(minutes=15)
    await create_healthcheck(type=ServiceType.SCHEDULER, timestamp=scheduler_time)

    # Call the method under test
    async with db_session_factory() as session:
        result = await HealthCheckService.get_last_healthchecks_per_type(session)

    # Verify the results
    assert len(result) == 2  # One for each service type

    # Convert to dict for easier assertion
    result_dict = {item.type: item for item in result}

    # Check that we got the latest timestamp for each type
    assert result_dict[ServiceType.API].type == ServiceType.API
    assert result_dict[ServiceType.API].timestamp == api_time

    assert result_dict[ServiceType.SCHEDULER].type == ServiceType.SCHEDULER
    assert result_dict[ServiceType.SCHEDULER].timestamp == scheduler_time


@pytest.mark.asyncio
async def test_get_last_healthchecks_per_type_empty(db_session_factory):
    # Test with no data in the database
    async with db_session_factory() as session:
        result = await HealthCheckService.get_last_healthchecks_per_type(session)
    assert len(result) == 0
