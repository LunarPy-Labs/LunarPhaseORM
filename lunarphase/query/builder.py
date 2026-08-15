from typing import Any, List, Optional, Tuple, Type, TypeVar, Dict
import math
from lunarphase.core.ast import BinaryOp, ColumnRef, Literal
from lunarphase.db.engine import get_engine

try:
    from lunarphase._lunarphase_rs import QueryCompiler as RustQueryCompiler
    HAS_RUST_COMPILER = True
except ImportError:
    HAS_RUST_COMPILER = False

T = TypeVar("T", bound="Model")

class QueryBuilder:
    def __init__(self, model_cls: Type[T]):
        self.model_cls = model_cls
        self.table_name = getattr(model_cls, "__tablename__", model_cls.__name__.lower())
        self._columns: List[str] = []
        self._wheres: List[Tuple[str, str, Any]] = [] # (col, op, val)
        self._joins: List[Tuple[str, str, str]] = [] # (join_type, table, condition)
        self._order_bys: List[Tuple[str, str]] = [] # (col, dir)
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._with_relations: List[str] = []

    def select(self, *fields: str) -> "QueryBuilder":
        self._columns.extend(fields)
        return self

    def where(self, *conditions: Any, **kwargs: Any) -> "QueryBuilder":
        for cond in conditions:
            if isinstance(cond, BinaryOp):
                col_name = cond.left.column_name if isinstance(cond.left, ColumnRef) else str(cond.left)
                val = cond.right.value if isinstance(cond.right, Literal) else cond.right
                self._wheres.append((col_name, cond.op, val))
        for k, v in kwargs.items():
            if k.endswith("__in"):
                col = k[:-4]
                self._wheres.append((col, "IN", v))
            else:
                self._wheres.append((k, "=", v))
        return self

    def limit(self, count: int) -> "QueryBuilder":
        self._limit = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        self._offset = count
        return self

    def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder":
        self._order_bys.append((field, direction))
        return self

    def join(self, target_model: Type[Any], on: str, join_type: str = "INNER") -> "QueryBuilder":
        target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())
        self._joins.append((join_type, target_table, on))
        return self

    def with_relations(self, *relations: str) -> "QueryBuilder":
        self._with_relations.extend(relations)
        return self

    def _compile_sql(self) -> Tuple[str, List[Any]]:
        engine = get_engine()
        dialect = engine.dialect

        cols_str = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols_str} FROM {self.table_name}"
        params = []

        for jtype, jtable, jcond in self._joins:
            sql += f" {jtype.upper()} JOIN {jtable} ON {jcond}"

        if self._wheres:
            where_clauses = []
            for col, op, val in self._wheres:
                if op.upper() == "IN" and isinstance(val, (list, tuple, set)):
                    phs = ", ".join(["?"] * len(val))
                    where_clauses.append(f"{col} IN ({phs})")
                    params.extend(val)
                else:
                    where_clauses.append(f"{col} {op} ?")
                    params.append(val)
            sql += " WHERE " + " AND ".join(where_clauses)

        if self._order_bys:
            order_clauses = [f"{col} {dir.upper()}" for col, dir in self._order_bys]
            sql += " ORDER BY " + ", ".join(order_clauses)

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"

        return sql, params

    async def all(self) -> List[T]:
        engine = get_engine()
        sql, params = self._compile_sql()
        rows = await engine.fetch_all(sql, tuple(params))
        instances = [self.model_cls.hydrate(row) for row in rows]

        # Handle eager loading if requested
        if self._with_relations:
            for rel_name in self._with_relations:
                if hasattr(self.model_cls, rel_name):
                    rel_descriptor = getattr(self.model_cls, rel_name)
                    if hasattr(rel_descriptor, "eager_load"):
                        await rel_descriptor.eager_load(instances)

        return instances

    async def first(self) -> Optional[T]:
        self.limit(1)
        results = await self.all()
        return results[0] if results else None

    async def count(self) -> int:
        engine = get_engine()
        where_clauses = []
        params = []
        for col, op, val in self._wheres:
            if op.upper() == "IN" and isinstance(val, (list, tuple, set)):
                phs = ", ".join(["?"] * len(val))
                where_clauses.append(f"{col} IN ({phs})")
                params.extend(val)
            else:
                where_clauses.append(f"{col} {op} ?")
                params.append(val)

        sql = f"SELECT COUNT(*) as cnt FROM {self.table_name}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        row = await engine.fetch_one(sql, tuple(params))
        if row:
            return list(row.values())[0]
        return 0

    async def exists(self) -> bool:
        c = await self.count()
        return c > 0

    async def paginate(self, page: int = 1, per_page: int = 15) -> Tuple[List[T], int, int]:
        total = await self.count()
        pages = math.ceil(total / per_page) if per_page > 0 else 1
        offset = (page - 1) * per_page
        items = await self.limit(per_page).offset(offset).all()
        return items, total, pages
