# Getting Started Tutorial

Welcome to **LunarPhaseORM**! This step-by-step tutorial guides you through setting up your environment, connecting to a database engine, defining models, performing CRUD operations, and building a full runnable application.

---

## 1. Installation

Install **LunarPhaseORM** from PyPI using `pip`:

```bash
pip install lunarphase-orm
```

### Installation Verification

Verify the package installation in Python:

```python
import lunarphase
print(lunarphase.__version__)
# Output: 0.1.3
```

---

## 2. Database Connection Setup

LunarPhaseORM connects to databases via async drivers (`aiosqlite`, `asyncpg`, `aiomysql`). Initialize your engine using `create_engine()`:

```python
from lunarphase import create_engine

# SQLite (In-Memory for testing/prototyping)
engine = create_engine("sqlite:///:memory:")

# SQLite (File-based database)
engine = create_engine("sqlite:///app.db")

# PostgreSQL
engine = create_engine("postgres://user:password@localhost:5432/my_database")

# MySQL
engine = create_engine("mysql://user:password@localhost:3306/my_database")
```

---

## 3. Defining Your First Model

Models derive from `lunarphase.Model`. Declare database table attributes using field descriptors (`PrimaryKeyField`, `StringField`, `IntegerField`, etc.):

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField, BooleanField

class User(Model):
    __tablename__ = "users"  # Database table name

    id = PrimaryKeyField()
    name = StringField(nullable=False)
    email = StringField(nullable=False)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)
```

---

## 4. Complete CRUD Syntax Tutorial

### Step 4.1: Creating Records (`INSERT`)

You can create records using `Model.create()` or by instantiating the model class and calling `await user.save()`:

```python
async def create_users_tutorial():
    # Method A: Classmethod creation (Saves directly to DB)
    alice = await User.create(name="Alice", email="alice@example.com", age=25)
    print(f"Created Alice with ID: {alice.id}")

    # Method B: Instantiate first, then save
    bob = User(name="Bob", email="bob@example.com", age=30)
    await bob.save()
    print(f"Created Bob with ID: {bob.id}")
```

### Step 4.2: Querying Records (`SELECT`)

Fetch records using the fluent `QueryBuilder` API:

```python
async def query_users_tutorial():
    # Fetch all records
    all_users = await User.all()
    print("Total users:", len(all_users))

    # Single record lookup by condition
    alice = await User.where(User.name == "Alice").first()
    print("Found Alice:", alice.email)

    # Filtered dataset lookup
    adults = await User.where(User.age >= 21).order_by("age", "desc").all()
    for user in adults:
        print(f"User: {user.name}, Age: {user.age}")

    # List filter using __in
    selected = await User.where(id__in=[1, 2, 3]).all()
```

### Step 4.3: Updating Records (`UPDATE`)

LunarPhaseORM includes **Rust-Powered Selective Field Tracking**. Only attributes you modify are included in the SQL `UPDATE` statement:

```python
async def update_user_tutorial():
    # 1. Fetch user from DB
    user = await User.where(User.name == "Alice").first()

    # 2. Modify attribute
    user.age = 26

    # 3. Save modifications
    # Executes: UPDATE users SET age = 26 WHERE id = 1;
    await user.save()
    print("Alice updated successfully!")
```

> **Performance Note**: Calling `user.save()` without modifying any attributes executes **zero** SQL queries!

### Step 4.4: Deleting Records (`DELETE`)

Delete records from the database using `.delete()`:

```python
async def delete_user_tutorial():
    user = await User.where(User.name == "Bob").first()
    if user:
        await user.delete()
        print("Bob deleted successfully!")
```

---

## 5. Full Runnable Quickstart Example

Copy and run this complete script to see LunarPhaseORM in action:

```python
import asyncio
from lunarphase import (
    Model, PrimaryKeyField, StringField, IntegerField,
    create_engine, get_engine
)

# 1. Define Model
class Product(Model):
    __tablename__ = "products"

    id = PrimaryKeyField()
    name = StringField(nullable=False)
    price = IntegerField(default=0)

async def main():
    # 2. Setup In-Memory SQLite Engine
    engine = create_engine("sqlite:///:memory:")
    
    # 3. Create table schema manually for testing
    await engine.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            price INTEGER DEFAULT 0
        );
    """)

    # 4. Create Products
    p1 = await Product.create(name="Laptop", price=1200)
    p2 = await Product.create(name="Smartphone", price=800)
    p3 = await Product.create(name="Headphones", price=150)

    print(f"Created products: {p1.name}, {p2.name}, {p3.name}")

    # 5. Query Products with Filter & Order
    items = await Product.where(Product.price >= 500).order_by("price", "desc").all()
    print("\nProducts priced >= 500:")
    for item in items:
        print(f" - {item.name}: ${item.price}")

    # 6. Update Product (Selective Field Update)
    p1.price = 1100
    await p1.save()
    print(f"\nUpdated {p1.name} price to ${p1.price}")

    # 7. Count Products
    total_count = await Product.where(Product.price > 0).count()
    print(f"\nTotal products count: {total_count}")

    # 8. Clean up engine connection
    await engine.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```
