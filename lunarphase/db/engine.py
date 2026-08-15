import asyncio
import re
from typing import Any, Dict, List, Optional, Union

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

class DatabaseEngine:
    """Base Async Database Engine abstraction."""
    def __init__(self, url: str):
        self.url = url
        self.dialect = self._parse_dialect(url)

    def _parse_dialect(self, url: str) -> str:
        if url.startswith("sqlite"):
            return "sqlite"
        elif url.startswith("postgres") or url.startswith("postgresql"):
            return "postgres"
        elif url.startswith("mysql"):
            return "mysql"
        return "sqlite"

    async def connect(self):
        raise NotImplementedError

    async def disconnect(self):
        raise NotImplementedError

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        rows = await self.fetch_all(sql, params)
        return rows[0] if rows else None

    async def execute(self, sql: str, params: tuple = ()) -> Any:
        raise NotImplementedError

    async def execute_insert(self, sql: str, params: tuple = ()) -> Any:
        raise NotImplementedError


class SQLiteEngine(DatabaseEngine):
    def __init__(self, url: str):
        super().__init__(url)
        # Parse db file path from url sqlite:///path/to/db.sqlite
        path = re.sub(r"^sqlite:///", "", url)
        self.db_path = path if path else ":memory:"
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if not self._conn:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.execute("PRAGMA foreign_keys = ON;")

    async def disconnect(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        await self.connect()
        async with self._conn.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def execute(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        async with self._conn.execute(sql, params) as cursor:
            await self._conn.commit()
            return cursor.rowcount

    async def execute_insert(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        async with self._conn.execute(sql, params) as cursor:
            await self._conn.commit()
            return cursor.lastrowid


_default_engine: Optional[DatabaseEngine] = None

def set_engine(engine: DatabaseEngine):
    global _default_engine
    _default_engine = engine

def get_engine() -> DatabaseEngine:
    global _default_engine
    if _default_engine is None:
        # Default fallback to in-memory SQLite
        _default_engine = SQLiteEngine("sqlite:///:memory:")
    return _default_engine

def create_engine(url: str) -> DatabaseEngine:
    if url.startswith("sqlite"):
        engine = SQLiteEngine(url)
    else:
        # Extendable to asyncpg or aiomysql
        engine = SQLiteEngine(url)
    set_engine(engine)
    return engine
