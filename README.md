<div align="center">
  <img width="220" height="220" alt="LunarPhaseORM logo" src="https://github.com/user-attachments/assets/32b24c36-eb89-4736-b288-9745280f78c5" />

  # 🌖 LunarPhaseORM

  > **Smart Sync. Zero N+1. High-Performance Python & Rust ORM.**

  [![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
  [![Rust Engine](https://img.shields.io/badge/core-Rust%20%2F%20PyO3-orange.svg)](https://www.rust-lang.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)](tests)

</div>

---

**LunarPhaseORM** is an async-first Object-Relational Mapper built for high-throughput applications where database performance and memory efficiency matter. It combines the developer ergonomics of **Active Record** (`user.save()`) with the safety of **Data Mapper & Unit of Work**, accelerated by a native **Rust core (`PyO3`/`maturin`)**.

---

## ✨ Key Features

- 🦀 **Rust-Powered Performance**: Offloads snapshot isolation state tracking, dirty diffing, AST compilation, and schema diffing to C-level Rust structs (`_lunarphase_rs`), drastically reducing Python RAM overhead.
- ⚡ **Zero N+1 Query Problem**: Solves N+1 query issues automatically via `asyncio` event loop micro-task flushing (`DeferredAutoBatcher`). Relation access inside loops is automatically batched into single `WHERE id IN (...)` queries.
- 🎯 **Precise Dirty Tracking**: Computes dirty attribute diffs in Rust. Calling `await user.save()` executes SQL `UPDATE` only on modified columns, and skips database I/O completely if no fields were altered.
- 🛡️ **Type-Safe Query Builder**: Fluent API with native Python operator overloading (`User.age > 18`) producing AST query nodes cleanly.
- 🔄 **Unit of Work & Session Transactions**: Guarantees object identity via `IdentityMap` and provides atomic transaction blocks (`async with session.begin()`) with automatic rollback on failure.
- 🛠 **CLI Auto-Migration System**: Automated database schema diffing and reversible DDL script generation (`lunarphase make:migration`, `migrate`, `rollback`, `status`).

---

## 📦 Installation

Install LunarPhaseORM from PyPI:

```bash
pip install lunarphase-orm
```

Or build locally with **Maturin**:

```bash
git clone https://github.com/LunarPy-Labs/LunarPhaseORM.git
cd LunarPhaseORM
python3 -m venv .venv
source .venv/bin/activate
pip install maturin aiosqlite pydantic
maturin develop
```

---

## ⚡ Quick Start

```python
import asyncio
from lunarphase import (
    Model,
    PrimaryKeyField,
    StringField,
    IntegerField,
    HasMany,
    BelongsTo,
    create_engine,
    UnitOfWork,
)

# 1. Define Models
class Author(Model):
    __tablename__ = "authors"
    id = PrimaryKeyField()
    name = StringField()
    posts = HasMany(lambda: Post, foreign_key="author_id")

class Post(Model):
    __tablename__ = "posts"
    id = PrimaryKeyField()
    title = StringField()
    author_id = IntegerField()
    author = BelongsTo(Author, foreign_key="author_id")

async def main():
    # 2. Connect Database Engine (SQLite, Postgres, MySQL)
    engine = create_engine("sqlite:///:memory:")

    # Setup Tables
    await engine.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255));")
    await engine.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(255), author_id INTEGER);")

    # 3. Create Record
    author = await Author.create(name="Arthur Conan Doyle")

    # 4. Create Related Record
    await Post.create(title="A Study in Scarlet", author_id=author.id)
    await Post.create(title="The Sign of the Four", author_id=author.id)

    # 5. Access Relations (Zero N+1 Query Problem!)
    fetched_author = await Author.where(name="Arthur Conan Doyle").first()
    posts = await fetched_author.posts
    print(f"Author: {fetched_author.name}")
    for p in posts:
        print(f" - Post: {p.title}")

    # 6. Precise Dirty Tracking Update
    fetched_author.name = "Sir Arthur Conan Doyle"
    await fetched_author.save() # Updates ONLY 'name' column in SQL!

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Comparison Matrix

| Feature | 🌖 LunarPhaseORM | 🐍 SQLAlchemy (v2.0) | 🐢 Tortoise ORM |
|---|---|---|---|
| **Primary Architecture** | **Hybrid** (AR + Data Mapper) | Data Mapper | Active Record |
| **State Storage & RAM** | 🟢 **Rust Core (`_lunarphase_rs`)** | 🔴 Heavy Python Object Graph | 🟡 Python Dict |
| **N+1 Query Resolution** | 🟢 **Automatic (Zero N+1 Engine)** | 🟡 Manual (`joinedload`) | 🟡 Manual (`prefetch`) |
| **Dirty Attribute Diffing** | 🟢 **Rust Snapshot Isolation** | 🟢 Unit of Work History | 🔴 Basic re-save |
| **SQL Query Compilation** | 🟢 **Rust AST Compiler** | 🟡 Python AST | 🟡 PyPika |
| **Async Support** | Native Async First | Async Extension | Native Async |

---

## 🛠 CLI Migration Commands

LunarPhaseORM includes a command-line tool for managing schema migrations:

```bash
# Check migration status
lunarphase status

# Generate a new DDL schema migration file
lunarphase make:migration "create_users_table"

# Apply pending migrations
lunarphase migrate

# Rollback last migration
lunarphase rollback
```

---

## 📖 Full Documentation

For in-depth technical documentation, API references, and advanced usage patterns, read [DOCUMENTATION.md](DOCUMENTATION.md).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
