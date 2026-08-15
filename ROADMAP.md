# LunarPhaseORM Roadmap

This document outlines the development roadmap, timeline matrix, and future milestones for **LunarPhaseORM**.

> [!NOTE]
> **Disclaimer & Research Flexibility**: This roadmap is a living document. Target timelines, planned features, and release milestones are subject to change over time based on ongoing research, architectural benchmarks, database driver evolutions, and community feedback.

---

## 📅 Timeline & Status Overview

```
2026                                                              2027
May - Jun               Jul - Aug           Sep - Oct           Nov - Dec           Jan - Feb
[=== Phases 1 - 2 ===]>[=== Phases 3 - 5 =]>[=== Phase 6 ===]--->[=== Phase 7 ===]--->[=== Phase 8 - 9 ===]
  (Core & AST            (Auto-Batching,     (Rust Drivers &     (Advanced Queries   (FastAPI Integration
   Query Compiler)        UoW, CLI Migr.)     Connection Pool)    & JSON Path)        & v1.0.0 Release)
```

---

## Core Roadmap Matrix (Blueprint Phases 1 - 5)

| Phase | Core Module | Deliverables & Features | Timeline / Target Status |
|---|---|---|---|
| **Phase 1** | **Core Descriptors & AST** | Metaclass parsing (`ModelBase`), `FieldDescriptor`, operator overloading (`==`, `!=`, `>`, `<`, `in_`, `like`, etc.), AST Query Compiler for SQLite. | ✅ **SELESAI** *(Start: Mei 2026 - Done: Juni 2026)* |
| **Phase 2** | **Async Drivers & Query Chaining** | Multi-driver engine abstraction (`aiosqlite`, `asyncpg`, `aiomysql`), fluent query chaining API (`where()`, `or_where()`, `limit()`, `offset()`, `order_by()`, `count()`, `exists()`, `paginate()`). | ✅ **SELESAI** *(Start: Juni 2026 - Done: Juli 2026)* |
| **Phase 3** | **Auto-Batching & Relations** | N+1 Query Resolver via `DeferredAutoBatcher` micro-task event loop flushing (`loop.call_soon()`), relational descriptors `HasMany`, `BelongsTo`, `HasOne`, and eager loading (`with_relations()`). | ✅ **SELESAI** *(Start: Juli 2026 - Done: Juli 2026)* |
| **Phase 4** | **Dirty Tracking & Unit of Work** | Rust-accelerated `StateTracker` Snapshot Isolation diffing, precise `UPDATE` execution (modifying only dirty columns), `IdentityMap`, and atomic `UnitOfWork` session transaction manager with automatic rollback. | ✅ **SELESAI** *(Start: Juli 2026 - Done: Agustus 2026)* |
| **Phase 5** | **CLI Auto-Migration System** | Real-time Python Model AST vs Database Schema comparison via Rust `SchemaDiffEngine`, auto-generating reversible `upgrade()` and `downgrade()` DDL scripts, and terminal CLI tool (`lunarphase`). | ✅ **SELESAI** *(Start: Agustus 2026 - Done: Agustus 2026)* |

---

## Future Roadmap & Beyond (v0.2.0 - v1.0.0+)

### 🔷 Phase 6: Advanced Connection Pooling & Native Rust Drivers (v0.2.0)
- **Target Timeline**: September 2026 – Oktober 2026 *(1.5 - 2 Bulan)*
- [ ] Native Rust PostgreSQL driver binding (`tokio-postgres` / `sqlx`) directly inside `_lunarphase_rs`.
- [ ] Built-in connection pool manager with dynamic scaling, health checks, and reconnect backoff.
- [ ] Read/Write replica routing support.

### 🔷 Phase 7: Advanced Query Operators & JSON Aggregations (v0.3.0)
- **Target Timeline**: November 2026 – Desember 2026 *(1 - 1.5 Bulan)*
- [ ] Complex SQL constructs: `GROUP BY`, `HAVING`, `UNION`, `INTERSECT`, and CTEs (`WITH` clauses).
- [ ] JSON path query operators (`JSON_EXTRACT`, JSON arrow `->` operators) in Rust query compiler.
- [ ] Subqueries and raw SQL expression blending.

### 🔷 Phase 8: Web Framework Integrations & Middlewares (v0.4.0)
- **Target Timeline**: Januari 2027 *(1 Bulan)*
- [ ] Official `lunarphase-fastapi` middleware providing request-scoped `UnitOfWork` sessions.
- [ ] Integrations for **Litestar**, **Sanic**, and **Starlette**.
- [ ] Pydantic v2 automatic schema generation from `Model` classes (`Model.to_pydantic()`).

### 🔷 Phase 9: High-Scale SIMD Acceleration & Benchmark Suite (v1.0.0 STABLE)
- **Target Timeline**: Februari 2027 – Maret 2027 *(1 - 1.5 Bulan)*
- [ ] SIMD-accelerated JSON deserialization via `simd-json` in Rust core.
- [ ] Zero-copy binary row parsing for extreme throughput.
- [ ] Comprehensive comparative benchmark suite published on GitHub Actions CI.

---

## 🤝 Contributing

We welcome community feedback and contributions! If you have feature requests or proposals for future phases, please open an issue or pull request on GitHub.
