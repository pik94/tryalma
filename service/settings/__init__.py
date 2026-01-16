import os
from typing import Literal, cast

from pydantic import SecretBytes, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from service.settings.database_settings import DatabaseSettings  # noqa
from service.settings.scheduler_settings import SchedulerSettings  # noqa


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='APP_')

    console_formatter: bool = False
    debug: bool = False

    jwt_public_key: SecretBytes = b'public-key'

    # Rate limiting settings
    rate_limit: str = '100/hour'  # Default: 100 requests per hour
    rate_limit_period: int = 3600  # Default: 1 hour in seconds


class SentrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='SENTRY_')

    dsn: HttpUrl | None = None


_env = os.environ.get('ENVIRONMENT', 'dev').lower()
ENVIRONMENT = cast(Literal['prod', 'dev', 'test', 'staging'], _env)
