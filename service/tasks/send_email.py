import asyncio
import logging
import pathlib

import sqlalchemy as sa

from service.container import MainContainer
from service.database import get_session_context
from service.database.models.leads import Lead, LeadStatus
from service.services.leads.service import LeadUpdate
from service.utils.date_utils import get_utc_now
from service.utils.decorators import set_context_for_scheduled

logger = logging.getLogger(__name__)


@set_context_for_scheduled
async def send_emails_to_leads(container: MainContainer) -> None:
    """
    Send emails to leads with status 'registered' and update their status to 'reached_out'.
    """
    async with get_session_context(container.database) as db_session:
        try:
            # Get all leads with status 'registered'
            query = sa.select(Lead).where(Lead.status == LeadStatus.REGISTERED)
            result = await db_session.execute(query)
            leads = result.scalars().all()

            if not leads:
                logger.info('No leads with status REGISTERED found')
                return

            logger.info(f'Found {len(leads)} leads to process')

            for lead in leads:
                try:
                    # Get the least busy attorney
                    attorney = await container.attorney_service.get_least_busy_attorney(db_session)

                    # Send email
                    email_text = (
                        "Thank you for submitting your resume. We'll review your application and return back soon."
                    )
                    await container.email_service.send(sender=attorney.email, receiver=lead.email, text=email_text)

                    await container.lead_service.update_lead(
                        db_session=db_session,
                        lead_id=lead.id,
                        lead_data=LeadUpdate(
                            status=LeadStatus.REACHED_OUT,
                            reached_out_by=attorney.id,
                            reached_out_at=get_utc_now(),
                        ),
                    )

                    logger.info(f'Sent email to lead {lead.email} from attorney {attorney.email}')

                except Exception as e:
                    logger.error(f'Error processing lead {lead.id}: {str(e)}')
                    await db_session.rollback()
                    continue

        except Exception as e:
            logger.error(f'Error in send_emails_to_leads task: {str(e)}')
            raise


async def run_task():
    from service.utils.loggers import prepare_logger

    async with MainContainer() as container:
        prepare_logger(app_settings=container.app_settings)
        await send_emails_to_leads(container)


if __name__ == '__main__':
    from dotenv import load_dotenv

    from service import settings

    base_path = pathlib.Path(__file__)

    if settings.ENVIRONMENT == 'dev':
        load_dotenv(base_path.parent.parent.parent / 'configs/.env.dev')
        load_dotenv(base_path.parent.parent.parent / 'configs/overrides/.env.dev', override=True)

    asyncio.run(run_task())
