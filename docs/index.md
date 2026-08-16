# Technical Manual — LunarPhaseORM

LunarPhaseORM is an async-first Object-Relational Mapping (ORM) framework for Python 3.9+ accelerated by a native C-extension compiled from Rust (`_lunarphase_rs`).

The framework combines an Active Record interface (`model.save()`, `Model.create()`) with a Data Mapper architecture utilizing a Unit of Work transaction engine, an Identity Map, and an event-loop micro-task queue for relationship batching.

---

## Technical Overview

```
+-------------------------------------------------------------------+
|                        Python Application                         |
|  - Async Engine Driver (aiosqlite / asyncpg / aiomysql)           |
|  - Model Classes (ModelBase Metaclass & Field Descriptors)        |
|  - Identity Map & UnitOfWork Transaction Management               |
|  - DeferredAutoBatcher Micro-Task Loop Scheduler                  |
+-------------------------------------------------------------------+
                                 │
           PyO3 / C-API FFI Boundary (abi3-py39)
                                 │
                                 ▼
+-------------------------------------------------------------------+
|               Native Rust Extension (_lunarphase_rs)              |
|  - StateTracker (FxHashMap<String, FieldEntry> Snapshot)          |
|  - BatchAggregator (FxHashSet<i64> & FxHashSet<String>)           |
|  - QueryCompiler (Pre-allocated String Buffers & Dialects)        |
|  - SchemaDiffEngine (Model vs Database DDL Comparison)            |
+-------------------------------------------------------------------+
```

---

## Architectural Objectives

1. **Memory Allocation Efficiency**: Model snapshot tracking and dirty field comparisons are offloaded to C-contiguous Rust memory structures (`FxHashMap`), avoiding per-instance Python dictionary graph creation.
2. **N+1 Query Resolution**: Relationship queries are deferred and batched into single `WHERE id IN (...)` operations via `asyncio.get_running_loop().call_soon()`.
3. **Selective Field Updates**: Dirty attribute tracking ensures SQL `UPDATE` statements format only fields modified since the last snapshot hydration.
4. **C-API Compatibility**: Rust modules are compiled using standard `PyO3` bindings under Python C-API ABI3 specifications (`cp39-abi3`), enabling binary wheel execution across CPython 3.9 through 3.14+.

---

## Module Breakdown

| Module Path | Primary Responsibility | Core Classes / Types |
|---|---|---|
| [`lunarphase.core.model`](models-and-fields.md) | Metaclass attribute registration and Active Record API | `ModelBase`, `Model` |
| [`lunarphase.core.fields`](models-and-fields.md) | Attribute descriptors and AST expression construction | `FieldDescriptor`, `PrimaryKeyField`, `StringField`, `IntegerField` |
| [`lunarphase.core.state`](architecture.md) | Snapshot management and dirty field identification | `StateTracker` (Rust bridge), `PyStateTracker` (Fallback) |
| [`lunarphase.query.builder`](query-builder.md) | AST compilation and parameter binding | `QueryBuilder`, `ColumnRef`, `BinaryOp` |
| [`lunarphase.query.batcher`](relations-and-batching.md) | Event loop micro-task batching scheduler | `DeferredAutoBatcher`, `BatchAggregator` |
| [`lunarphase.core.uow`](unit-of-work.md) | Transaction boundaries and identity mapping | `UnitOfWork`, `IdentityMap` |
| [`lunarphase.migrations`](migrations-cli.md) | Schema extraction, diffing, and CLI execution | `SchemaDiffEngine`, `MigrationRunner`, `CLI` |
