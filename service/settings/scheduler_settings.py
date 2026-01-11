from pydantic import Field
from pydantic_settings import BaseSettings


class SchedulerSettings(BaseSettings):
    update_healthcheck_enabled: bool = True
    update_healthcheck_schedule: str = Field(default='0/1 * * * *')

    class Config:
        env_prefix = 'SCHEDULER_'
