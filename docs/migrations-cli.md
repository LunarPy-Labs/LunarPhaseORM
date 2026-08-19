# Migrations & CLI Reference Tutorial

This document covers automated database schema diffing (`SchemaDiffEngine`), migration file generation, and CLI terminal commands.

---

## 1. Command Line Tool (`lunarphase`)

The `lunarphase` CLI manages database schema migrations, status inspections, and rollbacks.

### CLI Commands Summary

| Command Syntax | Description | Example Usage |
|---|---|---|
| `lunarphase status` | Displays current migration status and pending files | `lunarphase status` |
| `lunarphase make:migration <name>` | Generates a new DDL schema migration file | `lunarphase make:migration "create_users_table"` |
| `lunarphase migrate` | Applies all pending migrations sequentially | `lunarphase migrate` |
| `lunarphase rollback` | Rolls back the most recently applied migration | `lunarphase rollback` |

---

## 2. Step-by-Step CLI Migration Walkthrough

### Step 2.1: Checking Migration Status

Check current database migration state:

```bash
$ lunarphase status

--- LunarPhaseORM Migration Status ---
No migrations applied yet.
--------------------------------------
```

### Step 2.2: Generating Migration Files

Generate a new migration script based on your defined models:

```bash
$ lunarphase make:migration "create_users_table"
Created migration file: migrations/1723872000_create_users_table.py
```

### Step 2.3: Generated Migration File Structure

The CLI creates a Python migration script exporting `upgrade(engine)` and `downgrade(engine)` functions:

```python
"""
Migration generated automatically by LunarPhaseORM
Timestamp: 1723872000
"""

async def upgrade(engine):
    sql_statements = [
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) NOT NULL, age INTEGER DEFAULT 18);"
    ]
    for sql in sql_statements:
        await engine.execute(sql)

async def downgrade(engine):
    sql_statements = [
        "DROP TABLE IF EXISTS users;"
    ]
    for sql in sql_statements:
        await engine.execute(sql)
```

### Step 2.4: Applying Migrations (`lunarphase migrate`)

Execute pending migrations:

```bash
$ lunarphase migrate
Applying migration: 1723872000_create_users_table.py
Successfully applied: 1723872000_create_users_table.py
```

### Step 2.5: Verifying Updated Status

```bash
$ lunarphase status

--- LunarPhaseORM Migration Status ---
 [X] 1723872000_create_users_table.py (applied: 2026-08-17 10:15:00)
--------------------------------------
```

### Step 2.6: Rolling Back Migrations (`lunarphase rollback`)

Revert the last applied migration:

```bash
$ lunarphase rollback
Rolling back migration: 1723872000_create_users_table.py
Successfully rolled back: 1723872000_create_users_table.py
```
