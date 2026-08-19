"""
LunarPhaseORM: Smart, Async-Native, High-Performance Python & Rust Object-Relational Mapper
"""

from __future__ import annotations

from lunarphase.core.model import Model, ModelBase
from lunarphase.core.fields import (
    FieldDescriptor,
    PrimaryKeyField,
    IntegerField,
    StringField,
    FloatField,
    BooleanField,
    DateTimeField,
    JSONField,
)
from lunarphase.core.relations import HasMany, BelongsTo, HasOne
from lunarphase.core.uow import UnitOfWork, IdentityMap
from lunarphase.db.engine import create_engine, set_engine, get_engine, SQLiteEngine
from lunarphase.query.builder import QueryBuilder
from lunarphase.query.batcher import DeferredAutoBatcher
from lunarphase.migrations.runner import MigrationRunner

__version__ = "0.1.3"
__all__ = [
    "Model",
    "ModelBase",
    "FieldDescriptor",
    "PrimaryKeyField",
    "IntegerField",
    "StringField",
    "FloatField",
    "BooleanField",
    "DateTimeField",
    "JSONField",
    "HasMany",
    "BelongsTo",
    "HasOne",
    "UnitOfWork",
    "IdentityMap",
    "create_engine",
    "set_engine",
    "get_engine",
    "SQLiteEngine",
    "QueryBuilder",
    "DeferredAutoBatcher",
    "MigrationRunner",
]
