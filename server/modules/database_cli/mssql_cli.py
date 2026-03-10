"""MSSQL CLI helpers for database management."""

from __future__ import annotations

import logging


def _rewrite_dsn_database(dsn: str, dbname: str) -> str:
  parts: list[str] = []
  replaced = False
  for part in dsn.split(";"):
    upper = part.upper()
    if upper.startswith("DATABASE=") or upper.startswith("INITIAL CATALOG="):
      parts.append(f"DATABASE={dbname}")
      replaced = True
    else:
      parts.append(part)
  if not replaced:
    parts.append(f"DATABASE={dbname}")
  return ";".join(parts)


def _warn_if_missing_odbc18(dsn: str):
  if "ODBC Driver 18 for SQL Server" not in dsn:
    logging.warning("[DatabaseCli] DSN does not reference ODBC Driver 18 for SQL Server")


async def connect(*, dsn: str | None, dbname: str | None = None):
  try:
    import aioodbc  # type: ignore
  except Exception as exc:
    raise ImportError("aioodbc is required for database operations") from exc

  if not dsn:
    raise RuntimeError("AZURE_SQL_CONNECTION_STRING not set")
  _warn_if_missing_odbc18(dsn)
  if dbname:
    dsn = _rewrite_dsn_database(dsn, dbname)
  conn = await aioodbc.connect(dsn=dsn, autocommit=True)
  logging.info("[DatabaseCli] Connected to database")
  return conn
