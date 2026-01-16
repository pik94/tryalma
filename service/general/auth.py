import base64
import datetime as dt
import logging

import fastapi
from fastapi import Request, status
import jwt
from jwt.exceptions import PyJWTError

from service.api import errors as api_errors
from service.utils.date_utils import get_utc_now

logger = logging.getLogger(__name__)


signature_header_name = 'X-Auth-Token'
signature_header = fastapi.security.APIKeyHeader(
    name=signature_header_name, scheme_name='BearerTokenAuthHeader', auto_error=False
)

JWT_ALGORITHM = 'ES256'
BEARER_TOKEN_PREFIX = 'Bearer '


def auth_jwt(
    request: Request,
    token: str | None = fastapi.Security(signature_header),
) -> str | None:
    if not token:
        raise api_errors.HttpPnlServiceException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message='Auth token empty',
        )

    if not token.startswith(BEARER_TOKEN_PREFIX):
        raise api_errors.HttpPnlServiceException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Invalid token format. Must be '{BEARER_TOKEN_PREFIX}<token>'",
        )

    token = token[len(BEARER_TOKEN_PREFIX) :].strip()

    app_settings = request.app.state.container.app_settings
    payload = None
    try:
        pk = base64.b64decode(app_settings.jwt_public_key.get_secret_value())
        payload = jwt.decode(token, pk, algorithms=[JWT_ALGORITHM])
    except PyJWTError:
        logger.error('Auth token verification invalid')
        raise api_errors.HttpPnlServiceException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message='Invalid token',
        )

    user_id = payload.get('user_id')
    logger.info(f'Auth token verification succeeded: {user_id}')

    expired_at = payload.get('expired_at')
    if expired_at:
        logger.error(f'Auth token verification expired for user_id: {user_id}')
        if dt.datetime.fromtimestamp(expired_at, tz=dt.UTC) < get_utc_now():
            raise api_errors.HttpPnlServiceException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message='Token expired',
            )

    return user_id
