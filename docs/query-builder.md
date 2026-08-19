# Query Builder API Tutorial

This document details the fluent `QueryBuilder` API, AST query construction, parameter binding, and execution methods.

---

## 1. Query Builder Fluent Syntax

The `QueryBuilder` provides a type-safe, chainable interface for building SQL queries.

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField

class User(Model):
    id = PrimaryKeyField()
    name = StringField()
    age = IntegerField()
```

---

## 2. Chainable Clause Syntax

### `.select(*fields: str)`

Specifies columns to retrieve:

```python
# SELECT id, name FROM users;
users = await User.select("id", "name").all()
```

### `.where(*conditions, **kwargs)`

Applies filtering conditions. Supports AST operator expressions and keyword arguments:

```python
# AST Expression Filtering
users = await User.where(User.age >= 18).all()

# Multiple AST Conditions (AND logic)
users = await User.where(User.age >= 18, User.name != "Admin").all()

# Keyword Argument Filtering
users = await User.where(name="Alice", age=25).all()

# IN Expansion via kwarg (__in)
users = await User.where(id__in=[1, 2, 3, 4]).all()
```

### `.order_by(field: str, direction: str = "asc")`

Sorts results by field in `"asc"` or `"desc"` direction:

```python
# ORDER BY age DESC, name ASC
users = await User.where(User.age >= 18).order_by("age", "desc").order_by("name", "asc").all()
```

### `.limit(count: int)` & `.offset(count: int)`

Controls result set sizing and pagination offset:

```python
# LIMIT 10 OFFSET 20
users = await User.where(User.age >= 18).limit(10).offset(20).all()
```

### `.join(target_model, on: str, join_type: str = "INNER")`

Performs table joins:

```python
# SELECT * FROM posts INNER JOIN users ON posts.user_id = users.id
posts = await Post.join(User, on="posts.user_id = users.id").all()
```

### `.with_relations(*relations: str)`

Eagerly loads related models in a single batched query:

```python
# Eagerly loads posts for all fetched authors
authors = await Author.with_relations("posts").all()
```

---

## 3. Query Execution Methods Syntax

| Execution Method | Return Type | Description | Example Syntax |
|---|---|---|---|
| `.all()` | `List[Model]` | Fetches all matching rows as model instances | `users = await User.where(User.age >= 18).all()` |
| `.first()` | `Optional[Model]` | Returns the first matching record or `None` | `user = await User.where(User.name == "Alice").first()` |
| `.count()` | `int` | Executes `SELECT COUNT(*)` query | `total = await User.where(User.age >= 18).count()` |
| `.exists()` | `bool` | Checks if at least 1 record matches condition | `has_alice = await User.where(User.name == "Alice").exists()` |
| `.paginate(page, per_page)` | `Tuple[List[Model], int, int]` | Returns `(items, total_count, total_pages)` | `items, total, pages = await User.paginate(page=1, per_page=10)` |

---

## 4. Comprehensive Pagination Example

```python
async def pagination_tutorial():
    page = 2
    per_page = 10
    
    items, total_count, total_pages = await (
        User.where(User.age >= 18)
        .order_by("id", "asc")
        .paginate(page=page, per_page=per_page)
    )

    print(f"Page {page} of {total_pages} (Total Records: {total_count})")
    for user in items:
        print(f"- [{user.id}] {user.name}")
```
