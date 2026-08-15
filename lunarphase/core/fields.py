from typing import Any, Optional, Dict
from lunarphase.core.ast import ColumnRef, Literal, BinaryOp

class FieldDescriptor:
    def __init__(
        self,
        name: Optional[str] = None,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        data_type: str = "TEXT",
    ):
        self.name = name
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.data_type = data_type
        self.owner_class = None

    def __set_name__(self, owner, name: str):
        if not self.name:
            self.name = name
        self.owner_class = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._state.get_field(self.name)

    def __set__(self, instance, value):
        if instance is None:
            return
        instance._state.set_field(self.name, value)

    # Operator overloading for AST query generation
    def _col_ref(self) -> ColumnRef:
        table_name = getattr(self.owner_class, "__tablename__", None) if self.owner_class else None
        return ColumnRef(self.name, table_name)

    def __eq__(self, other: Any) -> BinaryOp:
        if other is None:
            return BinaryOp(self._col_ref(), "IS", Literal(None))
        return BinaryOp(self._col_ref(), "=", Literal(other))

    def __ne__(self, other: Any) -> BinaryOp:
        if other is None:
            return BinaryOp(self._col_ref(), "IS NOT", Literal(None))
        return BinaryOp(self._col_ref(), "!=", Literal(other))

    def __lt__(self, other: Any) -> BinaryOp:
        return BinaryOp(self._col_ref(), "<", Literal(other))

    def __le__(self, other: Any) -> BinaryOp:
        return BinaryOp(self._col_ref(), "<=", Literal(other))

    def __gt__(self, other: Any) -> BinaryOp:
        return BinaryOp(self._col_ref(), ">", Literal(other))

    def __ge__(self, other: Any) -> BinaryOp:
        return BinaryOp(self._col_ref(), ">=", Literal(other))

    def in_(self, values: list) -> BinaryOp:
        return BinaryOp(self._col_ref(), "IN", Literal(values))

    def like(self, pattern: str) -> BinaryOp:
        return BinaryOp(self._col_ref(), "LIKE", Literal(pattern))

    def is_null(self) -> BinaryOp:
        return BinaryOp(self._col_ref(), "IS", Literal(None))

    def is_not_null(self) -> BinaryOp:
        return BinaryOp(self._col_ref(), "IS NOT", Literal(None))


class PrimaryKeyField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, auto_increment: bool = True):
        super().__init__(name=name, primary_key=True, nullable=False, data_type="INTEGER")
        self.auto_increment = auto_increment


class IntegerField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, primary_key: bool = False, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=primary_key, nullable=nullable, default=default, data_type="INTEGER")


class StringField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, primary_key: bool = False, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=primary_key, nullable=nullable, default=default, data_type="VARCHAR(255)")


class FloatField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, primary_key: bool = False, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=primary_key, nullable=nullable, default=default, data_type="REAL")


class BooleanField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, primary_key: bool = False, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=primary_key, nullable=nullable, default=default, data_type="BOOLEAN")


class DateTimeField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, primary_key: bool = False, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=primary_key, nullable=nullable, default=default, data_type="DATETIME")


class JSONField(FieldDescriptor):
    def __init__(self, name: Optional[str] = None, nullable: bool = True, default: Any = None):
        super().__init__(name=name, primary_key=False, nullable=nullable, default=default, data_type="JSON")
