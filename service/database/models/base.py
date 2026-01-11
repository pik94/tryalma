from typing import ClassVar

import sqlalchemy as sa
import sqlmodel as sm


metadata = sa.MetaData()


class SqlModelBase(sm.SQLModel):
    metadata = metadata

    show_fields: ClassVar[tuple[str, ...]] = ()

    def __repr__(self) -> str:
        fields = ', '.join(f'{f}={getattr(self, f)!r}' for f in self.show_fields if hasattr(self, f))
        return f'{self.__class__.__name__}({fields})'

    __str__ = __repr__
