from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, Union
import asyncio
from lunarphase.query.batcher import DeferredAutoBatcher

class RelationDescriptor:
    def __init__(self, target_model_getter: Any, foreign_key: Optional[str] = None):
        self._target_model_raw = target_model_getter
        self.foreign_key = foreign_key
        self.name = ""
        self.owner_class = None

    def __set_name__(self, owner, name: str):
        self.name = name
        self.owner_class = owner

    @property
    def target_model(self) -> Type[Any]:
        if callable(self._target_model_raw) and not isinstance(self._target_model_raw, type):
            return self._target_model_raw()
        return self._target_model_raw


class HasMany(RelationDescriptor):
    def __init__(self, target_model_getter: Any, foreign_key: Optional[str] = None):
        super().__init__(target_model_getter, foreign_key)
        self._batcher: Optional[DeferredAutoBatcher] = None

    def _get_batcher(self) -> DeferredAutoBatcher:
        if self._batcher is None:
            fk = self.foreign_key or f"{self.owner_class.__name__.lower()}_id"

            async def fetch_batch(keys: List[Any]) -> Dict[Any, List[Any]]:
                target_cls = self.target_model
                # Batch query: SELECT * FROM target_table WHERE fk IN (1, 2, 3...)
                records = await target_cls.where(**{f"{fk}__in": keys} if hasattr(target_cls, "where") else {}).all()
                grouped: Dict[Any, List[Any]] = {k: [] for k in keys}
                for rec in records:
                    owner_id = getattr(rec, fk, None)
                    if owner_id in grouped:
                        grouped[owner_id].append(rec)
                return grouped

            self._batcher = DeferredAutoBatcher(fetch_batch)
        return self._batcher

    def __get__(self, instance, owner):
        if instance is None:
            return self

        fk = self.foreign_key or f"{owner.__name__.lower()}_id"
        owner_pk = getattr(instance, owner._primary_key_name, None)
        if owner_pk is None:
            async def empty():
                return []
            return empty()

        target_cls = self.target_model
        return target_cls.where(**{fk: owner_pk}).all()

    async def eager_load(self, instances: List[Any]):
        if not instances:
            return
        owner_cls = instances[0].__class__
        fk = self.foreign_key or f"{owner_cls.__name__.lower()}_id"
        owner_ids = [getattr(inst, owner_cls._primary_key_name) for inst in instances if getattr(inst, owner_cls._primary_key_name, None) is not None]

        target_cls = self.target_model
        related_records = await target_cls.where(**{f"{fk}__in": owner_ids} if hasattr(target_cls, "where") else {}).all()

        grouped = {id_val: [] for id_val in owner_ids}
        for rec in related_records:
            owner_id = getattr(rec, fk, None)
            if owner_id in grouped:
                grouped[owner_id].append(rec)

        for inst in instances:
            pk = getattr(inst, owner_cls._primary_key_name, None)
            setattr(inst, f"_{self.name}_cached", grouped.get(pk, []))


class BelongsTo(RelationDescriptor):
    def __init__(self, target_model_getter: Any, foreign_key: Optional[str] = None):
        super().__init__(target_model_getter, foreign_key)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        target_cls = self.target_model
        fk = self.foreign_key or f"{target_cls.__name__.lower()}_id"
        fk_val = getattr(instance, fk, None)
        if fk_val is None:
            async def empty():
                return None
            return empty()

        return target_cls.where(**{target_cls._primary_key_name: fk_val}).first()


class HasOne(RelationDescriptor):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        fk = self.foreign_key or f"{owner.__name__.lower()}_id"
        owner_pk = getattr(instance, owner._primary_key_name, None)
        if owner_pk is None:
            async def empty():
                return None
            return empty()

        target_cls = self.target_model
        return target_cls.where(**{fk: owner_pk}).first()
