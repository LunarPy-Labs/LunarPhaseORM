# Models & Fields Tutorial

This document details model definition mechanics, field descriptor configurations, active record methods, and AST operator overloading syntax.

---

## 1. Model Definition (`lunarphase.Model`)

Models represent database tables. To create a model, inherit from `lunarphase.Model`:

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField

class Article(Model):
    __tablename__ = "articles"  # Explicit table name specification

    id = PrimaryKeyField()
    title = StringField(nullable=False)
    views = IntegerField(default=0)
```

### Table Name Resolution Rules

1. **Explicit Specification**: Set `__tablename__ = "custom_table_name"`.
2. **Automatic Default**: If `__tablename__` is omitted, the metaclass (`ModelBase`) automatically converts the class name to lowercase plural (e.g. `User` -> `"users"`).

---

## 2. Field Descriptors Syntax Reference

Field descriptors define column data types, constraints, and defaults.

```python
from lunarphase import (
    PrimaryKeyField,
    StringField,
    IntegerField,
    FloatField,
    BooleanField,
    DateTimeField,
    JSONField
)
```

### Field Type Options & Constructor Reference

| Field Descriptor | Parameters | SQL Data Type | Usage Example |
|---|---|---|---|
| `PrimaryKeyField` | `name=None`, `auto_increment=True` | `INTEGER PRIMARY KEY AUTOINCREMENT` | `id = PrimaryKeyField()` |
| `StringField` | `name=None`, `nullable=True`, `default=None` | `VARCHAR(255)` | `title = StringField(nullable=False)` |
| `IntegerField` | `name=None`, `nullable=True`, `default=None` | `INTEGER` | `views = IntegerField(default=0)` |
| `FloatField` | `name=None`, `nullable=True`, `default=None` | `REAL` / `FLOAT` | `price = FloatField(default=0.0)` |
| `BooleanField` | `name=None`, `nullable=True`, `default=None` | `BOOLEAN` | `is_published = BooleanField(default=False)` |
| `DateTimeField` | `name=None`, `nullable=True`, `default=None` | `DATETIME` | `created_at = DateTimeField()` |
| `JSONField` | `name=None`, `nullable=True`, `default=None` | `JSON` / `TEXT` | `tags = JSONField(default=[])` |

---

## 3. Active Record Methods Tutorial

Every model instance inherits essential active record methods:

### `.create(**kwargs) -> Model`

Instantiates and saves a model record in a single operation:

```python
article = await Article.create(title="LunarPhaseORM Release", views=100)
```

### `.save() -> bool`

Persists changes to the database. Uses Rust `StateTracker` to diff current attributes against initial snapshots:

```python
article = Article(title="Draft Article", views=0)
await article.save()  # Executes INSERT

article.views = 5  # Mark field as dirty
await article.save()  # Executes UPDATE articles SET views = 5 WHERE id = 1;
```

### `.delete() -> bool`

Deletes the model instance from the database:

```python
article = await Article.where(id=1).first()
await article.delete()  # Executes DELETE FROM articles WHERE id = 1;
```

### `.hydrate(row: dict) -> Model`

Hydrates a dictionary row into a tracked model instance without triggering database SQL:

```python
raw_row = {"id": 10, "title": "Hydrated Article", "views": 500}
article = Article.hydrate(raw_row)
print(article.title)  # "Hydrated Article"
```

---

## 4. AST Operator Overloading Syntax

Accessing a field descriptor on a Model class returns a `ColumnRef` node. Python operators are overloaded to produce AST filter expressions:

```python
# Returns ColumnRef("views")
Article.views

# Returns BinaryOp(ColumnRef("views"), ">=", Literal(50))
Article.views >= 50
```

### Complete AST Expression Operators

```python
# Equality (==) -> "title = 'Python'"
Article.title == "Python"

# Inequality (!=) -> "views != 0"
Article.views != 0

# Less than (<) & Less than or equal (<=)
Article.views < 100
Article.views <= 100

# Greater than (>) & Greater than or equal (>=)
Article.views > 10
Article.views >= 10

# IN List (.in_([val1, val2]))
Article.id.in_([1, 2, 3])

# SQL LIKE Pattern (.like(pattern))
Article.title.like("%ORM%")

# Null Checks (.is_null() / .is_not_null())
Article.title.is_null()
Article.title.is_not_null()
```
