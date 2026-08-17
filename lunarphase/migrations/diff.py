from __future__ import annotations
from typing import Any, Dict, List, Tuple, Type
from lunarphase.core.model import Model
from lunarphase.migrations.schema import SchemaExtractor
from lunarphase.db.engine import get_engine

try:
    from lunarphase._lunarphase_rs import SchemaDiffEngine as RustSchemaDiffEngine
    HAS_RUST_DIFF = True
except ImportError:
    HAS_RUST_DIFF = False

class MigrationDiff:
    @staticmethod
    async def generate_diff(models: List[Type[Model]]) -> Tuple[List[str], List[str]]:
        engine = get_engine()
        upgrade_all = []
        downgrade_all = []

        for model_cls in models:
            model_schema = SchemaExtractor.extract_from_model(model_cls)
            table_name = model_schema["table_name"]
            db_schema = await SchemaExtractor.extract_from_db(table_name)

            if HAS_RUST_DIFF:
                rust_engine = RustSchemaDiffEngine()
                up, down = rust_engine.diff_table(
                    table_name,
                    model_schema["fields"],
                    db_schema["columns"],
                    engine.dialect,
                )
                upgrade_all.extend(up)
                downgrade_all.extend(down)
            else:
                # Python Fallback Schema Diff
                fields = model_schema["fields"]
                cols = db_schema["columns"]
                if not cols:
                    col_defs = []
                    for name, meta in fields.items():
                        d = f"{name} {meta['data_type']}"
                        if meta["primary_key"]:
                            d += " PRIMARY KEY"
                        elif not meta["nullable"]:
                            d += " NOT NULL"
                        col_defs.append(d)
                    up = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)});"
                    down = f"DROP TABLE IF EXISTS {table_name};"
                    upgrade_all.append(up)
                    downgrade_all.append(down)
                else:
                    for name, meta in fields.items():
                        if name not in cols:
                            up = f"ALTER TABLE {table_name} ADD COLUMN {name} {meta['data_type']};"
                            down = f"ALTER TABLE {table_name} DROP COLUMN {name};"
                            upgrade_all.append(up)
                            downgrade_all.append(down)

        return upgrade_all, downgrade_all
