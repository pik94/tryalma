from pydantic import BaseModel

from service.database.models.healthchecks import HealthCheckBase


class HealthChecksResponse(BaseModel):
    items: list[HealthCheckBase]
