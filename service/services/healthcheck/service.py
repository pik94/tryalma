import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
import sqlmodel as sm

from service.database.models.healthchecks import HealthCheckBase, HealthCheck


class HealthCheckService:
    @classmethod
    async def get_last_healthcheck(cls, db_session) -> HealthCheck | None:
        stmt = sa.select(HealthCheck).order_by(sm.col(HealthCheck.timestamp).desc()).limit(1)
        return (await db_session.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def save_healthcheck(cls, db_session, data: HealthCheckBase, commit: bool = True) -> None:
        data = data.model_dump()
        stmt = insert(HealthCheck).values(data).on_conflict_do_update(index_elements=['type'], set_=data)
        await db_session.execute(stmt)
        if commit:
            await db_session.commit()

    @classmethod
    async def get_last_healthchecks_per_type(cls, db_session) -> list[HealthCheck]:
        """Get the last healthcheck for each service type.

        Returns:
            List of HealthCheck objects, one per service type with the latest timestamp
        """
        # Use group_by to get the latest timestamp for each type
        stmt = sa.select(HealthCheck.type, sa.func.max(HealthCheck.timestamp).label('timestamp')).group_by(
            HealthCheck.type
        )

        result = await db_session.execute(stmt)
        rows = result.all()

        # Convert rows to HealthCheck objects
        return [HealthCheck(type=row.type, timestamp=row.timestamp) for row in rows]
