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
import re
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

# ── Graph read / traverse bounds ────────────────────────────────────────────
# Edge reads carry an explicit direction so a client renders 'supersedes -> X'
# vs '<- superseded by Y' without re-inverting the stored from->to.
_VALID_DIRECTIONS = ('both', 'out', 'in')
_MAX_DEPTH = 3                 # BFS depth cap (traversal is not the whole DB)
_DEFAULT_DEPTH = 1
_DEFAULT_NEIGHBOR_LIMIT = 50   # node-set cap for neighbors
_MAX_NEIGHBOR_LIMIT = 200
_DEFAULT_GRAPH_LIMIT = 200     # node-set cap for a project graph export
_MAX_GRAPH_LIMIT = 500

# ── Defensive write-path sanitiser ──────────────────────────────────────────
# A recurring client/serialisation glitch leaks a store/update's trailing param
# boundary into the body value — e.g. the body arrives as
#   '…real body</body>\n<parameter name="tags">the tags",'
# with the real `tags` argument absorbed into it (so tags itself arrives None),
# nulling the column. This regex matches ONLY that trailing run of boundary junk
# (a leaked close tag + an optional leaked tags param + quote/comma junk),
# anchored to end-of-string, so a body that merely MENTIONS these tokens mid-text
# (this bug's own writeup, say) is never touched. See _sanitize_body_tags.
_BODY_LEAK_RE = re.compile(
  r'\s*</(?:antml:)?(?:body|parameter|invoke)>'
  r'\s*(?:<(?:antml:)?parameter\s+name="tags"\s*>(?P<tags>[^<\n]*))?'
  r'\s*["\',]*\s*(?:</(?:antml:)?(?:parameter|invoke)>\s*)*$',
  re.DOTALL,
)


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

  @staticmethod
  def _validate_direction(direction: str | None) -> str:
    """Normalise + validate an edge-traversal direction (default 'both')."""
    normalised = (direction or 'both').strip().lower()
    if normalised not in _VALID_DIRECTIONS:
      raise ValueError(
        f'Invalid direction {direction!r}. One of: {", ".join(_VALID_DIRECTIONS)}.'
      )
    return normalised

  @staticmethod
  def _normalise_kinds(kinds: str | None) -> str | None:
    """Turn a comma/space-delimited kinds filter into a validated CSV (lower-
    cased, matching how kinds are stored) or None when empty. Raises on an
    unknown kind so a typo fails loud rather than silently matching nothing."""
    if not kinds:
      return None
    parts = [p.strip().lower() for p in re.split(r'[,\s]+', kinds) if p.strip()]
    invalid = [p for p in parts if p not in _VALID_REF_KINDS]
    if invalid:
      raise ValueError(
        f'Invalid reference kind(s): {", ".join(invalid)}. '
        f'Valid: {", ".join(_VALID_REF_KINDS)}.'
      )
    return ','.join(parts) if parts else None

  @staticmethod
  def _clamp_depth(depth: int | None) -> int:
    try:
      value = int(depth) if depth is not None else _DEFAULT_DEPTH
    except (TypeError, ValueError):
      value = _DEFAULT_DEPTH
    return max(1, min(_MAX_DEPTH, value))

  @staticmethod
  def _clamp(value: int | None, default: int, maximum: int) -> int:
    try:
      resolved = int(value) if value is not None else default
    except (TypeError, ValueError):
      resolved = default
    return max(1, min(maximum, resolved))

  @staticmethod
  def _link_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reshape flat memory.references.list rows into nested link objects with an
    explicit direction and the neighbor ('other') node summarised."""
    links = []
    for r in rows:
      links.append({
        'edge_guid': r.get('edge_guid'),
        'kind': r.get('kind'),
        'weight': r.get('weight'),
        'is_active': bool(r.get('is_active')),
        'direction': r.get('direction'),
        'other': {
          'guid': r.get('other_guid'),
          'title': r.get('other_title'),
          'kind': r.get('other_kind'),
          'project': r.get('other_project'),
          'node_state': r.get('other_node_state'),
          'is_active': bool(r.get('other_is_active')),
        },
      })
    return links

  @staticmethod
  def _edge_row(r: dict[str, Any]) -> dict[str, Any]:
    """Reshape a raw memory.references.edges_batch row into a graph edge."""
    return {
      'edge_guid': str(r.get('edge_guid')),
      'from_guid': str(r.get('from_guid')),
      'to_guid': str(r.get('to_guid')),
      'kind': r.get('kind'),
      'weight': r.get('weight'),
      'is_active': bool(r.get('is_active')),
    }

  @staticmethod
  def _sanitize_body_tags(
    body: str | None, tags: str | None,
  ) -> tuple[str | None, str | None]:
    """Heal a write-time tool-call boundary leak before persisting.

    Some clients occasionally emit a store/update whose trailing param boundary
    bled into ``body`` — e.g. it ends with
    ``…real body</body>\\n<parameter name="tags">the tags",`` and the real
    ``tags`` argument was absorbed (arriving as ``None``), nulling the column.
    This strips that trailing leaked boundary from ``body`` and, when ``tags`` is
    empty, recovers the leaked tag string. Only a TRAILING run of boundary junk
    is removed, so a body that merely MENTIONS ``</body>`` / ``<parameter …>``
    mid-text is left intact. No-op on clean input."""
    if not body:
      return body, tags
    match = _BODY_LEAK_RE.search(body)
    if not match:
      return body, tags
    cleaned = body[:match.start()].rstrip()
    if not cleaned:            # body was nothing but boundary junk — don't destroy it
      return body, tags
    recovered = match.group('tags')
    if recovered is not None:
      recovered = recovered.strip().strip('"\',').strip() or None
    if recovered and not (tags and str(tags).strip()):
      tags = recovered
    return cleaned, tags

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
    body, tags = self._sanitize_body_tags(body, tags)
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
    if body is not None:
      body, tags = self._sanitize_body_tags(body, tags)
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

  async def get_memory(
    self, key_guid: str, include_links: bool = False,
  ) -> dict[str, Any]:
    """Fetch a single memory entry by ``key_guid``.

    When ``include_links`` is true, attach ``links`` — the active reference
    edges incident to this entry, each with an explicit ``direction``
    ('out'/'in') and the neighbor node summarised (so the graph is navigable
    straight from a fetch)."""
    await self.on_ready()
    result = await self._run_query('memory.entries.get', (key_guid,))
    rows = self._rows(result)
    if not rows:
      raise ValueError(
        f'Unknown memory entry key_guid={key_guid!r}. '
        'Use memory_search to find an entry by title, project, or tag.'
      )
    entry = rows[0]
    if include_links:
      link_result = await self._run_query(
        'memory.references.list', (key_guid, 'both', None, 0),
      )
      entry = dict(entry)
      entry['links'] = self._link_rows(self._rows(link_result))
    return entry

  async def search_memory(
    self, query: str | None = None, project: str | None = None,
    kind: str | None = None, tags: str | None = None,
    limit: int = _DEFAULT_LIMIT, offset: int = 0,
  ) -> dict[str, Any]:
    """Filter + paginate active entries by relevance. Returns ``{entries[],
    total}`` (``total`` = full match count ignoring paging). ``query`` matches
    if ANY whitespace term hits title/body/tags; results are ordered by how many
    distinct terms match (each row carries a ``match_count``), then recency. A
    query-less call browses by recency. ``project``/``kind`` are exact filters;
    ``tags`` is a LIKE filter."""
    await self.on_ready()
    limit = self._clamp_limit(limit)
    try:
      offset = max(0, int(offset))
    except (TypeError, ValueError):
      offset = 0
    tags_like = self._like(tags)
    params = (
      query,                     # relevance: matched OR-wise, ranked by term hits
      project,                   # project exact
      kind,                      # kind exact
      tags, tags_like,           # tags NULL-guard + LIKE
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

    Backs the ``memory_coderules`` tool. Returns active entries of kind
    ``rule`` (the constraining subset — a rule is an idea that constrains a
    choice) ordered by authority = confidence*(1+ref_count). When ``project`` is given, the
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

  # ── Graph read / traverse (the read half of the mind-map) ───────────────

  async def list_references(
    self, key_guid: str, direction: str = 'both',
    kinds: str | None = None, include_inactive: bool = False,
  ) -> dict[str, Any]:
    """List the reference edges incident to one entry. Returns
    ``{key_guid, links[]}`` where each link is
    ``{edge_guid, kind, weight, is_active, direction:'out'|'in',
    other:{guid,title,kind,project,node_state,is_active}}``.

    ``direction``: both|out|in. ``kinds``: optional comma/space list to filter
    edge kinds. ``include_inactive``: include soft-deleted edges (default
    False)."""
    await self.on_ready()
    direction = self._validate_direction(direction)
    kinds_csv = self._normalise_kinds(kinds)
    inc = 1 if include_inactive else 0
    result = await self._run_query(
      'memory.references.list', (key_guid, direction, kinds_csv, inc),
    )
    return {'key_guid': key_guid, 'links': self._link_rows(self._rows(result))}

  async def get_neighbors(
    self, key_guid: str, depth: int = _DEFAULT_DEPTH,
    kinds: str | None = None, direction: str = 'both',
    limit: int = _DEFAULT_NEIGHBOR_LIMIT,
  ) -> dict[str, Any]:
    """Breadth-first expansion around a node — the "explore related topics"
    navigator. Returns ``{root, nodes[], edges[], truncated}``.

    Cycle-guarded and deduped; ``depth`` clamped to 1..3 and the node set
    clamped to ``limit`` (default 50, max 200). Only *active* nodes are expanded
    and only *active* edges are followed (unless ``kinds`` widens the selection);
    a reached inactive node appears as a leaf. ``edges`` are those incident to an
    expanded node in the requested ``direction`` (use ``export_graph`` for the
    full induced edge set of a project)."""
    await self.on_ready()
    root = str(key_guid)
    depth = self._clamp_depth(depth)
    direction = self._validate_direction(direction)
    kinds_csv = self._normalise_kinds(kinds)
    node_cap = self._clamp(limit, _DEFAULT_NEIGHBOR_LIMIT, _MAX_NEIGHBOR_LIMIT)

    root_rows = self._rows(await self._run_query('memory.entries.get_many', (root,)))
    if not root_rows:
      raise ValueError(
        f'Unknown memory entry key_guid={key_guid!r}. '
        'Use memory_search to find an entry by title, project, or tag.'
      )
    nodes: dict[str, dict[str, Any]] = {str(r.get('key_guid')): r for r in root_rows}
    seen: set[str] = set(nodes)
    edges: dict[str, dict[str, Any]] = {}
    frontier = [root]
    truncated = False

    for _ in range(depth):
      # Only expand THROUGH active nodes (respect node-level soft-delete).
      active_frontier = [
        g for g in frontier if bool(nodes.get(g, {}).get('pub_is_active'))
      ]
      if not active_frontier:
        break
      fset = set(active_frontier)
      erows = self._rows(await self._run_query(
        'memory.references.edges_batch', (','.join(active_frontier), kinds_csv, 0),
      ))
      discovered: list[str] = []
      for r in erows:
        fg, tg = str(r.get('from_guid')), str(r.get('to_guid'))
        edge = self._edge_row(r)
        # An edge is 'out' of a frontier node when that node is the from-end.
        if direction in ('both', 'out') and fg in fset:
          edges[edge['edge_guid']] = edge
          if tg not in seen:
            discovered.append(tg)
        if direction in ('both', 'in') and tg in fset:
          edges[edge['edge_guid']] = edge
          if fg not in seen:
            discovered.append(fg)
      # Dedupe + breadth-cap the newly discovered nodes.
      new_nodes: list[str] = []
      for g in discovered:
        if g in seen:
          continue
        if len(seen) >= node_cap:
          truncated = True
          break
        seen.add(g)
        new_nodes.append(g)
      if new_nodes:
        nrows = self._rows(await self._run_query(
          'memory.entries.get_many', (','.join(new_nodes),),
        ))
        for r in nrows:
          nodes[str(r.get('key_guid'))] = r
      frontier = new_nodes
      if truncated:
        break

    return {
      'root': root,
      'nodes': list(nodes.values()),
      'edges': list(edges.values()),
      'truncated': truncated,
    }

  async def export_graph(
    self, project: str | None = None, kinds: str | None = None,
    limit: int = _DEFAULT_GRAPH_LIMIT,
  ) -> dict[str, Any]:
    """Export a project's memory sub-graph as ``{nodes[], edges[], truncated}``
    for visualization / mind-mapping. Nodes = active entries in ``project`` (its
    universal ``general`` entries folded in), most-referenced first, capped at
    ``limit`` (default 200, max 500). Edges = active reference edges whose BOTH
    endpoints are in the node set (the induced sub-graph).

    ``kinds`` filters the EDGE relationship types (cites/supports/…), the same
    meaning it carries in ``list_references``/``get_neighbors`` — NOT the node
    ``pub_kind``. Nodes are never dropped by ``kinds``; only edges are."""
    await self.on_ready()
    kinds_csv = self._normalise_kinds(kinds)
    node_cap = self._clamp(limit, _DEFAULT_GRAPH_LIMIT, _MAX_GRAPH_LIMIT)
    # Node set is picked by project only — pass None for the query's node-kind
    # slot so `kinds` filters EDGES (below), consistent with the other graph tools.
    nrows = self._rows(await self._run_query(
      'memory.graph.nodes', (project, None, node_cap),
    ))
    node_guids = {str(r.get('key_guid')) for r in nrows}
    truncated = len(nrows) >= node_cap
    edges: list[dict[str, Any]] = []
    if node_guids:
      erows = self._rows(await self._run_query(
        'memory.references.edges_batch', (','.join(node_guids), kinds_csv, 0),
      ))
      for r in erows:
        edge = self._edge_row(r)
        if edge['from_guid'] in node_guids and edge['to_guid'] in node_guids:
          edges.append(edge)
    return {'nodes': nrows, 'edges': edges, 'truncated': truncated}

  # ── Edge maintenance (retract / re-weight — the other half of the write side)

  async def remove_reference(self, edge_guid: str) -> dict[str, Any]:
    """Soft-delete a reference edge (``pub_is_active=0``) and recompute the
    target's ``ref_count`` — the exact inverse of ``add_reference`` so authority
    (confidence × (1 + ref_count)) stays honest. Returns
    ``{edge_guid, to_guid, ref_count}``."""
    await self.on_ready()
    result = await self._run_query('memory.references.remove', (edge_guid,))
    rows = self._rows(result)
    row = rows[0] if rows else None
    if not row or not row.get('found'):
      raise ValueError(
        f'Unknown reference edge_guid={edge_guid!r}. '
        'Use memory_links (or memory_get with include_links=true) to find edge guids.'
      )
    return {
      'edge_guid': str(row.get('edge_guid')),
      'to_guid': str(row.get('to_guid')),
      'ref_count': row.get('ref_count'),
    }

  async def update_reference(
    self, edge_guid: str, weight: float | None = None,
    kind: str | None = None, is_active: bool | None = None,
  ) -> dict[str, Any]:
    """Patch a reference edge (only supplied fields change) and recompute the
    target's ``ref_count``. Retyping to/from cites/supports changes authority,
    which is why the recompute always runs. ``kind`` must be a valid ref kind.
    Returns ``{edge_guid, to_guid, ref_count}``.

    Note: ``(from, to, kind)`` is unique — retyping to a kind that already
    exists between the same endpoints raises a DB uniqueness error."""
    await self.on_ready()
    kind_norm = self._validate_ref_kind(kind) if kind is not None else None
    active_param = None if is_active is None else (1 if is_active else 0)
    result = await self._run_query(
      'memory.references.update', (edge_guid, weight, kind_norm, active_param),
    )
    rows = self._rows(result)
    row = rows[0] if rows else None
    if not row or not row.get('found'):
      raise ValueError(
        f'Unknown reference edge_guid={edge_guid!r}. '
        'Use memory_links (or memory_get with include_links=true) to find edge guids.'
      )
    return {
      'edge_guid': str(row.get('edge_guid')),
      'to_guid': str(row.get('to_guid')),
      'ref_count': row.get('ref_count'),
    }
