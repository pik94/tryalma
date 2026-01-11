import datetime as dt

import sqlalchemy as sa
import sqlmodel as sm

from service.utils.date_utils import get_utc_now


class CreatedAtMixin:
    created_at: dt.datetime = sm.Field(
        sa_type=sa.DateTime(timezone=True),
        default_factory=get_utc_now,
        sa_column_kwargs={'server_default': sa.func.now()},
        nullable=False,
        index=False,
    )


class UpdatedAtMixin:
    updated_at: dt.datetime = sm.Field(
        sa_type=sa.DateTime(timezone=True),
        default_factory=get_utc_now,
        sa_column_kwargs={'server_default': sa.func.now()},
        nullable=False,
        index=False,
    )


class DeletedAtMixin:
    deleted_at: dt.datetime | None = sm.Field(
        sa_type=sa.DateTime(timezone=True),
        nullable=True,
        index=False,
        default=None,
    )
