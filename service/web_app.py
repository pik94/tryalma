import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
from starlette.responses import JSONResponse

from service import settings
from service.api import errors as api_errors
from service.api.v1.router import v1_router
from service.container import MainContainer
from service.utils.loggers import prepare_logger
from service.utils.sentry import init_sentry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with MainContainer() as container:
        app.state.container = container
        yield


def init_middleware(app: FastAPI):
    # Add new middlewares here. log_request should be called first, so it should be defined last.

    request_handler_logger = structlog.get_logger('request_handler')

    @app.middleware('http')
    async def log_request(request: Request, call_next) -> Response:
        structlog.contextvars.clear_contextvars()
        request.state.started_at = time.monotonic()
        request.state.request_id = uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request.state.request_id)

        response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            response = await call_next(request)
        except Exception:
            request_handler_logger.exception(
                f'Unhandled exception while processing request_id={request.state.request_id}'
            )
            raise
        finally:
            response.headers['request-id'] = request.state.request_id
            request_exec_time = time.monotonic() - request.state.started_at
            response.headers['request-exec-time'] = str(request_exec_time)
            status_code = response.status_code

            request_handler_logger.info(
                'request finished',
                extra={
                    'url': str(request.url),
                    'method': request.method,
                    'status_code': status_code,
                    'request_exec_time': round(request_exec_time, 4),
                },
            )

            return response

    @app.exception_handler(api_errors.HttpServiceException)
    async def handle_http_service_response(request: Request, exc: api_errors.HttpServiceException) -> Response:
        return JSONResponse(
            status_code=exc.status_code,
            content=dict(
                message=exc.message,
                error_items=exc.error_items,
            ),
        )


def init_routers(app: FastAPI):
    app.include_router(v1_router)


def create_app():
    if settings.ENVIRONMENT == 'dev':
        load_dotenv('../configs/.env.dev')
        load_dotenv('../configs/overrides/.env.dev', override=True)

    prepare_logger(app_settings=settings.AppSettings())
    init_sentry(sentry_settings=settings.SentrySettings())

    app = FastAPI(title='Service', lifespan=lifespan)

    init_middleware(app)

    if app.user_middleware[0].kwargs['dispatch'].__name__ != 'log_request':
        raise RuntimeError('log_request should be the first middleware')

    init_routers(app)

    return app


app = create_app()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
