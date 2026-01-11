import os
from typing import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from service.web_app import create_app


@pytest.fixture(scope='session')
def jwt_token() -> str:
    return os.environ['CLIENT_JWT_TOKEN']


@pytest.fixture(scope='function')
async def app(event_loop) -> AsyncGenerator[FastAPI, None]:
    app = create_app()
    async with LifespanManager(app, startup_timeout=10):
        yield app


@pytest.fixture(scope='function')
async def not_auth_test_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
        yield client


@pytest.fixture(scope='function')
async def auth_jwt_test_client(app: FastAPI, jwt_token: str) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://testserver',
        headers={'X-Auth-Token': f'Bearer {jwt_token}'},
    ) as client:
        yield client
