import datetime as dt
import enum

import sqlalchemy as sa
import sqlmodel as sm

from service.database.mixins.metadata import CreatedAtMixin
from service.database.models.base import SqlModelBase
from service.database.models.types import EnumString


class ServiceType(str, enum.Enum):
    UNKNOWN = 'unknown'
    API = 'api'
    SCHEDULER = 'scheduler'

    def __str__(self) -> str:
        return self.value


class ServiceTypeString(EnumString):
    enum_type_class = ServiceType


class HealthCheckBase(SqlModelBase):
    type: ServiceType = sm.Field(sa_type=ServiceTypeString, nullable=False, primary_key=True)
    timestamp: dt.datetime = sm.Field(sa_type=sa.DateTime(timezone=True), nullable=False)


class HealthCheck(HealthCheckBase, CreatedAtMixin, table=True):
    __tablename__ = 'healthchecks'
