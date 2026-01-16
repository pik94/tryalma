from uuid import UUID

import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy.ext.asyncio import AsyncSession

from service.database.helpers import get_model_by_id_or_none
from service.database.models.attorneys import Attorney
from service.database.models.leads import Lead, LeadStatus


class AttorneyService:
    @classmethod
    async def get_attorney_by_id(cls, db_session: AsyncSession, attorney_id: UUID) -> Attorney | None:
        """Get an attorney by ID.

        Args:
            db_session: Database session
            attorney_id: Attorney ID to search for

        Returns:
            Attorney instance if found, None otherwise
        """
        return await get_model_by_id_or_none(
            db_session=db_session,
            db_model_class=Attorney,
            id_value=attorney_id,
        )

    @classmethod
    async def get_least_busy_attorney(cls, db_session: AsyncSession) -> Attorney:
        """Get the attorney with the least number of leads that have been reached out to.

        Args:
            db_session: Database session

        Returns:
            Attorney with the least number of reached out leads

        Raises:
            ValueError: If no active attorneys are found
        """
        reached_out_leads_count = (
            sa.select(Lead.reached_out_by.label('attorney_id'), sa.func.count(Lead.id).label('lead_count'))
            .where(Lead.status == LeadStatus.REACHED_OUT)
            .group_by(Lead.reached_out_by)
            .subquery()
        )

        query = (
            sa.select(Attorney, sa.func.coalesce(reached_out_leads_count.c.lead_count, 0).label('lead_count'))
            .outerjoin(reached_out_leads_count, Attorney.id == reached_out_leads_count.c.attorney_id)
            .where(sm.col(Attorney.is_active) == True)  # noqa: E712
            .order_by(sa.func.coalesce(reached_out_leads_count.c.lead_count, 0).asc())
            .limit(1)
        )

        result = await db_session.execute(query)
        row = result.first()

        if not row:
            raise ValueError('No active attorneys found')

        return row[0]  # Return the Attorney object (first element of the tuple)
