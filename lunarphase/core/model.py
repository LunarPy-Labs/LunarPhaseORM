from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Type, TypeVar
from lunarphase.core.fields import FieldDescriptor, PrimaryKeyField
from lunarphase.core.state import create_state_tracker
from lunarphase.db.engine import get_engine
from lunarphase.query.builder import QueryBuilder

try:
    from lunarphase._lunarphase_rs import QueryCompiler as RustQueryCompiler
    HAS_RUST_COMPILER = True
except ImportError:
    HAS_RUST_COMPILER = False

M = TypeVar("M", bound="Model")

class ModelBase(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict):
        fields: Dict[str, FieldDescriptor] = {}
        primary_key_name = "id"

        # Inherit fields from parent base classes
        for base in bases:
            if hasattr(base, "_fields"):
                fields.update(base._fields)

        # Collect fields from current class attrs
        for k, v in list(attrs.items()):
            if isinstance(v, FieldDescriptor):
                v.name = k
                fields[k] = v
                if v.primary_key:
                    primary_key_name = k

        # If no primary key declared, add default PrimaryKeyField 'id'
        if primary_key_name not in fields and name != "Model":
            pk_field = PrimaryKeyField("id")
            pk_field.name = "id"
            fields["id"] = pk_field
            attrs["id"] = pk_field
            primary_key_name = "id"

        attrs["_fields"] = fields
        attrs["_primary_key_name"] = primary_key_name

        if "__tablename__" not in attrs and name != "Model":
            attrs["__tablename__"] = f"{name.lower()}s"

        new_cls = super().__new__(cls, name, bases, attrs)

        # Bind owner class to descriptors
        for field in fields.values():
            field.owner_class = new_cls

        return new_cls


class Model(metaclass=ModelBase):
    _fields: Dict[str, FieldDescriptor]
    _primary_key_name: str
    __tablename__: str

    def __init__(self, **kwargs: Any):
        self._state = create_state_tracker()
        initial_data = {}

        for name, field in self._fields.items():
            val = kwargs.get(name, field.default)
            initial_data[name] = val

        self._state.set_initial_state(initial_data)

    @property
    def is_dirty(self) -> bool:
        return self._state.is_dirty()

    def get_dirty_changes(self) -> Dict[str, Any]:
        return self._state.get_dirty_changes()

    def _hydrate_snapshot(self):
        self._state.hydrate_snapshot()

    @classmethod
    def hydrate(cls: Type[M], row: Dict[str, Any]) -> M:
        instance = cls.__new__(cls)
        instance._state = create_state_tracker()
        instance._state.set_initial_state(row)
        return instance

    @classmethod
    def query(cls: Type[M]) -> QueryBuilder[M]:
        return QueryBuilder(cls)

    @classmethod
    def where(cls: Type[M], *conditions: Any, **kwargs: Any) -> QueryBuilder[M]:
        return QueryBuilder(cls).where(*conditions, **kwargs)

    @classmethod
    def all(cls: Type[M]):
        return QueryBuilder(cls).all()

    @classmethod
    def first(cls: Type[M]):
        return QueryBuilder(cls).first()

    @classmethod
    async def create(cls: Type[M], **kwargs: Any) -> M:
        instance = cls(**kwargs)
        await instance.save()
        return instance

    async def save(self) -> bool:
        engine = get_engine()
        pk_name = self._primary_key_name
        pk_val = getattr(self, pk_name, None)

        # Case 1: New record (INSERT)
        if pk_val is None:
            data = self._state.get_current_dict()
            if pk_name in data and data[pk_name] is None:
                del data[pk_name]

            cols = list(data.keys())
            vals = [data[c] for c in cols]

            if HAS_RUST_COMPILER:
                compiler = RustQueryCompiler()
                sql = compiler.compile_insert(self.__tablename__, cols, engine.dialect)
            else:
                ph = ", ".join(["?"] * len(cols))
                sql = f"INSERT INTO {self.__tablename__} ({', '.join(cols)}) VALUES ({ph})"

            last_id = await engine.execute_insert(sql, tuple(vals))
            if last_id and pk_name in self._fields:
                setattr(self, pk_name, last_id)
            self._hydrate_snapshot()
            return True

        # Case 2: Existing record (UPDATE dirty fields only)
        if not self.is_dirty:
            return False # Zero unnecessary SQL execution

        changes = self.get_dirty_changes()
        if not changes:
            return False

        cols = list(changes.keys())
        vals = [changes[c] for c in cols]
        vals.append(pk_val) # Primary key parameter for WHERE clause

        if HAS_RUST_COMPILER:
            compiler = RustQueryCompiler()
            sql = compiler.compile_update(self.__tablename__, cols, pk_name, engine.dialect)
        else:
            set_str = ", ".join([f"{c} = ?" for c in cols])
            sql = f"UPDATE {self.__tablename__} SET {set_str} WHERE {pk_name} = ?"

        await engine.execute(sql, tuple(vals))
        self._hydrate_snapshot()
        return True

    async def delete(self) -> bool:
        engine = get_engine()
        pk_name = self._primary_key_name
        pk_val = getattr(self, pk_name, None)
        if pk_val is None:
            return False

        if HAS_RUST_COMPILER:
            compiler = RustQueryCompiler()
            sql = compiler.compile_delete(self.__tablename__, pk_name, engine.dialect)
        else:
            sql = f"DELETE FROM {self.__tablename__} WHERE {pk_name} = ?"

        await engine.execute(sql, (pk_val,))
        return True

    def __repr__(self) -> str:
        pk_val = getattr(self, self._primary_key_name, None)
        return f"<{self.__class__.__name__} id={pk_val}>"
