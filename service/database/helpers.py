import enum
import uuid

import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy.ext.asyncio import AsyncSession


class AscDescEnum(enum.Enum):
    ASC = 'asc'
    DESC = 'desc'


async def get_count(db_session: AsyncSession, statement: sa.Select) -> int:
    return (await db_session.execute(sa.select(sa.func.count()).select_from(statement.subquery()))).scalar_one()


def make_offset_limit_query(
    statement: sa.Select, offset: int | None = None, limit: int | None = None
) -> sa.Select | sa.CompoundSelect:
    if offset:
        statement = statement.offset(offset=offset)
    if limit:
        statement = statement.limit(limit=limit)
    return statement


async def get_list_with_count(
    db_session: AsyncSession,
    statement: sa.Select,
    offset: int | None = None,
    limit: int | None = None,
    lock_for_update: bool = False,
    order_by: tuple[sm.col, AscDescEnum] = None,
) -> tuple[int, list]:
    if lock_for_update:
        statement = statement.with_for_update()
    total_count = await get_count(db_session=db_session, statement=statement)
    statement = make_offset_limit_query(statement=statement, offset=offset, limit=limit)
    if order_by:
        order_by_col, asc_desc = order_by
        if asc_desc == AscDescEnum.DESC:
            statement = statement.order_by(order_by_col.desc())
        else:
            statement = statement.order_by(order_by_col.asc())

    results = (await db_session.execute(statement)).scalars().all()
    return total_count, list(results)


async def get_model_by_id_or_none(
    db_session: AsyncSession,
    db_model_class,
    id_value: int | uuid.UUID,
    id_col: str = 'id',
    lock_for_update: bool = False,
):
    if lock_for_update:
        count, models = await get_list_with_count(
            db_session=db_session,
            statement=sa.select(db_model_class).where(sm.col(getattr(db_model_class, id_col)) == id_value),
            lock_for_update=lock_for_update,
        )
        if not count:
            return None
        db_model = models[0]
    else:
        db_model = await db_session.get(db_model_class, id_value)
        if not db_model:
            return None

    return db_model
