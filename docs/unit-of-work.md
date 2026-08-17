# Unit of Work & Transactions

This document details session management, identity mapping (`IdentityMap`), atomic transaction boundaries (`UnitOfWork`), and snapshot isolation.

---

## Identity Map (`IdentityMap`)

The `IdentityMap` maintains in-memory object identity within a session scope, ensuring that multiple queries fetching the same database record (`table`, `primary_key`) return references to the exact same Python object instance:

```python
from lunarphase.core.uow import IdentityMap

identity_map = IdentityMap()

# Registers or returns existing instance
user1 = identity_map.get(User, 1)
user2 = identity_map.get(User, 1)

assert user1 is user2  # Guarantees single object identity in memory
```

---

## Transaction Engine (`UnitOfWork`)

`UnitOfWork` tracks pending mutations across model instances during a session, committing changes atomically inside transaction blocks.

### Basic Transaction Scope

```python
from lunarphase import UnitOfWork, create_engine

engine = create_engine("sqlite:///app.db")
session = UnitOfWork(engine)

async with session.begin():
    user = User(name="Alice", age=25)
    session.register_new(user)

    order = Order(user_id=user.id, amount=100.0)
    session.register_new(order)
    
    # Exiting context block automatically calls await session.commit()
```

If an exception occurs within `async with session.begin():`, the context manager automatically catches the error, calls `await session.rollback()`, and propagates the exception.

---

## Dirty State Tracking Mechanism

```
State Initialization (hydrate / create)
  │
  ├─► Snapshot State: {"name": "Alice", "age": 25}
  └─► Current State:  {"name": "Alice", "age": 25}
  
Attribute Mutation: user.age = 26
  │
  ├─► Snapshot State: {"name": "Alice", "age": 25}
  └─► Current State:  {"name": "Alice", "age": 26}  <-- Marked Dirty!

Calling user.save() / session.commit()
  │
  ├─► Rust StateTracker diffs FxHashMap entries
  ├─► Formats SQL: UPDATE users SET age = 26 WHERE id = 1;
  └─► Calls hydrate_snapshot(): Snapshot updated to {"name": "Alice", "age": 26}
```
