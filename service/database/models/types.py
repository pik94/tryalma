import enum
import logging
from typing import Type

import sqlalchemy as sa


logger = logging.getLogger(__name__)


class EnumString(sa.types.TypeDecorator):
    impl = sa.String()
    enum_type_class: Type[enum.Enum]

    def process_bind_param(self, value, dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.lower()
        raise TypeError(f'Type must be str but actual type is {type(value)}')

    def process_result_value(self, value: str | None, dialect) -> enum.Enum | None:
        if value is None:
            return None
        try:
            return self.enum_type_class(value)
        except Exception as e:
            logger.error(f'Failed to parse status {value} from db because of {e}. Set to None')
            status = None

        return status
