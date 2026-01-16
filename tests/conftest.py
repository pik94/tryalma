import asyncio
from typing import AsyncIterator

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from service.container import MainContainer
from service.database import Database
from service.settings import (
    DatabaseSettings,
    AppSettings,
)
from tests.database.fixtures import (
    create_healthcheck,  # noqa: F401
    create_lead,  # noqa: F401
)
from tests.database.attorneys.fixtures import (
    create_attorney,  # noqa: F401
)


@pytest.fixture(scope='session')
def event_loop(request: pytest.FixtureRequest):
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def app_settings() -> AppSettings:
    return AppSettings()


@pytest.fixture(scope='session')
def database_settings():
    return DatabaseSettings()


@pytest.fixture(scope='session')
def async_engine(database_settings: DatabaseSettings, event_loop):
    return create_async_engine(database_settings.build_url('postgresql+asyncpg'), poolclass=NullPool)


@pytest.fixture(scope='session')
async def database(database_settings: DatabaseSettings, async_engine):
    yield Database(database_settings, async_engine)


@pytest.fixture(scope='session')
async def prepare_db(database: Database):
    await database.drop_all()
    await database.create_all()
    yield
    await database.drop_all()


@pytest.fixture(scope='function')
async def db_session_factory(database: Database, prepare_db):
    yield database.get_async_session_factory()


@pytest.fixture(scope='function')
async def db_session(db_session_factory) -> AsyncIterator[AsyncSession]:
    async with db_session_factory() as session:
        yield session


@pytest.fixture(scope='function')
def container(prepare_db) -> AsyncIterator[MainContainer]:
    container = MainContainer()
    yield container
