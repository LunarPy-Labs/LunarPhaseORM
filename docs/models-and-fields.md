# Models & Fields

This document describes model definition mechanics, field descriptor types, metaclass attribute processing, and operator overloading expressions.

---

## Model Metaclass (`ModelBase`)

Model classes derive from `lunarphase.Model`, which is instantiated by metaclass `ModelBase`. The metaclass performs class creation processing:

1. **Table Name Resolution**: Reads `__tablename__`. If unspecified, defaults to the lowercase pluralized class name.
2. **Field Descriptor Collection**: Scans class attributes for instances of `FieldDescriptor`, registering them into a `_fields` dictionary.
3. **Primary Key Identification**: Verifies the presence of a `PrimaryKeyField`. If omitted, automatically appends `id = PrimaryKeyField()`.
4. **Relationship Registration**: Collects relationship descriptors (`HasMany`, `BelongsTo`, `HasOne`) into `_relations`.

---

## Field Descriptors

Field descriptors manage type coercion, default value assignment, nullability constraints, and SQL data type mapping.

### Available Field Types

| Field Class | Python Type | Default SQL Type | Constructor Arguments |
|---|---|---|---|
| `PrimaryKeyField` | `int` | `INTEGER PRIMARY KEY AUTOINCREMENT` | `name=None` |
| `StringField` | `str` | `VARCHAR(255)` | `max_length=255`, `nullable=True`, `default=None` |
| `IntegerField` | `int` | `INTEGER` | `nullable=True`, `default=None` |
| `FloatField` | `float` | `FLOAT` | `nullable=True`, `default=None` |
| `BooleanField` | `bool` | `BOOLEAN` | `nullable=True`, `default=False` |
| `DateTimeField` | `datetime` | `DATETIME` | `auto_now=False`, `auto_now_add=False` |
| `JSONField` | `dict` / `list` | `JSON` | `nullable=True`, `default=None` |

---

## Operator Overloading & AST Expressions

Accessing a field descriptor at the class level returns a `ColumnRef` AST node. Operator overloading builds AST expressions without executing queries:

```python
# Returns ColumnRef("age")
User.age

# Returns BinaryOp(ColumnRef("age"), ">=", Literal(18))
User.age >= 18
```

### Supported Operator Mappings

| Operator / Method | SQL Output Pattern | AST Node Formed |
|---|---|---|
| `==` | `column = ?` | `BinaryOp(col, "=", val)` |
| `!=` | `column != ?` | `BinaryOp(col, "!=", val)` |
| `<` | `column < ?` | `BinaryOp(col, "<", val)` |
| `<=` | `column <= ?` | `BinaryOp(col, "<=", val)` |
| `>` | `column > ?` | `BinaryOp(col, ">", val)` |
| `>=` | `column >= ?` | `BinaryOp(col, ">=", val)` |
| `.in_(list)` | `column IN (?, ?, ?)` | `BinaryOp(col, "IN", tuple)` |
| `.like(pattern)` | `column LIKE ?` | `BinaryOp(col, "LIKE", pattern)` |
| `.is_null()` | `column IS NULL` | `BinaryOp(col, "IS NULL", None)` |
| `.is_not_null()` | `column IS NOT NULL` | `BinaryOp(col, "IS NOT NULL", None)` |
