from typing import Any, Dict, List, Optional, Set, Tuple, Type
from lunarphase.db.engine import get_engine, DatabaseEngine

class IdentityMap:
    """Identity Map pattern ensuring single in-memory instance per DB row."""
    def __init__(self):
        self._map: Dict[Tuple[Type[Any], Any], Any] = {}

    def get(self, model_cls: Type[Any], pk: Any) -> Optional[Any]:
        return self._map.get((model_cls, pk))

    def register(self, instance: Any):
        pk_name = instance._primary_key_name
        pk_val = getattr(instance, pk_name, None)
        if pk_val is not None:
            self._map[(instance.__class__, pk_val)] = instance

    def remove(self, instance: Any):
        pk_name = instance._primary_key_name
        pk_val = getattr(instance, pk_name, None)
        if pk_val is not None:
            self._map.pop((instance.__class__, pk_val), None)

    def clear(self):
        self._map.clear()


class UnitOfWork:
    """Unit of Work & Session transaction manager."""
    def __init__(self, engine: Optional[DatabaseEngine] = None):
        self.engine = engine or get_engine()
        self.identity_map = IdentityMap()
        self.new_objects: Set[Any] = set()
        self.dirty_objects: Set[Any] = set()
        self.deleted_objects: Set[Any] = set()
        self._in_transaction = False

    def register_new(self, instance: Any):
        self.new_objects.add(instance)

    def register_dirty(self, instance: Any):
        if instance not in self.new_objects:
            self.dirty_objects.add(instance)

    def register_deleted(self, instance: Any):
        if instance in self.new_objects:
            self.new_objects.remove(instance)
        else:
            self.deleted_objects.add(instance)

    async def commit(self):
        """Flushes all changes atomically."""
        # Save new objects
        for obj in list(self.new_objects):
            await obj.save()
            self.identity_map.register(obj)

        # Save dirty objects
        for obj in list(self.dirty_objects):
            if obj.is_dirty:
                await obj.save()

        # Delete objects
        for obj in list(self.deleted_objects):
            await obj.delete()
            self.identity_map.remove(obj)

        self.clear()

    async def rollback(self):
        """Rolls back all uncommitted tracking state."""
        self.clear()

    def clear(self):
        self.new_objects.clear()
        self.dirty_objects.clear()
        self.deleted_objects.clear()

    def begin(self):
        return SessionTransactionContext(self)


class SessionTransactionContext:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def __aenter__(self):
        self.uow._in_transaction = True
        return self.uow

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.uow.rollback()
            return False # Re-raise exception
        else:
            await self.uow.commit()
            return True
