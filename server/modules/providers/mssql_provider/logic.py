# providers/mssql_provider/logic.py
import aioodbc, logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Iterable, Optional

_pool: aioodbc.pool.Pool | None = None

async def init_pool(*, dsn: str | None = None, **cfg):
    global _pool
    if not dsn:
        # allow explicit pieces if you pass them later
        raise RuntimeError("MSSQL DSN is required")
    _pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
    logging.info("MSSQL ODBC Connection Pool Created")

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logging.info("MSSQL ODBC Connection Pool Closed")

@asynccontextmanager
async def transaction():
    assert _pool, "MSSQL pool not initialized"
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            # aioodbc connections created with autocommit=True do not support
            # explicit transaction begin. Temporarily disable autocommit so
            # commit/rollback can manage the transaction scope.
            orig_autocommit = conn.autocommit
            conn.autocommit = False
            try:
                yield cur
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logging.debug(f"[TRANSACTION ERROR] Rolled back due to: {e}")
                raise
            finally:
                conn.autocommit = orig_autocommit

def _rowdict(cols: Iterable[str], row: Iterable[Any]):  # no JSON decode here
    return dict(zip(cols, row))

async def fetch_json_one(query: str, params: tuple[Any, ...] = ()):
    """Assumes SELECT ... FOR JSON ... WITHOUT_ARRAY_WRAPPER"""
    assert _pool, "MSSQL pool not initialized"
    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()
                if not row or not row[0]:
                    return None
                import json
                return json.loads(row[0])
    except Exception as e:
        logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
        return None

async def fetch_json_many(query: str, params: tuple[Any, ...] = ()):
    """Assumes SELECT ... FOR JSON PATH (array)"""
    assert _pool, "MSSQL pool not initialized"
    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()
                if not row or not row[0]:
                    return []
                import json
                return json.loads(row[0])
    except Exception as e:
        logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
        return []

async def exec_(query: str, params: tuple[Any, ...] = ()):
    assert _pool, "MSSQL pool not initialized"
    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.rowcount or 0
    except Exception as e:
        logging.debug(f"Exec failed:\n{query}\nArgs: {params}\nError: {e}")
        return 0
