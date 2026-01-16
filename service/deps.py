from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from service.container import MainContainer
from service.database import get_session_context


async def get_container(request: Request) -> MainContainer:
    return request.app.state.container


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with get_session_context(request.app.state.container.database) as session:
        yield session
