# providers/postgres_provider/logic.py
import asyncpg, logging
from contextlib import asynccontextmanager
from typing import Any, Iterable

_pool: asyncpg.Pool | None = None

async def init_pool(*, dsn: str | None = None, **cfg):
  global _pool
  if not dsn:
    raise RuntimeError("PostgreSQL DSN is required")
  _pool = await asyncpg.create_pool(dsn=dsn, **cfg)
  logging.info("PostgreSQL Connection Pool Created")

async def close_pool():
  global _pool
  if _pool:
    await _pool.close()
    _pool = None
    logging.info("PostgreSQL Connection Pool Closed")

@asynccontextmanager
async def transaction():
  assert _pool, "PostgreSQL pool not initialized"
  async with _pool.acquire() as conn:
    async with conn.transaction():
      try:
        yield conn
      except Exception as e:
        logging.debug(f"[TRANSACTION ERROR] Rolled back due to: {e}")
        raise

async def execute(query: str, params: Iterable[Any] = ()):  # returns rowcount
  assert _pool, "PostgreSQL pool not initialized"
  try:
    async with _pool.acquire() as conn:
      status = await conn.execute(query, *params)
      try:
        return int(status.split()[-1])
      except Exception:
        return 0
  except Exception as e:
    logging.debug(f"Exec failed:\n{query}\nArgs: {params}\nError: {e}")
    return 0

async def fetch_one(query: str, params: Iterable[Any] = ()):  # returns dict or None
  assert _pool, "PostgreSQL pool not initialized"
  try:
    async with _pool.acquire() as conn:
      row = await conn.fetchrow(query, *params)
      return dict(row) if row else None
  except Exception as e:
    logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    return None

async def fetch_many(query: str, params: Iterable[Any] = ()):  # returns list[dict]
  assert _pool, "PostgreSQL pool not initialized"
  try:
    async with _pool.acquire() as conn:
      rows = await conn.fetch(query, *params)
      return [dict(r) for r in rows]
  except Exception as e:
    logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    return []

