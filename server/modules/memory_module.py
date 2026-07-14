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

# ── Confidence weighting policy (FDD-ORACLE-MEM-CONFLICT-01) ─────────────────
# Base confidence assigned to a claim when the caller supplies none. Confidence
# is CONFIDENCE, never truth: it gates how loudly the system objects to a
# contradiction, not whether a claim is accepted. A human-sourced statement is
# pinned to 1.0 as a *source* property — still not truth (a human can typo).
# These numbers MIRROR the PHASE 2 backfill in migration v0.13.2.0; keep in sync.
_BASE_CONFIDENCE: dict[str, float] = {
  'invariant': 0.90,
  'decision': 0.85,
  'spec': 0.80,
  'reference': 0.75,
  'snippet': 0.70,
  'note': 0.60,
  'session_summary': 0.55,
}
_DEFAULT_CONFIDENCE = 0.70  # unknown / unlisted kind
_VALID_CONFIDENCE_SOURCES = ('agent', 'human', 'derived', 'imported')

# Reference-edge kinds and contradiction resolution classes (FDD §4). Only
# 'cites'/'supports' edges confer authority (feed pub_ref_count); the rest are
# structural (supersede/contradict/disambiguate/derive).
_VALID_REF_KINDS = ('cites', 'supports', 'supersedes', 'derived_from', 'contradicts', 'disambiguates')
_VALID_RESOLUTIONS = ('correction', 'new_version', 'typo', 'contradiction', 'misunderstanding')


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

  @staticmethod
  def _resolve_confidence(
    kind: str, confidence: float | None, confidence_source: str | None,
  ) -> tuple[float, str]:
    """Resolve the stored (confidence, source) for a new entry.

    - source defaults to 'agent'; unknown sources are coerced to 'agent'.
    - if confidence is omitted: a 'human' source yields 1.0, otherwise the
      per-kind base weight (falling back to _DEFAULT_CONFIDENCE).
    - an explicit confidence is honoured but clamped to [0, 1] (invariant #1:
      confidence is always a 0..1 scalar).
    """
    source = (confidence_source or 'agent').strip().lower()
    if source not in _VALID_CONFIDENCE_SOURCES:
      source = 'agent'
    if confidence is None:
      value = 1.0 if source == 'human' else _BASE_CONFIDENCE.get(kind, _DEFAULT_CONFIDENCE)
    else:
      try:
        value = float(confidence)
      except (TypeError, ValueError):
        value = _DEFAULT_CONFIDENCE
    value = max(0.0, min(1.0, value))
    return value, source

  @staticmethod
  def _validate_ref_kind(kind: str | None) -> str:
    """Normalise + validate a reference-edge kind (default 'cites')."""
    normalised = (kind or 'cites').strip().lower()
    if normalised not in _VALID_REF_KINDS:
      raise ValueError(
        f'Invalid reference kind {kind!r}. One of: {", ".join(_VALID_REF_KINDS)}.'
      )
    return normalised

  @staticmethod
  def _validate_resolution(resolution: str | None) -> str:
    """Normalise + validate a contradiction resolution class."""
    normalised = (resolution or '').strip().lower()
    if normalised not in _VALID_RESOLUTIONS:
      raise ValueError(
        f'Invalid resolution {resolution!r}. One of: {", ".join(_VALID_RESOLUTIONS)}.'
      )
    return normalised

  @staticmethod
  def _authority(confidence: float, ref_count: int) -> float:
    """Anti-decay authority score used for consult ranking (mirrors the SQL in
    memory.entries.consult): confidence * (1 + ref_count)."""
    return float(confidence) * (1 + int(ref_count))

  # ── Entries ────────────────────────────────────────────────────────────

  async def store_memory(
    self, project: str, kind: str, title: str, body: str,
    tags: str | None = None, thread_guid: str | None = None,
    source: str | None = None, confidence: float | None = None,
    confidence_source: str | None = None,
  ) -> dict[str, Any]:
    """Insert a memory entry. Returns ``{key_guid}`` of the new row.

    ``confidence`` is a 0..1 scalar; omit it to take the per-kind base weight
    (or 1.0 when ``confidence_source='human'``). New rows start ``node_state``
    ``active`` with ``ref_count`` 0 (DB defaults)."""
    await self.on_ready()
    conf_value, conf_source = self._resolve_confidence(kind, confidence, confidence_source)
    result = await self._run_query(
      'memory.entries.insert',
      (thread_guid, project, kind, title, body, tags, source, conf_value, conf_source),
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
    tags_like = self._like(tags)
    params = (
      query, query,              # tokenised block: NULL-guard + STRING_SPLIT input
      project, project,          # project exact
      kind, kind,                # kind exact
      tags, tags_like,           # tags LIKE
      offset, limit,             # paging
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

  # ── Consult (anti-decay rule retrieval) ─────────────────────────────────

  async def consult_memory(
    self, project: str | None = None, query: str | None = None,
    limit: int = _DEFAULT_LIMIT,
  ) -> dict[str, Any]:
    """Authority-ranked CODE RULES to conform to before writing code.

    Backs the ``memory_coderules`` tool. Returns active entries TAGGED ``rule``
    (the constraining subset — rule/idea is orthogonal to ``kind``) ordered by
    authority = confidence*(1+ref_count). When ``project`` is given, the
    universal ``general`` rules are folded in. ``query`` is an optional
    tokenised filter (every whitespace term must match title/body/tags)."""
    await self.on_ready()
    limit = self._clamp_limit(limit)
    result = await self._run_query(
      'memory.entries.consult', (limit, project, project, query, query),
    )
    return {'entries': self._rows(result)}

  # ── References (mind-map edges / reinforcement) ─────────────────────────

  async def add_reference(
    self, from_guid: str, to_guid: str, kind: str = 'cites',
    weight: float | None = None,
  ) -> dict[str, Any]:
    """Add a directed reference edge and recompute the target's authority.

    Idempotent on (from, to, kind). Inbound cites/supports edges raise the
    target's ref_count — this is how reference/correction REINFORCES a claim
    (anti-decay). Returns the edge ``{key_guid}``."""
    await self.on_ready()
    kind = self._validate_ref_kind(kind)
    result = await self._run_query(
      'memory.references.insert', (from_guid, to_guid, kind, weight),
    )
    rows = self._rows(result)
    key = str(rows[0].get('key_guid')) if rows else None
    # Recompute the referenced node's authority rollup now the edge exists.
    await self._run_query('memory.entries.recompute_refcount', (to_guid,))
    return {'key_guid': key}

  # ── Contradictions (first-class conflict lifecycle) ─────────────────────

  async def open_contradiction(
    self, project: str, claim_a_guid: str, claim_b_guid: str,
    note: str | None = None,
  ) -> dict[str, Any]:
    """Record a contradiction between two claims and flip both active nodes to
    ``conflict``. Neither claim is destroyed (FDD §3). Returns ``{key_guid}``."""
    await self.on_ready()
    result = await self._run_query(
      'memory.contradictions.open', (claim_a_guid, claim_b_guid, project, note),
    )
    rows = self._rows(result)
    if not rows:
      raise RuntimeError('open_contradiction failed to create the record')
    return {'key_guid': str(rows[0].get('key_guid'))}

  async def resolve_contradiction(
    self, conflict_guid: str, resolution: str, note: str | None = None,
    resolved_source: str | None = None,
  ) -> dict[str, Any]:
    """Resolve a contradiction with an explicit classified transition (FDD §4):

    - ``correction``: A was always wrong → retire A, promote B, B supersedes A.
    - ``new_version``: both true at different times → A historical, B supersedes A.
    - ``typo``: B is malformed → keep A, retire B.
    - ``misunderstanding``: A and B are different things → both active, disambiguated.
    - ``contradiction``: genuine standoff → both active, a contradicts edge recorded.
    """
    await self.on_ready()
    resolution = self._validate_resolution(resolution)
    result = await self._run_query(
      'memory.contradictions.resolve',
      (conflict_guid, resolution, note, resolved_source),
    )
    rows = self._rows(result)
    if not rows:
      raise ValueError(
        f'Unknown contradiction conflict_guid={conflict_guid!r}. '
        'Use memory_conflicts_list to find open contradictions.'
      )
    return rows[0]

  async def list_contradictions(
    self, project: str | None = None, state: str | None = 'open',
    limit: int = _DEFAULT_LIMIT,
  ) -> dict[str, Any]:
    """List contradictions (default ``state='open'`` — the interrupt queue).
    Pass ``state=None`` for all states. Returns ``{contradictions[]}`` with both
    claims' titles/confidence/state joined in."""
    await self.on_ready()
    limit = self._clamp_limit(limit)
    result = await self._run_query(
      'memory.contradictions.list', (limit, project, project, state, state),
    )
    return {'contradictions': self._rows(result)}
