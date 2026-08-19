# Unit of Work & Transactions Tutorial

This document details session management, identity mapping (`IdentityMap`), atomic transaction boundaries (`UnitOfWork`), and snapshot isolation.

---

## 1. Identity Map (`IdentityMap`)

The `IdentityMap` maintains in-memory object identity within a session scope. It guarantees that multiple database queries fetching the same record (`table`, `primary_key`) return references to the exact same Python object instance:

```python
from lunarphase.core.uow import IdentityMap
from lunarphase import Model, PrimaryKeyField, StringField

class User(Model):
    id = PrimaryKeyField()
    name = StringField()

identity_map = IdentityMap()

# Register or retrieve instance
user1 = identity_map.get(User, 1)
user2 = identity_map.get(User, 1)

assert user1 is user2  # True! Guarantees single object reference in memory
```

---

## 2. Unit of Work Transaction Engine

`UnitOfWork` manages dirty state tracking and transaction boundaries across multiple operations.

### Basic Transaction Syntax

```python
from lunarphase import UnitOfWork, create_engine, Model, PrimaryKeyField, StringField, IntegerField

engine = create_engine("sqlite:///app.db")
session = UnitOfWork(engine)

async def transaction_tutorial():
    # Atomic transaction scope
    async with session.begin():
        # 1. Register new user
        alice = User(name="Alice", age=25)
        session.register_new(alice)

        # 2. Register another new user
        bob = User(name="Bob", age=30)
        session.register_new(bob)

        # Exiting context block automatically calls await session.commit()!
```

---

## 3. Registration Methods Reference

| Method Signature | Description | Example Syntax |
|---|---|---|
| `session.register_new(instance)` | Registers new instance for `INSERT` on commit | `session.register_new(user)` |
| `session.register_dirty(instance)` | Registers modified instance for `UPDATE` on commit | `session.register_dirty(user)` |
| `session.register_deleted(instance)` | Registers instance for `DELETE` on commit | `session.register_deleted(user)` |

---

## 4. Automatic Rollback & Error Handling

If an exception occurs within `async with session.begin():`, `UnitOfWork` automatically catches the error, executes `await session.rollback()`, and propagates the exception safely:

```python
async def error_rollback_tutorial():
    session = UnitOfWork(engine)

    try:
        async with session.begin():
            user = User(name="Charlie", age=40)
            session.register_new(user)

            # Simulate an unexpected error
            raise ValueError("Something went wrong during checkout!")

    except ValueError as e:
        print("Transaction rolled back safely:", e)
        # Database remains clean and unaffected!
```
