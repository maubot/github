# Based on https://docs.sqlalchemy.org/en/13/core/custom_types.html#backend-agnostic-guid-type
from typing import Union, Optional, Type, Any

from sqlalchemy import types
from sqlalchemy.dialects import postgresql
import uuid

InputUUID = Union[uuid.UUID, str, None]


class UUIDType(types.TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """

    impl = types.CHAR

    @property
    def python_type(self) -> Type[uuid.UUID]:
        return uuid.UUID

    def process_literal_param(self, value: InputUUID, dialect: Any) -> Optional[str]:
        raise NotImplementedError()

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(types.CHAR(32))

    def process_bind_param(self, value: InputUUID, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        elif dialect.name == "postgresql":
            return str(value)
        elif not isinstance(value, uuid.UUID):
            return uuid.UUID(value).hex
        return value.hex

    def process_result_value(self, value: InputUUID, dialect: Any) -> Optional[uuid.UUID]:
        if value is not None and not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value
