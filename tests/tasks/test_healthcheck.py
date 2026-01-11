import datetime as dt
from unittest.mock import patch

import sqlalchemy as sa

from service.container import MainContainer
from service.database.models.healthchecks import ServiceType, HealthCheck
from service.tasks.healthcheck import update_healthcheck_data


async def test_update_healthcheck_data_scheduler(
    container: MainContainer,
    db_session_factory,
):
    """Test that update_healthcheck_data creates a healthcheck record for SCHEDULER type."""
    timestamp = dt.datetime(2024, 8, 14, 4, 25, 00, tzinfo=dt.UTC)

    with patch('service.tasks.healthcheck.get_utc_now', lambda: timestamp):
        await update_healthcheck_data(container, ServiceType.SCHEDULER, timestamp)

    async with db_session_factory() as db_session:
        # Query database directly
        stmt = sa.select(HealthCheck).where(
            HealthCheck.type == ServiceType.SCHEDULER, HealthCheck.timestamp == timestamp
        )
        result = await db_session.execute(stmt)
        healthcheck = result.scalar_one_or_none()

        assert healthcheck.type == ServiceType.SCHEDULER
        assert healthcheck.timestamp == timestamp

        # Cleanup
        await db_session.delete(healthcheck)
        await db_session.commit()


async def test_update_healthcheck_data_upsert(
    container: MainContainer,
    db_session_factory,
    create_healthcheck,
):
    """Test that update_healthcheck_data updates existing healthcheck record."""
    initial_timestamp = dt.datetime(2024, 8, 14, 4, 0, 0, tzinfo=dt.UTC)
    updated_timestamp = dt.datetime(2024, 8, 14, 5, 0, 0, tzinfo=dt.UTC)

    # Create initial healthcheck
    await create_healthcheck(type=ServiceType.SCHEDULER, timestamp=initial_timestamp)

    # Update with new timestamp
    with patch('service.tasks.healthcheck.get_utc_now', lambda: updated_timestamp):
        await update_healthcheck_data(container, ServiceType.SCHEDULER, updated_timestamp)

    async with db_session_factory() as db_session:
        # Query database directly
        stmt = sa.select(HealthCheck).where(HealthCheck.type == ServiceType.SCHEDULER)
        result = await db_session.execute(stmt)
        healthcheck = result.scalar_one_or_none()

        assert healthcheck is not None
        assert healthcheck.type == ServiceType.SCHEDULER
        # Should be updated to the new timestamp
        assert healthcheck.timestamp == updated_timestamp
