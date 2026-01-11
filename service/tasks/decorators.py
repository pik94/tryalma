import asyncio
import logging
import uuid
from functools import wraps
from typing import Any, Awaitable, Callable

import sentry_sdk
import structlog

logger = logging.getLogger(__name__)


def set_context_for_scheduled(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    if not asyncio.iscoroutinefunction(func):
        raise TypeError('set_context can decorate only async functions')

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        task_id = f'{func.__name__}-{uuid.uuid4().hex[:8]}'
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(task_id=task_id)

        logger.info(f'Scheduled task started: {task_id}')
        try:
            ret = await func(*args, **kwargs)
        except Exception:
            with sentry_sdk.push_scope() as scope:
                scope.set_context('scheduler_task', {'task_id': task_id})
                logger.exception(f'Scheduled task failed: {task_id}')
            raise
        else:
            logger.info(f'Scheduled task finished: {task_id}')
        return ret

    return wrapper
