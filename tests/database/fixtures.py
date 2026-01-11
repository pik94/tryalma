import datetime as dt
from typing import AsyncIterator, Callable, Awaitable, Optional

import pytest
import sqlalchemy as sa
from faker import Faker

from service.database.models.healthchecks import HealthCheck, ServiceType


@pytest.fixture(scope='function')
async def create_healthcheck(
    db_session_factory,
) -> AsyncIterator[Callable[[Optional[ServiceType], Optional[dt.datetime]], Awaitable[HealthCheck]]]:
    """Create a healthcheck entry in the database.

    Args:
        db_session_factory: Database session factory fixture

    Yields:
        Async function that creates a healthcheck with the given parameters or random ones if not provided
    """
    faker = Faker()

    async def _create_healthcheck(
        type: Optional[ServiceType] = None,
        timestamp: Optional[dt.datetime] = None,
    ) -> HealthCheck:
        """Create a healthcheck entry.

        Args:
            type: Service type (API, SCHEDULER, etc.)
            timestamp: When the healthcheck was recorded

        Returns:
            Created HealthCheck instance
        """
        type = type or faker.random_element([ServiceType.API, ServiceType.SCHEDULER])
        timestamp = timestamp or faker.date_time_between(start_date='-30d', end_date='now', tzinfo=dt.UTC)

        async with db_session_factory() as db_session:
            healthcheck = HealthCheck(
                type=type,
                timestamp=timestamp,
            )
            db_session.add(healthcheck)
            await db_session.commit()
            await db_session.refresh(healthcheck)
            created_healthchecks.append(healthcheck)
            return healthcheck

    created_healthchecks = []

    async def _cleanup():
        async with db_session_factory() as db_session:
            for healthcheck in created_healthchecks:
                await db_session.execute(sa.delete(HealthCheck).where(HealthCheck.type == healthcheck.type))
            await db_session.commit()

    yield _create_healthcheck

    # Cleanup after the test
    await _cleanup()
