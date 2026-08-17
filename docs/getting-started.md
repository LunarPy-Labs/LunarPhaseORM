# Getting Started

This guide details environment setup, database engine initialization, model definitions, and basic CRUD operations.

---

## Installation

Install the compiled package from PyPI:

```bash
pip install lunarphase-orm
```

### Local Build from Source

Building the C-extension requires Rust 1.80+ and Maturin:

```bash
git clone https://github.com/LunarPy-Labs/LunarPhaseORM.git
cd LunarPhaseORM
python3 -m venv .venv
source .venv/bin/activate
pip install maturin aiosqlite pydantic
maturin develop --release
```

---

## Database Connection Configuration

LunarPhaseORM supports SQLite, PostgreSQL, and MySQL using async Python database drivers. Driver selection is determined by the connection URI scheme:

```python
from lunarphase import create_engine

# SQLite (In-Memory or File)
sqlite_engine = create_engine("sqlite:///:memory:")

# PostgreSQL (via asyncpg)
pg_engine = create_engine("postgres://user:password@localhost:5432/dbname")

# MySQL (via aiomysql)
mysql_engine = create_engine("mysql://user:password@localhost:3306/dbname")
```

---

## Defining Models

Models subclass `lunarphase.Model`. Column fields are defined using field descriptors:

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField, BooleanField

class User(Model):
    __tablename__ = "users"

    id = PrimaryKeyField()
    name = StringField(nullable=False)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)
```

---

## Basic Operations

### 1. Creating Records

Records can be created using `Model.create()` or by instantiating the model class and calling `save()`:

```python
async def create_examples():
    # Approach 1: Direct instantiation and save
    user = User(name="Alice", age=25)
    await user.save()

    # Approach 2: Classmethod creation
    bob = await User.create(name="Bob", age=30)
```

### 2. Querying Records

The query builder API supports filtering, ordering, limiting, and pagination:

```python
async def query_examples():
    # Single record lookup
    user = await User.where(id=1).first()

    # Filtered dataset lookup
    adults = await User.where(User.age >= 18).order_by("age", "desc").all()

    # IN clause expansion
    results = await User.where(id__in=[1, 2, 3]).all()
```

### 3. Updating Records (Dirty Field Tracking)

Modifying an attribute updates the model's internal tracking state. Calling `save()` generates an `UPDATE` query containing only the modified columns:

```python
async def update_example():
    user = await User.where(id=1).first()
    
    # Modify property
    user.age = 26
    
    # Executes: UPDATE users SET age = 26 WHERE id = 1;
    await user.save()
```

If `user.save()` is called without modifying attributes, no database query is executed.

### 4. Deleting Records

```python
async def delete_example():
    user = await User.where(id=1).first()
    await user.delete()
```
