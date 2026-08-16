# Query Builder API

This document details the type-safe fluent `QueryBuilder` API, AST generation, dialect-specific parameter binding, and execution methods.

---

## Query Construction

`QueryBuilder` constructs abstract syntax trees (AST) representing database queries. Method chaining appends clause nodes:

```python
from lunarphase import QueryBuilder

# Constructs AST for SELECT id, name FROM users WHERE age >= 18 ORDER BY name ASC LIMIT 10
query = (
    User.select("id", "name")
    .where(User.age >= 18)
    .order_by("name", "asc")
    .limit(10)
)
```

---

## Dialect Parameter Binding

SQL parameters are formatted according to the configured database engine driver:

| Database Dialect | Driver Package | Parameter Placeholder Format | Compiled Example |
|---|---|---|---|
| `sqlite` | `aiosqlite` | `?` | `WHERE age >= ?` |
| `postgres` / `postgresql` | `asyncpg` | `$1`, `$2`, `$N` | `WHERE age >= $1 AND status = $2` |
| `mysql` | `aiomysql` | `%s` | `WHERE age >= %s` |

Parameter placeholders are generated in Rust via `QueryCompiler::get_placeholder(dialect, index)`.

---

## Query Execution Methods

| Method Signature | Return Type | Description |
|---|---|---|
| `await query.all()` | `List[Model]` | Fetches all matching rows and hydrates model instances. |
| `await query.first()` | `Optional[Model]` | Fetches the first matching record or returns `None`. |
| `await query.count()` | `int` | Executes `SELECT COUNT(*) FROM table WHERE ...` and returns integer count. |
| `await query.exists()` | `bool` | Evaluates if at least one matching record exists in the table. |
| `await query.paginate(page, per_page)` | `Tuple[List[Model], int]` | Applies `LIMIT` and `OFFSET` for pagination, returning records and total count. |

---

## IN Expansion (`__in`)

Passing list parameters expands placeholders dynamically:

```python
# Executes: SELECT * FROM users WHERE id IN (?, ?, ?)
users = await User.where(id__in=[1, 2, 3]).all()
```
