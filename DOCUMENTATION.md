# 🌖 LunarPhaseORM Documentation

Welcome to the official technical documentation for **LunarPhaseORM** — a high-performance, async-first Python Object-Relational Mapper (ORM) powered by a Rust core (`PyO3`/`maturin`) for low RAM footprint, zero N+1 queries, and instant AST query compilation.

---

## 📋 Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Installation & Setup](#2-installation--setup)
3. [Defining Models & Fields](#3-defining-models--fields)
4. [Dirty Tracking System (Snapshot Isolation)](#4-dirty-tracking-system-snapshot-isolation)
5. [Type-Safe Query Builder API](#5-type-safe-query-builder-api)
6. [Relationships & Auto-Batching Engine (Zero N+1 Query)](#6-relationships--auto-batching-engine-zero-n1-query)
7. [Unit of Work & Session Transactions](#7-unit-of-work--session-transactions)
8. [CLI Auto-Migration System](#8-cli-auto-migration-system)
9. [Rust Core Engine & Performa Benchmarks](#9-rust-core-engine--performa-benchmarks)
10. [Complete End-to-End Example](#10-complete-end-to-end-example)

---

## 1. Overview & Architecture

LunarPhaseORM combines the developer ergonomics of the **Active Record** pattern (`user.save()`, `User.create()`) with the safety and strict state isolation of **Data Mapper & Unit of Work**.

### 🏗 Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            DEVELOPER API LAYER                                    |
|   Active Record (user.save()) | Type-Safe Query Builder | UoW & Transaction Session   |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                     CORE RUST ENGINE (_lunarphase_rs)                              |
|   +------------------------------------+  +------------------------------------+  |
|   |  Rust StateTracker & Dirty Diff    |  |  Rust AST Compiler & Dialects      |  |
|   |  - Compact Snapshot Allocation     |  |  - SQLite (aiosqlite)              |  |
|   |  - Zero-overhead Diffing           |  |  - Postgres (asyncpg)              |  |
|   |                                    |  |  - MySQL (aiomysql)                |  |
|   +------------------------------------+  +------------------------------------+  |
|   +----------------------------------------------------------------------------+  |
|   |  Rust Auto-Batch Aggregator & Schema Diff Engine                           |  |
|   +----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                           DEFERRED MICRO-TASK FLUSH                               |
|   - N+1 Query Resolver using asyncio.Event & loop.call_soon()                     |
|   - HasMany / BelongsTo / HasOne relation automatic batching                      |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                        ASYNC DATABASE DRIVER LAYER                                |
|           aiosqlite (SQLite) | asyncpg (PostgreSQL) | aiomysql (MySQL)            |
+-----------------------------------------------------------------------------------+
```

---

## 2. Installation & Setup

### Requirements
- Python `>= 3.9`
- Rust / Cargo (for building native extension via Maturin)

### Installation

```bash
pip install lunarphase-orm
```

Or install in development mode from source:

```bash
git clone https://github.com/LunarPy-Labs/LunarPhaseORM.git
cd LunarPhaseORM
python3 -m venv .venv
source .venv/bin/activate
pip install maturin pytest pytest-cov aiosqlite
maturin develop
```

### Initializing Database Connection

```python
from lunarphase import create_engine

# SQLite (In-Memory or File)
engine = create_engine("sqlite:///app.db")

# PostgreSQL
# engine = create_engine("postgresql://user:password@localhost:5432/dbname")

# MySQL
# engine = create_engine("mysql://user:password@localhost:3306/dbname")
```

---

## 3. Defining Models & Fields

Models are defined by inheriting from `lunarphase.Model`. Fields are declared using `FieldDescriptor` classes.

```python
from lunarphase import (
    Model,
    PrimaryKeyField,
    StringField,
    IntegerField,
    BooleanField,
    DateTimeField,
    JSONField,
)

class User(Model):
    __tablename__ = "users"

    id = PrimaryKeyField()
    name = StringField(nullable=False)
    email = StringField(nullable=False)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)
    created_at = DateTimeField()
    metadata = JSONField(default=dict)
```

### Field Types

| Field Type | Python Type | Default SQL Type | Description |
|---|---|---|---|
| `PrimaryKeyField` | `int` | `INTEGER PRIMARY KEY` | Auto-incrementing primary key |
| `StringField` | `str` | `VARCHAR(255)` | Text / String column |
| `IntegerField` | `int` | `INTEGER` | Integer numeric column |
| `FloatField` | `float` | `REAL` | Floating point column |
| `BooleanField` | `bool` | `BOOLEAN` | True/False column |
| `DateTimeField` | `datetime` / `str` | `DATETIME` | Date and time column |
| `JSONField` | `dict` / `list` | `JSON` | Serialized JSON data column |

### Operator Overloading

Field descriptors overload Python comparison operators to generate type-safe AST query conditions:

```python
User.age > 21             # WHERE age > 21
User.name == "Alice"      # WHERE name = 'Alice'
User.email.like("%@gmail")# WHERE email LIKE '%@gmail'
User.age.in_([18, 19, 20])# WHERE age IN (18, 19, 20)
User.name.is_null()       # WHERE name IS NULL
```

---

## 4. Dirty Tracking System (Snapshot Isolation)

LunarPhaseORM applies the **Snapshot Isolation Pattern** backed by the Rust `StateTracker` struct (`src/state_tracker.rs`).

- When a model instance is fetched from DB or hydrated, an initial state snapshot `_state_snapshot` is stored.
- Property modifications update `_state_current`.
- Calling `user.save()` computes the diff in Rust and executes an `UPDATE` query **only containing changed columns**.
- If no fields were modified, `await user.save()` returns `False` and **skips SQL execution completely**.

```python
user = await User.where(id=1).first()

# Checking dirty status
print(user.is_dirty) # False

user.age = 25
print(user.is_dirty) # True
print(user.get_dirty_changes()) # {'age': 25}

# Only updates 'age' in SQL: UPDATE users SET age = ? WHERE id = 1
saved = await user.save()
print(saved) # True
print(user.is_dirty) # False
```

---

## 5. Type-Safe Query Builder API

`QueryBuilder` provides fluent async query construction:

```python
# Select specific columns
users = await User.where(User.age >= 18)\
                  .order_by("created_at", "desc")\
                  .limit(10)\
                  .offset(0)\
                  .all()

# Single record
user = await User.where(email="alice@example.com").first()

# Aggregations & Existence
count = await User.where(User.is_active == True).count()
has_active = await User.where(User.is_active == True).exists()

# Pagination
items, total_count, total_pages = await User.where(User.age > 18).paginate(page=1, per_page=15)
```

---

## 6. Relationships & Auto-Batching Engine (Zero N+1 Query)

Solving the $N+1$ query problem is automatic in LunarPhaseORM using `DeferredAutoBatcher` micro-task flushing via `asyncio.get_running_loop().call_soon()`.

### Defining Relationships

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField, HasMany, BelongsTo

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
```

### Accessing Relations

```python
author = await Author.where(id=1).first()
posts = await author.posts # Returns all posts belonging to Author

post = await Post.where(id=10).first()
author = await post.author # Returns parent Author
```

### Eager Loading (`with_relations`)

To load relations up front for multiple items:

```python
authors = await Author.where(Author.id > 0).with_relations("posts").all()
```

---

## 7. Unit of Work & Session Transactions

`UnitOfWork` manages an `IdentityMap` (ensuring 1 DB row maps to exactly 1 model instance in memory) and provides atomic session transactions.

```python
from lunarphase import UnitOfWork, get_engine

uow = UnitOfWork()

# Atomic transaction block
async with uow.begin() as session:
    user1 = User(name="Alice", email="alice@test.com")
    user2 = User(name="Bob", email="bob@test.com")
    
    session.register_new(user1)
    session.register_new(user2)
    # If any error occurs inside block, transaction is automatically rolled back!
```

---

## 8. CLI Auto-Migration System

LunarPhaseORM includes an automated schema diffing CLI powered by Rust `SchemaDiffEngine`.

### CLI Commands

```bash
# Check migration status
lunarphase status

# Generate a new DDL migration script
lunarphase make:migration "create_users_table"

# Apply pending migrations
lunarphase migrate

# Rollback last migration
lunarphase rollback
```

### Reversible Migration File Structure

```python
"""
Migration generated automatically by LunarPhaseORM
"""

async def upgrade(engine):
    sql_statements = ['CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT);']
    for sql in sql_statements:
        await engine.execute(sql)

async def downgrade(engine):
    sql_statements = ['DROP TABLE IF EXISTS users;']
    for sql in sql_statements:
        await engine.execute(sql)
```

---

## 9. Rust Core Engine & Performa Benchmarks

The native Rust extension `lunarphase._lunarphase_rs` offloads CPU-heavy operations from Python to C-level native code:

1. **State Tracking Memory**: Avoids large `__dict__` state duplication per model instance.
2. **SQL Dialect Formatting**: Formats query ASTs in native Rust buffers.
3. **Key Aggregation**: Deduplicates batch relation keys instantly.

### Running Benchmarks & Tests

```bash
# Run pytest with coverage
pytest --cov=lunarphase --cov-report=term-missing
```

---

## 10. Complete End-to-End Example

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
    # 1. Connect Engine
    engine = create_engine("sqlite:///:memory:")

    # 2. Setup tables
    await engine.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255));")
    await engine.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(255), author_id INTEGER);")

    # 3. Create records using Unit of Work
    uow = UnitOfWork(engine)
    async with uow.begin() as session:
        author = Author(name="Arthur Conan Doyle")
        session.register_new(author)

    # 4. Add posts
    await Post.create(title="A Study in Scarlet", author_id=author.id)
    await Post.create(title="The Sign of the Four", author_id=author.id)

    # 5. Query with Zero N+1
    fetched_author = await Author.where(name="Arthur Conan Doyle").first()
    author_posts = await fetched_author.posts
    print(f"Author: {fetched_author.name}")
    for p in author_posts:
        print(f" - Post: {p.title}")

    # 6. Dirty Tracking Update
    fetched_author.name = "Sir Arthur Conan Doyle"
    await fetched_author.save()
    print("Updated author successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```
