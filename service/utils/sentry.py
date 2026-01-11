import logging
from typing import Literal

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from service.settings import SentrySettings, ENVIRONMENT


logger = logging.getLogger(__name__)


# Method to avoid duplicated sends
def _before_send(event, hint):
    exc = (event.get('exception') or {}).get('values') or []
    mech = exc[-1].get('mechanism') if exc else None
    if mech and mech.get('type') in ('excepthook', 'asyncio'):
        return None
    return event


def init_sentry(sentry_settings: SentrySettings, service_type: Literal['app', 'scheduler'] = 'app') -> None:
    if not sentry_settings.dsn:
        logger.warning('Sentry init: sentry_dsn not set')
        return

    kwargs = {}
    if service_type == 'app':
        error_codes = set(range(500, 599))
        integrations = [
            StarletteIntegration(
                transaction_style='url',
                failed_request_status_codes=error_codes,
            ),
            FastApiIntegration(
                transaction_style='url',
                failed_request_status_codes=error_codes,
            ),
        ]
    elif service_type == 'scheduler':
        kwargs['before_send'] = _before_send
        integrations = [
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            )
        ]
    else:
        return

    logger.info(f'Init sentry for {service_type=}')
    sentry_sdk.init(
        dsn=str(sentry_settings.dsn),
        environment=ENVIRONMENT,
        integrations=integrations,
        **kwargs,
    )
