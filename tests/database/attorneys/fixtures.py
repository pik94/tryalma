import uuid
from typing import AsyncIterator, Callable, Awaitable

import pytest
import sqlalchemy as sa
from faker import Faker
from pydantic import EmailStr

from service.database.models.attorneys import Attorney


@pytest.fixture(scope='function')
async def create_attorney(
    db_session_factory,
) -> AsyncIterator[Callable[[EmailStr | None, bool | None], Awaitable[Attorney]]]:
    """Create an attorney entry in the database.

    Args:
        db_session_factory: Database session factory fixture

    Yields:
        Async function that creates an attorney with the given parameters or random ones if not provided
    """
    faker = Faker()

    async def _create_attorney(
        email: EmailStr | None = None,
        is_active: bool | None = None,
    ) -> Attorney:
        """Create an attorney entry.

        Args:
            email: Attorney's email address
            is_active: Whether the attorney is active

        Returns:
            Created Attorney instance
        """
        email = email or faker.email()
        is_active = is_active if is_active is not None else True

        async with db_session_factory() as db_session:
            attorney = Attorney(
                id=uuid.uuid4(),
                email=email,
                is_active=is_active,
            )
            db_session.add(attorney)
            await db_session.commit()
            await db_session.refresh(attorney)
            created_attorneys.append(attorney)
            return attorney

    created_attorneys = []

    async def _cleanup():
        async with db_session_factory() as db_session:
            for attorney in created_attorneys:
                await db_session.execute(sa.delete(Attorney).where(Attorney.id == attorney.id))
            await db_session.commit()

    yield _create_attorney

    # Cleanup after the test
    await _cleanup()
