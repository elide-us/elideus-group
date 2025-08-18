# providers/mssql_provider/logic.py
import aioodbc, logging
from contextlib import asynccontextmanager
from typing import Callable, Optional

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
