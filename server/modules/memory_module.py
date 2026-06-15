"""Agent memory-bank host module.

Backs the MCP ``memory_*`` tools.  Each public method runs a query that is
registered in ``system_objects_queries`` (namespace ``memory.*``) — there is no
raw-SQL passthrough.  The MCP gateway dispatches to these methods via
``system_objects_gateway_method_bindings`` (see mcp_io_service_module.dispatch).

Conventions:
  * Reads use ``FOR JSON PATH`` ( + ``WITHOUT_ARRAY_WRAPPER`` for single-row).
  * Writes return the affected ``key_guid`` via a trailing single-row SELECT.
  * Queries use positional ``?`` placeholders (pyodbc); GUIDs/timestamps are
    cast in SQL with ``TRY_CAST(? AS UNIQUEIDENTIFIER/DATETIMEOFFSET(7))``.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from . import BaseModule
from .db_module import DbModule

# Bound search/recent page sizes so a misbehaving caller cannot pull the table.
_MAX_LIMIT = 100
_DEFAULT_LIMIT = 20


class MemoryModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._queries: dict[str, str] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    await self._load_queries()
    logging.info("[MemoryModule] Loaded queries=%d", len(self._queries))
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self._queries = {}

  # ── Query loading / execution ──────────────────────────────────────────

  async def _load_queries(self):
    sql = """
SELECT pub_name, pub_query_text
FROM system_objects_queries
WHERE pub_is_active = 1 AND pub_name LIKE 'memory.%'
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""
    loaded = await run_json_many(sql)
    rows = loaded.rows if loaded else []
    self._queries = {
      str(row.get('pub_name')): str(row.get('pub_query_text'))
      for row in rows
      if row.get('pub_name') and row.get('pub_query_text')
    }

  async def _run_query(self, query_name: str, params: tuple = ()) -> Any:
    sql = self._queries.get(query_name)
    if not sql:
      raise RuntimeError(
        f'Memory query not loaded: {query_name}. '
        'Apply migration v0.13.1.0_memory_seed.sql and restart the module.'
      )
    if 'FOR JSON' in sql:
      if 'WITHOUT_ARRAY_WRAPPER' in sql:
        return await run_json_one(sql, params)
      return await run_json_many(sql, params)
    return await run_exec(sql, params)

  @staticmethod
  def _rows(result: Any) -> list[dict[str, Any]]:
    return list(result.rows) if result and getattr(result, 'rows', None) else []

  @staticmethod
  def _clamp_limit(limit: int | None) -> int:
    try:
      value = int(limit) if limit is not None else _DEFAULT_LIMIT
    except (TypeError, ValueError):
      value = _DEFAULT_LIMIT
    return max(1, min(_MAX_LIMIT, value))

  @staticmethod
  def _like(term: str | None) -> str | None:
    return f'%{term}%' if term else None

  # ── Entries ────────────────────────────────────────────────────────────

  async def store_memory(
    self, project: str, kind: str, title: str, body: str,
    tags: str | None = None, thread_guid: str | None = None,
    source: str | None = None,
  ) -> dict[str, Any]:
    """Insert a memory entry. Returns ``{key_guid}`` of the new row."""
    await self.on_ready()
    result = await self._run_query(
      'memory.entries.insert',
      (thread_guid, project, kind, title, body, tags, source),
    )
    rows = self._rows(result)
    if not rows:
      raise RuntimeError('store_memory failed to create the entry')
    return {'key_guid': str(rows[0].get('key_guid'))}

  async def update_memory(
    self, key_guid: str, title: str | None = None, body: str | None = None,
    tags: str | None = None, kind: str | None = None,
    is_active: bool | None = None,
  ) -> dict[str, Any]:
    """Patch a memory entry (only non-null fields change) and bump
    ``priv_modified_on``. Returns ``{key_guid}``."""
    await self.on_ready()
    is_active_param = None if is_active is None else (1 if is_active else 0)
    result = await self._run_query(
      'memory.entries.update',
      (title, body, tags, kind, is_active_param, key_guid, key_guid),
    )
    rows = self._rows(result)
    if not rows:
      raise ValueError(
        f'Unknown memory entry key_guid={key_guid!r}. '
        'Use memory_search to find an entry by title, project, or tag.'
      )
    return {'key_guid': str(rows[0].get('key_guid'))}

  async def get_memory(self, key_guid: str) -> dict[str, Any]:
    """Fetch a single memory entry by ``key_guid``."""
    await self.on_ready()
    result = await self._run_query('memory.entries.get', (key_guid,))
    rows = self._rows(result)
    if not rows:
      raise ValueError(
        f'Unknown memory entry key_guid={key_guid!r}. '
        'Use memory_search to find an entry by title, project, or tag.'
      )
    return rows[0]

  async def search_memory(
    self, query: str | None = None, project: str | None = None,
    kind: str | None = None, tags: str | None = None,
    limit: int = _DEFAULT_LIMIT, offset: int = 0,
  ) -> dict[str, Any]:
    """Filter + paginate active entries. Returns ``{entries[], total}`` where
    ``total`` is the full match count ignoring paging."""
    await self.on_ready()
    limit = self._clamp_limit(limit)
    try:
      offset = max(0, int(offset))
    except (TypeError, ValueError):
      offset = 0
    query_like = self._like(query)
    tags_like = self._like(tags)
    params = (
      query, query_like, query_like, query_like,  # full-text-ish LIKE block
      project, project,                            # project exact
      kind, kind,                                  # kind exact
      tags, tags_like,                             # tags LIKE
      offset, limit,                               # paging
    )
    result = await self._run_query('memory.entries.search', params)
    rows = self._rows(result)
    total = int(rows[0].get('total') or 0) if rows else 0
    entries = []
    for row in rows:
      row.pop('total', None)
      entries.append(row)
    return {'entries': entries, 'total': total}

  async def list_recent_memory(
    self, project: str | None = None, limit: int = _DEFAULT_LIMIT,
  ) -> dict[str, Any]:
    """Most recently modified active entries (optionally per project)."""
    await self.on_ready()
    limit = self._clamp_limit(limit)
    result = await self._run_query('memory.entries.recent', (limit, project, project))
    return {'entries': self._rows(result)}

  # ── Threads ────────────────────────────────────────────────────────────

  async def create_thread(
    self, project: str, title: str, summary: str | None = None,
  ) -> dict[str, Any]:
    """Create a memory thread (a named grouping of entries). Returns
    ``{key_guid}``."""
    await self.on_ready()
    result = await self._run_query('memory.threads.insert', (project, title, summary))
    rows = self._rows(result)
    if not rows:
      raise RuntimeError('create_thread failed to create the thread')
    return {'key_guid': str(rows[0].get('key_guid'))}

  async def get_thread(self, thread_guid: str) -> dict[str, Any]:
    """Fetch a thread and its active entries. Returns ``{thread, entries[]}``."""
    await self.on_ready()
    result = await self._run_query('memory.threads.get', (thread_guid,))
    rows = self._rows(result)
    if not rows:
      raise ValueError(
        f'Unknown memory thread thread_guid={thread_guid!r}. '
        'Use memory_search or memory_list_recent to discover entries.'
      )
    thread = rows[0]
    entries = thread.pop('entries', None) or []
    return {'thread': thread, 'entries': entries}
