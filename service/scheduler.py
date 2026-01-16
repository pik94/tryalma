import asyncio
import datetime as dt
import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Type
from functools import cached_property

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from service.container import MainContainer
from service import settings
from service.database.models.healthchecks import ServiceType
from service.settings import SchedulerSettings
from service.tasks.healthcheck import update_healthcheck_data
from service.tasks.send_email import send_emails_to_leads
from service.utils.loggers import prepare_logger
from service.utils.sentry import init_sentry

logger = logging.getLogger(__name__)


@dataclass
class SchedulerContainer:
    _scheduler: AsyncIOScheduler | None = None

    def __post_init__(self):
        self._container = MainContainer()

    @property
    def scheduler(self) -> AsyncIOScheduler:
        if not self._scheduler:
            jobstores = {'default': MemoryJobStore()}
            job_defaults = {'coalesce': False, 'max_instances': 2}
            self._scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults, timezone=dt.UTC)
        return self._scheduler

    @cached_property
    def scheduler_settings(self) -> SchedulerSettings:
        return SchedulerSettings()

    def add_jobs(self, container: MainContainer) -> None:
        logger.info('Adding scheduler jobs')

        # Healthcheck job
        if self.scheduler_settings.update_healthcheck_enabled:
            logger.info(
                f'Enable update_healthcheck_data by schedule: {self.scheduler_settings.update_healthcheck_schedule}'
            )
            self.scheduler.add_job(
                update_healthcheck_data,
                trigger=CronTrigger.from_crontab(self.scheduler_settings.update_healthcheck_schedule),
                id='update_healthcheck_data',
                replace_existing=True,
                args=(container, ServiceType.SCHEDULER),
            )

        # Email job
        if self.scheduler_settings.send_emails_enabled:
            logger.info(f'Enable send_emails_to_leads by schedule: {self.scheduler_settings.send_emails_schedule}')
            self.scheduler.add_job(
                send_emails_to_leads,
                trigger=CronTrigger.from_crontab(self.scheduler_settings.send_emails_schedule),
                id='send_emails_to_leads',
                replace_existing=True,
                args=(container,),
            )

        logger.info('Jobs added')

    async def __aenter__(self) -> 'SchedulerContainer':
        prepare_logger(app_settings=self._container.app_settings)
        init_sentry(sentry_settings=self._container.sentry_settings, service_type='scheduler')
        logger.info('SchedulerContainer: initialized')

        self._container.start()
        self.scheduler.start()
        self.add_jobs(self._container)
        return self

    async def __aexit__(
        self,
        typ: Type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        logger.info('SchedulerContainer: disposed')
        self._container.stop()
        self.scheduler.shutdown()


async def main():
    async with SchedulerContainer():
        await asyncio.Event().wait()


if __name__ == '__main__':
    if settings.ENVIRONMENT == 'dev':
        load_dotenv('../configs/.env.dev')
        load_dotenv('../configs/overrides/.env.dev', override=True)

    asyncio.run(main())
