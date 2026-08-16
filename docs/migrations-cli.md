# Migrations & CLI Reference

This document covers automated database schema diffing (`SchemaDiffEngine`), reversible migration generation, and terminal CLI commands.

---

## Schema Diff Engine (`SchemaDiffEngine`)

LunarPhaseORM includes an automated DDL generator powered by native Rust (`src/migration_diff.rs`). The engine compares in-memory `Model` field definitions against database table introspection schemas:

```
+---------------------------+       +---------------------------+
|    Model Definitions      |       |  Database Introspection   |
|  - id: INTEGER PRIMARY KEY|  vs   |  - id: INTEGER PRIMARY KEY|
|  - name: VARCHAR(255)     |       |  - name: VARCHAR(255)     |
|  - age: INTEGER           |       |  (missing 'age' column)   |
+---------------------------+       +---------------------------+
                                  │
                       SchemaDiffEngine.diff_table()
                                  │
                                  ▼
                Generated DDL: ALTER TABLE users ADD COLUMN age INTEGER;
```

---

## Command Line Tool (`lunarphase`)

The `lunarphase` command-line interface provides tools to manage migration files, inspect status, apply pending migrations, and roll back changes.

### 1. `lunarphase status`

Displays current migration state and checks for pending migration files:

```bash
$ lunarphase status
Database Dialect: sqlite
Current Revision: 20260815_001_create_users_table.py
Pending Migrations: 1 file(s) remaining
```

### 2. `lunarphase make:migration`

Generates a reversible Python migration file in `migrations/`:

```bash
$ lunarphase make:migration "add_user_age_column"
Created migration: migrations/20260815_002_add_user_age_column.py
```

#### Migration File Anatomy

Generated migration files export `upgrade()` and `downgrade()` functions:

```python
# migrations/20260815_002_add_user_age_column.py

async def upgrade(engine):
    await engine.execute("ALTER TABLE users ADD COLUMN age INTEGER;")

async def downgrade(engine):
    await engine.execute("ALTER TABLE users DROP COLUMN age;")
```

### 3. `lunarphase migrate`

Applies all pending migration files sequentially:

```bash
$ lunarphase migrate
Applying migration 20260815_002_add_user_age_column.py... OK
Successfully applied 1 migration(s).
```

### 4. `lunarphase rollback`

Rolls back the most recently applied migration by executing its `downgrade()` function:

```bash
$ lunarphase rollback
Rolling back migration 20260815_002_add_user_age_column.py... OK
Successfully rolled back 1 migration(s).
```
