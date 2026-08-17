from __future__ import annotations
from typing import Any, Dict, List, Type
from lunarphase.core.model import Model
from lunarphase.db.engine import get_engine

class SchemaExtractor:
    """Extracts schema representation from Python Model classes and live DB."""

    @staticmethod
    def extract_from_model(model_cls: Type[Model]) -> Dict[str, Any]:
        table_name = model_cls.__tablename__
        fields_meta = {}
        for name, field in model_cls._fields.items():
            fields_meta[name] = {
                "data_type": field.data_type,
                "nullable": field.nullable,
                "primary_key": field.primary_key,
                "default": field.default,
            }
        return {"table_name": table_name, "fields": fields_meta}

    @staticmethod
    async def extract_from_db(table_name: str) -> Dict[str, Any]:
        engine = get_engine()
        dialect = engine.dialect
        columns = {}

        if dialect == "sqlite":
            rows = await engine.fetch_all(f"PRAGMA table_info('{table_name}');")
            for r in rows:
                # r: cid, name, type, notnull, dflt_value, pk
                col_name = r.get("name")
                columns[col_name] = r.get("type", "TEXT")
        return {"table_name": table_name, "columns": columns}
