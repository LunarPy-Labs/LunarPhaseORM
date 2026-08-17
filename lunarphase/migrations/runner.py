import importlib.util
import os
import time
from typing import List, Optional
from lunarphase.db.engine import get_engine
from lunarphase.migrations.diff import MigrationDiff

MIGRATIONS_DIR = "migrations"

TEMPLATE = '''"""
Migration generated automatically by LunarPhaseORM
Timestamp: {timestamp}
"""

async def upgrade(engine):
    sql_statements = {upgrade_sql!r}
    for sql in sql_statements:
        await engine.execute(sql)

async def downgrade(engine):
    sql_statements = {downgrade_sql!r}
    for sql in sql_statements:
        await engine.execute(sql)
'''

class MigrationRunner:
    def __init__(self, migrations_dir: str = MIGRATIONS_DIR):
        self.migrations_dir = migrations_dir
        os.makedirs(self.migrations_dir, exist_ok=True)

    async def init_migration_table(self):
        engine = get_engine()
        sql = """
        CREATE TABLE IF NOT EXISTS _lunarphase_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        await engine.execute(sql)

    async def make_migration(self, name: str, models: list) -> Optional[str]:
        upgrade_sql, downgrade_sql = await MigrationDiff.generate_diff(models)
        if not upgrade_sql:
            print("No schema changes detected.")
            return None

        timestamp = int(time.time())
        filename = f"{timestamp}_{name}.py"
        filepath = os.path.join(self.migrations_dir, filename)

        content = TEMPLATE.format(
            timestamp=timestamp,
            upgrade_sql=upgrade_sql,
            downgrade_sql=downgrade_sql,
        )

        with open(filepath, "w") as f:
            f.write(content)

        print(f"Created migration file: {filepath}")
        return filepath

    async def migrate(self):
        await self.init_migration_table()
        engine = get_engine()

        applied_rows = await engine.fetch_all("SELECT name FROM _lunarphase_migrations;")
        applied_names = {r["name"] for r in applied_rows}

        files = sorted([f for f in os.listdir(self.migrations_dir) if f.endswith(".py") and not f.startswith("__")])

        for fname in files:
            if fname not in applied_names:
                print(f"Applying migration: {fname}")
                fpath = os.path.join(self.migrations_dir, fname)
                spec = importlib.util.spec_from_file_location(fname[:-3], fpath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                await mod.upgrade(engine)
                await engine.execute(
                    "INSERT INTO _lunarphase_migrations (name) VALUES (?);", (fname,)
                )
                print(f"Successfully applied: {fname}")

    async def rollback(self):
        await self.init_migration_table()
        engine = get_engine()

        applied_rows = await engine.fetch_all(
            "SELECT name FROM _lunarphase_migrations ORDER BY id DESC LIMIT 1;"
        )
        if not applied_rows:
            print("No migrations to rollback.")
            return

        last_fname = applied_rows[0]["name"]
        print(f"Rolling back migration: {last_fname}")
        fpath = os.path.join(self.migrations_dir, last_fname)

        if os.path.exists(fpath):
            spec = importlib.util.spec_from_file_location(last_fname[:-3], fpath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            await mod.downgrade(engine)
            await engine.execute(
                "DELETE FROM _lunarphase_migrations WHERE name = ?;", (last_fname,)
            )
            print(f"Successfully rolled back: {last_fname}")
