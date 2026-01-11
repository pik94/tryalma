import asyncio
import datetime as dt
import logging
import pathlib

from service.container import MainContainer
from service.database import get_session_context

from service.database.models.healthchecks import ServiceType, HealthCheckBase
from service.utils.date_utils import get_utc_now
from service.utils.decorators import set_context_for_scheduled

logger = logging.getLogger(__name__)


@set_context_for_scheduled
async def update_healthcheck_data(
    container: MainContainer,
    service_type: ServiceType,
    timestamp: dt.datetime | None = None,
):
    timestamp = timestamp or get_utc_now().replace(microsecond=0)
    async with get_session_context(container.database) as db_session:
        await container.healthcheck_service.save_healthcheck(
            db_session=db_session, data=HealthCheckBase(type=service_type, timestamp=timestamp), commit=True
        )


async def run_task():
    from service.utils.loggers import prepare_logger

    async with MainContainer() as container:
        prepare_logger(app_settings=container.app_settings)
        await update_healthcheck_data(container)


if __name__ == '__main__':
    from dotenv import load_dotenv

    from service import settings

    base_path = pathlib.Path(__file__)

    if settings.ENVIRONMENT == 'dev':
        load_dotenv(base_path.parent.parent.parent / 'configs/.env.dev')
        load_dotenv(base_path.parent.parent.parent / 'configs/overrides/.env.dev', override=True)

    asyncio.run(run_task())
