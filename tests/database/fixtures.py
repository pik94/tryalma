import datetime as dt
from typing import AsyncIterator, Callable, Awaitable
import uuid

import pytest
import sqlalchemy as sa
from faker import Faker

from service.database.models.healthchecks import HealthCheck, ServiceType
from service.database.models.leads import Lead, LeadStatus


@pytest.fixture(scope='function')
async def create_healthcheck(
    db_session_factory,
) -> AsyncIterator[Callable[[ServiceType | None, dt.datetime | None], Awaitable[HealthCheck]]]:
    """Create a healthcheck entry in the database.

    Args:
        db_session_factory: Database session factory fixture

    Yields:
        Async function that creates a healthcheck with the given parameters or random ones if not provided
    """
    faker = Faker()

    async def _create_healthcheck(
        type: ServiceType | None = None,
        timestamp: dt.datetime | None = None,
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


@pytest.fixture(scope='function')
async def create_lead(
    db_session_factory,
) -> AsyncIterator[Callable[[str | None, str | None, str | None, LeadStatus | None], Awaitable[Lead]]]:
    """Create a lead entry in the database.

    Args:
        db_session_factory: Database session factory fixture

    Yields:
        Async function that creates a lead with the given parameters or random ones if not provided
    """
    faker = Faker()

    async def _create_lead(
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        status: LeadStatus | None = None,
        resume_url: str | None = None,
        reached_out_by: uuid.UUID | None = None,
    ) -> Lead:
        """Create a lead entry.

        Args:
            first_name: Lead's first name
            last_name: Lead's last name
            email: Lead's email address
            status: Lead's status

        Returns:
            Created Lead instance
        """
        first_name = first_name or faker.first_name()
        last_name = last_name or faker.last_name()
        email = email or faker.unique.email()
        status = status or faker.random_element([LeadStatus.REGISTERED, LeadStatus.PENDING, LeadStatus.EMAIL_SENT])
        resume_url = resume_url or f'https://blob-storage.example.com/{uuid.uuid4()}.pdf'

        async with db_session_factory() as db_session:
            lead = Lead(
                id=uuid.uuid4(),
                first_name=first_name,
                last_name=last_name,
                email=email,
                resume_url=resume_url,
                status=status,
                reached_out_by=reached_out_by,
            )
            db_session.add(lead)
            await db_session.commit()
            await db_session.refresh(lead)
            created_leads.append(lead)
            return lead

    created_leads = []

    async def _cleanup():
        async with db_session_factory() as db_session:
            for lead in created_leads:
                await db_session.execute(sa.delete(Lead).where(Lead.id == lead.id))
            await db_session.commit()

    yield _create_lead

    # Cleanup after the test
    await _cleanup()
