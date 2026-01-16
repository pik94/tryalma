import uuid
from typing import AsyncIterator, Callable, Awaitable

import pytest
import sqlalchemy as sa
from faker import Faker
from pydantic import EmailStr

from service.database.models.leads import Lead, LeadStatus


@pytest.fixture(scope='function')
async def create_lead(
    db_session_factory,
) -> AsyncIterator[Callable[[str | None, str | None, EmailStr | None, str | None, LeadStatus | None], Awaitable[Lead]]]:
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
        email: EmailStr | None = None,
        resume_url: str | None = None,
        status: LeadStatus | None = None,
        reached_out_by: uuid.UUID | None = None,
    ) -> Lead:
        """Create a lead entry.

        Args:
            first_name: Lead's first name
            last_name: Lead's last name
            email: Lead's email address
            resume_url: URL to the lead's resume
            status: Lead status

        Returns:
            Created Lead instance
        """
        first_name = first_name or faker.first_name()
        last_name = last_name or faker.last_name()
        email = email or faker.email()
        resume_url = resume_url or faker.url()
        status = status or faker.random_element(
            [LeadStatus.UNKNOWN, LeadStatus.REGISTERED, LeadStatus.EMAIL_SENT, LeadStatus.PENDING]
        )

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
