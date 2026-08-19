# Syntax Cheat Sheet & API Quick Reference

This document provides a concise, copy-paste ready syntax reference for all core features of **LunarPhaseORM**.

---

## 1. Package Imports

```python
from lunarphase import (
    # Core Base Model
    Model,
    ModelBase,
    
    # Field Descriptors
    PrimaryKeyField,
    StringField,
    IntegerField,
    FloatField,
    BooleanField,
    DateTimeField,
    JSONField,
    
    # Relationships
    HasMany,
    BelongsTo,
    HasOne,
    
    # Database Engine Setup
    create_engine,
    get_engine,
    set_engine,
    SQLiteEngine,
    
    # Query Builder & Batcher
    QueryBuilder,
    DeferredAutoBatcher,
    
    # Unit of Work & Identity Map
    UnitOfWork,
    IdentityMap,
    
    # CLI & Migration Runner
    MigrationRunner,
)
```

---

## 2. Database Connection

```python
# SQLite (In-Memory)
engine = create_engine("sqlite:///:memory:")

# SQLite (File-based)
engine = create_engine("sqlite:///app.db")

# PostgreSQL
engine = create_engine("postgres://user:pass@localhost:5432/dbname")

# MySQL
engine = create_engine("mysql://user:pass@localhost:3306/dbname")
```

---

## 3. Model & Field Declarations

```python
from lunarphase import (
    Model, PrimaryKeyField, StringField, IntegerField,
    FloatField, BooleanField, DateTimeField, JSONField,
    HasMany, BelongsTo
)

class User(Model):
    __tablename__ = "users"  # Optional; defaults to "users"

    id = PrimaryKeyField()
    username = StringField(nullable=False)
    email = StringField(nullable=False)
    age = IntegerField(default=18)
    balance = FloatField(default=0.0)
    is_active = BooleanField(default=True)
    metadata = JSONField(nullable=True, default={})
    
    # Relationships
    posts = HasMany(lambda: Post, foreign_key="user_id")

class Post(Model):
    __tablename__ = "posts"

    id = PrimaryKeyField()
    user_id = IntegerField(nullable=False)
    title = StringField(nullable=False)
    content = StringField(nullable=True)
    
    # Relationships
    author = BelongsTo(User, foreign_key="user_id")
```

---

## 4. CRUD Operations (Active Record)

```python
# --- CREATE ---
# Method A: Classmethod create (saves immediately)
user = await User.create(username="alice", email="alice@example.com", age=25)

# Method B: Instantiate and save
user = User(username="bob", email="bob@example.com", age=30)
await user.save()

# --- READ ---
# Fetch all records
all_users = await User.all()

# Fetch first matching record
user = await User.where(username="alice").first()

# Fetch filtered list
adults = await User.where(User.age >= 18).all()

# --- UPDATE (Selective Dirty Field Tracking) ---
user = await User.where(id=1).first()
user.age = 26  # Modifies attribute in Rust StateTracker
await user.save()  # Executes: UPDATE users SET age = 26 WHERE id = 1;

# --- DELETE ---
user = await User.where(id=1).first()
await user.delete()  # Executes: DELETE FROM users WHERE id = 1;
```

---

## 5. Query Builder Fluent API

```python
# Select specific columns
users = await User.select("id", "username").all()

# Single & Multiple WHERE conditions
users = await User.where(User.age >= 18, User.is_active == True).all()

# Kwarg filter & IN clause expansion
users = await User.where(username="alice", id__in=[1, 2, 3]).all()

# Ordering, Limit & Offset
users = await (
    User.where(User.age >= 18)
    .order_by("username", "asc")
    .limit(10)
    .offset(20)
    .all()
)

# Counting & Existence
total_count = await User.where(User.age >= 18).count()
is_exists = await User.where(username="alice").exists()

# Pagination: returns (items, total_count, total_pages)
items, total, pages = await User.where(User.age >= 18).paginate(page=1, per_page=10)

# Eager Loading Relationships
users_with_posts = await User.with_relations("posts").all()
```

---

## 6. AST Filter Operators

| Syntax Operator | Compiled SQL | Example Code |
|---|---|---|
| `User.field == val` | `field = ?` | `User.where(User.username == "alice")` |
| `User.field != val` | `field != ?` | `User.where(User.age != 18)` |
| `User.field < val` | `field < ?` | `User.where(User.age < 18)` |
| `User.field <= val` | `field <= ?` | `User.where(User.age <= 18)` |
| `User.field > val` | `field > ?` | `User.where(User.age > 18)` |
| `User.field >= val` | `field >= ?` | `User.where(User.age >= 18)` |
| `User.field.in_([a, b])` | `field IN (?, ?)` | `User.where(User.id.in_([1, 2, 3]))` |
| `User.field.like("%val%")` | `field LIKE ?` | `User.where(User.email.like("%@gmail.com"))` |
| `User.field.is_null()` | `field IS NULL` | `User.where(User.metadata.is_null())` |
| `User.field.is_not_null()` | `field IS NOT NULL` | `User.where(User.email.is_not_null())` |

---

## 7. Relationships & Auto-Batching

```python
# Accessing HasMany relationship (Lazy loaded via DeferredAutoBatcher micro-task)
author = await Author.where(id=1).first()
posts = await author.posts  # Batched automatically across loop iterations!

# Accessing BelongsTo relationship
post = await Post.where(id=10).first()
author = await post.author

# Eager Loading (Zero N+1 Queries)
authors = await Author.with_relations("posts").all()
for author in authors:
    for post in author.posts:
        print(author.name, post.title)
```

---

## 8. Unit of Work & Transactions

```python
from lunarphase import UnitOfWork, create_engine

engine = create_engine("sqlite:///app.db")
uow = UnitOfWork(engine)

# Atomic Transaction Scope (Auto-commit on success, Auto-rollback on exception)
async with uow.begin():
    user = User(username="charlie", email="charlie@example.com")
    uow.register_new(user)
    
    post = Post(user_id=user.id, title="First Post")
    uow.register_new(post)
```

---

## 9. CLI Migration Commands

```bash
# Check migration status
lunarphase status

# Generate auto-diff migration file
lunarphase make:migration "create_users_table"

# Apply pending migrations
lunarphase migrate

# Rollback last migration
lunarphase rollback
```
