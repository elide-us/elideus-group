# providers/database/mssql_provider/logic.py
import aioodbc, logging
from contextlib import asynccontextmanager
from typing import Callable, Optional

_pool: aioodbc.pool.Pool | None = None


def _parse_dsn_info(dsn: str) -> dict[str, str]:
  """Extract server and database from a DSN connection string."""
  info: dict[str, str] = {}
  for part in dsn.split(";"):
    part = part.strip()
    if not part or "=" not in part:
      continue
    key, _, value = part.partition("=")
    key_upper = key.strip().upper()
    if key_upper == "SERVER":
      info["server"] = value.strip()
    elif key_upper in ("DATABASE", "INITIAL CATALOG"):
      info["database"] = value.strip()
    elif key_upper == "DRIVER":
      info["driver"] = value.strip()
  return info


async def init_pool(*, dsn: str | None = None, **cfg):
  global _pool
  if not dsn:
    raise RuntimeError("MSSQL DSN is required")
  info = _parse_dsn_info(dsn)
  server = info.get("server", "unknown")
  database = info.get("database", "unknown")
  driver = info.get("driver", "unknown")
  _pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
  logging.info(
    "MSSQL ODBC Connection Pool Created: server=%s database=%s driver=%s",
    server,
    database,
    driver,
  )
  print(f"Connected to {database} on {server} ({driver})")

async def close_pool():
  global _pool
  if _pool:
    _pool.close()
    await _pool.wait_closed()
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
