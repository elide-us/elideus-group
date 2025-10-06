# providers/database/mssql_provider/logic.py
import asyncio
import logging
import aioodbc
from contextlib import asynccontextmanager

_pool: aioodbc.pool.Pool | None = None
_pool_config: dict[str, object] | None = None
_init_lock = asyncio.Lock()


async def init_pool(*, dsn: str | None = None, minsize: int | None = None, maxsize: int | None = None, **cfg):
  global _pool, _pool_config
  if not dsn:
    raise RuntimeError("MSSQL DSN is required")
  pool_kwargs: dict[str, object] = {"dsn": dsn, "autocommit": True}
  if minsize is not None:
    pool_kwargs["minsize"] = int(minsize)
  if maxsize is not None:
    pool_kwargs["maxsize"] = int(maxsize)
  pool_kwargs.update(cfg)
  async with _init_lock:
    if _pool is not None:
      if _pool_config != pool_kwargs:
        raise RuntimeError("MSSQL pool already initialized with different configuration")
      return _pool
    _pool = await aioodbc.create_pool(**pool_kwargs)
    _pool_config = dict(pool_kwargs)
    logging.info("MSSQL ODBC Connection Pool Created")
    return _pool


async def close_pool():
  global _pool, _pool_config
  async with _init_lock:
    if _pool:
      _pool.close()
      await _pool.wait_closed()
      _pool = None
      _pool_config = None
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
