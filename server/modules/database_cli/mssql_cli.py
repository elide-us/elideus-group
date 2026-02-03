"""MSSQL CLI helpers for database management."""

from __future__ import annotations

import logging
from typing import Iterable


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


async def reconnect(conn, *, dsn: str | None, dbname: str):
  if conn:
    try:
      await conn.close()
      logging.info("[DatabaseCli] Closed existing connection")
    except Exception:
      logging.exception("[DatabaseCli] Failed to close existing connection")
      raise
  return await connect(dsn=dsn, dbname=dbname)


async def list_tables(conn) -> list[str]:
  query = (
    "SELECT TABLE_SCHEMA, TABLE_NAME "
    "FROM INFORMATION_SCHEMA.TABLES "
    "WHERE TABLE_TYPE='BASE TABLE' "
    "AND TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'sys') "
    "ORDER BY TABLE_SCHEMA, TABLE_NAME"
  )
  async with conn.cursor() as cur:
    await cur.execute(query)
    rows = await cur.fetchall()
  return [f\"{row[0]}.{row[1]}\" for row in rows]


async def list_table_names(conn) -> list[str]:
  return await list_tables(conn)
