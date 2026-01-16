import uuid

from pydantic import BaseModel
import sqlmodel as sm


class PkUuidMixin(BaseModel):
    id: uuid.UUID = sm.Field(primary_key=True)


class PkIncrementalIdMixin(BaseModel):
    id: int | None = sm.Field(
        default=None,
        primary_key=True,
        description='Autoincrementing integer primary key',
    )
