import asyncio
import re
from typing import Any, Dict, List, Optional, Union

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

try:
    import aiomysql
except ImportError:
    aiomysql = None

try:
    import asyncpg
except ImportError:
    asyncpg = None

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


class MySQLEngine(DatabaseEngine):
    def __init__(self, url: str):
        super().__init__(url)
        # URL format: mysql://user:password@host:port/database
        pattern = r"mysql://(?:(?P<user>[^:@]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>[^?]+)"
        match = re.match(pattern, url)
        if match:
            gd = match.groupdict()
            self.host = gd["host"] or "localhost"
            self.port = int(gd["port"]) if gd["port"] else 3306
            self.user = gd["user"] or "root"
            self.password = gd["password"] or ""
            self.db = gd["db"] or ""
        else:
            self.host = "localhost"
            self.port = 3306
            self.user = "root"
            self.password = ""
            self.db = ""
        self._pool = None

    async def connect(self):
        if not self._pool:
            if aiomysql is None:
                raise ImportError("aiomysql package is required for MySQL support. Install it with 'pip install aiomysql'.")
            self._pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                autocommit=True
            )

    async def disconnect(self):
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        await self.connect()
        sql_conv = sql.replace("?", "%s")
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql_conv, params)
                rows = await cur.fetchall()
                return list(rows)

    async def execute(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        sql_conv = sql.replace("?", "%s")
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                res = await cur.execute(sql_conv, params)
                return res

    async def execute_insert(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        sql_conv = sql.replace("?", "%s")
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql_conv, params)
                return cur.lastrowid


class PostgresEngine(DatabaseEngine):
    def __init__(self, url: str):
        super().__init__(url)
        self._pool = None

    async def connect(self):
        if not self._pool:
            if asyncpg is None:
                raise ImportError("asyncpg package is required for PostgreSQL support. Install it with 'pip install asyncpg'.")
            self._pool = await asyncpg.create_pool(self.url)

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _convert_placeholders(self, sql: str) -> str:
        count = 0
        def repl(match):
            nonlocal count
            count += 1
            return f"${count}"
        return re.sub(r"\?", repl, sql)

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        await self.connect()
        sql_conv = self._convert_placeholders(sql)
        async with self._pool.acquire() as conn:
            records = await conn.fetch(sql_conv, *params)
            return [dict(r) for r in records]

    async def execute(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        sql_conv = self._convert_placeholders(sql)
        async with self._pool.acquire() as conn:
            status = await conn.execute(sql_conv, *params)
            return status

    async def execute_insert(self, sql: str, params: tuple = ()) -> Any:
        await self.connect()
        sql_conv = self._convert_placeholders(sql)
        if "RETURNING" not in sql_conv.upper():
            sql_conv = sql_conv.rstrip(";") + " RETURNING id;"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql_conv, *params)
            return row["id"] if row else None


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
    elif url.startswith("mysql"):
        engine = MySQLEngine(url)
    elif url.startswith("postgres") or url.startswith("postgresql"):
        engine = PostgresEngine(url)
    else:
        engine = SQLiteEngine(url)
    set_engine(engine)
    return engine
