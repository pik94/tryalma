from contextlib import asynccontextmanager
from typing import AsyncIterator

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine, AsyncSession

from service.database.models.base import SqlModelBase
from service.settings import DatabaseSettings


class Database:
    def __init__(self, db_settings: DatabaseSettings, engine: AsyncEngine):
        self._db_settings = db_settings
        self._engine = engine
        self._session_factory = None
        self._metadata = SqlModelBase.metadata

    @property
    def metadata(self) -> sa.MetaData:
        return self._metadata

    def get_async_session_factory(self):
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self._engine, expire_on_commit=self._db_settings.expire_on_commit
            )
        return self._session_factory

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.create_all)

    async def drop_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.drop_all)


def create_engine(db_settings: DatabaseSettings) -> AsyncEngine:
    return create_async_engine(**db_settings.build_async_engine_options())


@asynccontextmanager
async def get_session_context(database: Database) -> AsyncIterator[AsyncSession]:
    async_session_factory = database.get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
