import enum
import uuid

import sqlalchemy as sa
import sqlmodel as sm
from pydantic import EmailStr

from service.database.mixins.metadata import CreatedAtMixin, UpdatedAtMixin
from service.database.mixins.primary_keys import PkUuidMixin
from service.database.models.base import SqlModelBase
from service.database.models.types import EnumString


class LeadStatus(str, enum.Enum):
    UNKNOWN = 'unknown'
    REGISTERED = 'registered'
    EMAIL_SENT = 'email_sent'
    PENDING = 'pending'
    REACHED_OUT = 'reached_out'

    def __str__(self) -> str:
        return self.value


class LeadStatusString(EnumString):
    enum_type_class = LeadStatus


class LeadBase(SqlModelBase):
    first_name: str
    last_name: str
    email: EmailStr = sm.Field(sa_type=sa.String(), index=True, unique=True)
    resume_url: str
    status: LeadStatus = sm.Field(sa_type=LeadStatusString, nullable=False)
    reached_out_by: uuid.UUID | None = sm.Field(
        sa_type=sa.UUID, nullable=True, default=None, foreign_key='attorneys.id'
    )


class Lead(LeadBase, PkUuidMixin, CreatedAtMixin, UpdatedAtMixin, table=True):
    __tablename__ = 'leads'
