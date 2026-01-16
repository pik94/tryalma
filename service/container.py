import logging
from functools import cached_property
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncEngine

from service.database import Database, create_engine
from service.services.attorneys.service import AttorneyService
from service.services.blob_storage.service import BlobStorageService
from service.services.email_service.service import EmailService
from service.services.healthcheck.service import HealthCheckService
from service.services.leads.service import LeadService
from service.settings import (
    DatabaseSettings,
    AppSettings,
    SentrySettings,
)


logger = logging.getLogger(__name__)


class MainContainer:
    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
        self,
        typ: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.stop()

    def start(self):
        logger.info('Service: initialized')

    def stop(self):
        logger.info('Service: disposed')

    @cached_property
    def app_settings(self) -> AppSettings:
        return AppSettings()

    @cached_property
    def sentry_settings(self) -> SentrySettings:
        return SentrySettings()

    @cached_property
    def database_settings(self) -> DatabaseSettings:
        return DatabaseSettings()

    @cached_property
    def async_engine(self) -> AsyncEngine:
        return create_engine(self.database_settings)

    @cached_property
    def database(self) -> Database:
        return Database(self.database_settings, self.async_engine)

    @cached_property
    def healthcheck_service(self) -> HealthCheckService:
        return HealthCheckService()

    @cached_property
    def blob_storage_service(self) -> BlobStorageService:
        return BlobStorageService()

    @cached_property
    def lead_service(self) -> LeadService:
        return LeadService()

    @cached_property
    def email_service(self) -> EmailService:
        return EmailService()

    @cached_property
    def attorney_service(self) -> AttorneyService:
        return AttorneyService()
