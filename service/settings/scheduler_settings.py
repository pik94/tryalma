from pydantic import Field
from pydantic_settings import BaseSettings


class SchedulerSettings(BaseSettings):
    update_healthcheck_enabled: bool = True
    update_healthcheck_schedule: str = Field(default='0/1 * * * *')

    send_emails_enabled: bool = True
    send_emails_schedule: str = Field(default='0/30 * * * *')  # Every 30 minutes

    class Config:
        env_prefix = 'SCHEDULER_'
