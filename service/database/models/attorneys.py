import sqlalchemy as sa
import sqlmodel as sm
from pydantic import EmailStr

from service.database.mixins.metadata import CreatedAtMixin, UpdatedAtMixin
from service.database.mixins.primary_keys import PkUuidMixin
from service.database.models.base import SqlModelBase


class Attorney(SqlModelBase, PkUuidMixin, CreatedAtMixin, UpdatedAtMixin, table=True):
    __tablename__ = 'attorneys'

    email: EmailStr = sm.Field(sa_type=sa.String(), index=True, unique=True)
    is_active: bool = sm.Field(sa_type=sa.Boolean(), nullable=True, default=True)
