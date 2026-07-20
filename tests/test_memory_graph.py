"""Unit tests for the memory-graph READ/TRAVERSE + edge-maintenance surface
(v0.13.6.0 — the read half of the mind-map the write half already built).

Pure logic — no DB. The graph read/traverse methods talk to registered queries
through ``MemoryModule._run_query``; here that is replaced with an in-memory
fake so the BFS, direction/kind filtering, cycle-guarding, breadth-capping and
edge-maintenance branches can be exercised without SQL Server. Async methods are
driven with ``asyncio.run`` (no pytest-asyncio dependency).
"""

import asyncio
import os

import pytest

from server.modules.memory_module import (
  MemoryModule,
  _MAX_DEPTH,
  _MAX_NEIGHBOR_LIMIT,
  _VALID_DIRECTIONS,
)

direction = MemoryModule._validate_direction
norm_kinds = MemoryModule._normalise_kinds
clamp_depth = MemoryModule._clamp_depth
clamp = MemoryModule._clamp
link_rows = MemoryModule._link_rows
edge_row = MemoryModule._edge_row


# ── Test doubles ────────────────────────────────────────────────────────────

class _FakeResult:
  def __init__(self, rows):
    self.rows = rows


def _module(nodes, edges):
  """A MemoryModule wired to an in-memory graph.

  nodes: {guid: {..entry columns.., 'pub_is_active': bool}}
  edges: [{edge_guid, from_guid, to_guid, kind, weight, is_active}]
  Only the queries the graph methods actually call are implemented.
  """
  m = MemoryModule.__new__(MemoryModule)

  async def _ready():
    return None

  def _split(csv):
    return [g for g in (csv or '').split(',') if g]

  async def _run(name, params=()):
    if name == 'memory.entries.get_many':
      guids = _split(params[0])
      return _FakeResult([dict(nodes[g]) for g in guids if g in nodes])

    if name == 'memory.references.edges_batch':
      frontier = set(_split(params[0]))
      kinds = set(_split(params[1])) if params[1] else None
      include_inactive = bool(params[2])
      out = []
      for e in edges:
        if not include_inactive and not e['is_active']:
          continue
        if e['from_guid'] not in frontier and e['to_guid'] not in frontier:
          continue
        if kinds and e['kind'] not in kinds:
          continue
        out.append({
          'edge_guid': e['edge_guid'], 'from_guid': e['from_guid'],
          'to_guid': e['to_guid'], 'kind': e['kind'],
          'weight': e['weight'], 'is_active': e['is_active'],
        })
      return _FakeResult(out)

    if name == 'memory.graph.nodes':
      project, kinds_csv, limit = params
      kinds = set(_split(kinds_csv)) if kinds_csv else None
      rows = [
        dict(n) for n in nodes.values()
        if n.get('pub_is_active')
        and (project is None or n.get('pub_project') in (project, 'general'))
        and (kinds is None or n.get('pub_kind') in kinds)
      ]
      rows.sort(key=lambda n: n.get('pub_ref_count', 0), reverse=True)
      return _FakeResult(rows[:limit])

    raise AssertionError(f'unexpected query: {name}')

  m.on_ready = _ready
  m._run_query = _run
  return m


def _node(guid, active=True, project='p', kind='note', ref_count=0):
  return {
    'key_guid': guid, 'pub_project': project, 'pub_kind': kind,
    'pub_title': f'title-{guid}', 'pub_is_active': active,
    'pub_ref_count': ref_count,
  }


def _edge(eg, frm, to, kind='cites', active=True, weight=1.0):
  return {'edge_guid': eg, 'from_guid': frm, 'to_guid': to,
          'kind': kind, 'weight': weight, 'is_active': active}


def _neighbors(m, guid, **kw):
  return asyncio.run(m.get_neighbors(guid, **kw))


# ── direction validation ────────────────────────────────────────────────────

def test_direction_defaults_to_both():
  assert direction(None) == 'both'
  assert direction('') == 'both'


def test_direction_normalises_case():
  assert direction('  OUT ') == 'out'


def test_every_valid_direction_passes():
  for d in _VALID_DIRECTIONS:
    assert direction(d) == d


def test_invalid_direction_raises():
  with pytest.raises(ValueError):
    direction('upstream')


# ── kinds normalisation ─────────────────────────────────────────────────────

def test_kinds_empty_is_none():
  assert norm_kinds(None) is None
  assert norm_kinds('') is None
  assert norm_kinds('   ') is None


def test_kinds_splits_on_comma_and_space_and_lowercases():
  assert norm_kinds('Cites, supports') == 'cites,supports'
  assert norm_kinds('cites supports') == 'cites,supports'


def test_kinds_rejects_unknown():
  with pytest.raises(ValueError):
    norm_kinds('cites,endorses')


# ── clamps ──────────────────────────────────────────────────────────────────

def test_depth_clamped_to_one_through_three():
  assert clamp_depth(0) == 1
  assert clamp_depth(2) == 2
  assert clamp_depth(99) == _MAX_DEPTH
  assert clamp_depth(None) == 1
  assert clamp_depth('nope') == 1


def test_generic_clamp_bounds_and_defaults():
  assert clamp(None, 50, 200) == 50
  assert clamp(0, 50, 200) == 1
  assert clamp(9999, 50, 200) == _MAX_NEIGHBOR_LIMIT
  assert clamp('bad', 50, 200) == 50


# ── reshapers ───────────────────────────────────────────────────────────────

def test_link_rows_nests_other_and_coerces_bools():
  rows = [{
    'edge_guid': 'E1', 'kind': 'supersedes', 'weight': 1.0, 'is_active': 1,
    'direction': 'out', 'other_guid': 'B', 'other_title': 'b', 'other_kind': 'spec',
    'other_project': 'p', 'other_node_state': 'active', 'other_is_active': 0,
  }]
  (link,) = link_rows(rows)
  assert link['direction'] == 'out'
  assert link['is_active'] is True
  assert link['other'] == {
    'guid': 'B', 'title': 'b', 'kind': 'spec', 'project': 'p',
    'node_state': 'active', 'is_active': False,
  }


def test_edge_row_shape():
  e = edge_row({'edge_guid': 'E', 'from_guid': 'A', 'to_guid': 'B',
                'kind': 'cites', 'weight': 2.0, 'is_active': 1})
  assert e == {'edge_guid': 'E', 'from_guid': 'A', 'to_guid': 'B',
               'kind': 'cites', 'weight': 2.0, 'is_active': True}


# ── neighbors BFS ───────────────────────────────────────────────────────────

def test_neighbors_depth_one_returns_immediate_edge():
  m = _module({'A': _node('A'), 'B': _node('B'), 'C': _node('C')},
              [_edge('E1', 'A', 'B'), _edge('E2', 'B', 'C')])
  out = _neighbors(m, 'A', depth=1)
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1'}
  assert out['truncated'] is False


def test_neighbors_depth_two_walks_further():
  m = _module({'A': _node('A'), 'B': _node('B'), 'C': _node('C')},
              [_edge('E1', 'A', 'B'), _edge('E2', 'B', 'C')])
  out = _neighbors(m, 'A', depth=2)
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B', 'C'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1', 'E2'}


def test_neighbors_is_cycle_guarded():
  # A -> B -> A ; a deep walk must terminate and not revisit.
  m = _module({'A': _node('A'), 'B': _node('B')},
              [_edge('E1', 'A', 'B'), _edge('E2', 'B', 'A')])
  out = _neighbors(m, 'A', depth=3)
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1', 'E2'}
  assert out['truncated'] is False


def test_neighbors_breadth_cap_truncates():
  nodes = {g: _node(g) for g in ('A', 'B', 'C', 'D')}
  edges = [_edge('E1', 'A', 'B'), _edge('E2', 'A', 'C'), _edge('E3', 'A', 'D')]
  out = _neighbors(_module(nodes, edges), 'A', depth=1, limit=2)
  assert out['truncated'] is True
  # root + at most (limit-1) discovered = 2 nodes total
  assert len(out['nodes']) == 2


def test_neighbors_direction_out_vs_in():
  m_nodes = {'A': _node('A'), 'B': _node('B')}
  m_edges = [_edge('E1', 'A', 'B')]  # A --out--> B
  out = _neighbors(_module(m_nodes, m_edges), 'A', depth=1, direction='out')
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  # 'in' from A finds nothing (no inbound edge to A)
  incoming = _neighbors(_module(m_nodes, m_edges), 'A', depth=1, direction='in')
  assert {n['key_guid'] for n in incoming['nodes']} == {'A'}
  assert incoming['edges'] == []


def test_neighbors_includes_inactive_node_as_leaf_but_does_not_expand_it():
  # A -> B(inactive) -> C : B is reached (leaf) but never expanded, so C is absent.
  m = _module(
    {'A': _node('A'), 'B': _node('B', active=False), 'C': _node('C')},
    [_edge('E1', 'A', 'B'), _edge('E2', 'B', 'C')],
  )
  out = _neighbors(m, 'A', depth=3)
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1'}


def test_neighbors_kind_filter_restricts_the_walk():
  m = _module(
    {'A': _node('A'), 'B': _node('B'), 'C': _node('C')},
    [_edge('E1', 'A', 'B', kind='cites'), _edge('E2', 'A', 'C', kind='contradicts')],
  )
  out = _neighbors(m, 'A', depth=1, kinds='cites')
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1'}


def test_neighbors_unknown_root_raises():
  with pytest.raises(ValueError):
    _neighbors(_module({'A': _node('A')}, []), 'ZZZ', depth=1)


# ── graph export (induced sub-graph) ────────────────────────────────────────

def test_export_graph_keeps_only_induced_edges():
  # Nodes A,B in project p; X is out-of-project. Edge A->B stays; A->X is dropped
  # because X is not in the node set.
  nodes = {
    'A': _node('A', project='p', ref_count=2),
    'B': _node('B', project='p', ref_count=0),
    'X': _node('X', project='other'),
  }
  edges = [_edge('E1', 'A', 'B'), _edge('E2', 'A', 'X')]
  out = asyncio.run(_module(nodes, edges).export_graph(project='p'))
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'B'}
  assert {e['edge_guid'] for e in out['edges']} == {'E1'}


def test_export_graph_folds_in_general():
  nodes = {
    'A': _node('A', project='p'),
    'G': _node('G', project='general'),
    'O': _node('O', project='other'),
  }
  out = asyncio.run(_module(nodes, []).export_graph(project='p'))
  assert {n['key_guid'] for n in out['nodes']} == {'A', 'G'}


# ── edge maintenance: not-found paths raise ─────────────────────────────────

def _module_edge_query(found):
  m = MemoryModule.__new__(MemoryModule)

  async def _ready():
    return None

  async def _run(name, params=()):
    row = {'edge_guid': params[0], 'to_guid': 'B', 'ref_count': 1, 'found': 1} \
      if found else {'found': 0}
    return _FakeResult([row])

  m.on_ready = _ready
  m._run_query = _run
  return m


def test_remove_reference_returns_recompute_payload():
  out = asyncio.run(_module_edge_query(found=True).remove_reference('E1'))
  assert out == {'edge_guid': 'E1', 'to_guid': 'B', 'ref_count': 1}


def test_remove_reference_unknown_edge_raises():
  with pytest.raises(ValueError):
    asyncio.run(_module_edge_query(found=False).remove_reference('E1'))


def test_update_reference_validates_kind_before_running():
  # An invalid kind must fail loud before any query runs.
  with pytest.raises(ValueError):
    asyncio.run(_module_edge_query(found=True).update_reference('E1', kind='endorses'))


def test_update_reference_unknown_edge_raises():
  with pytest.raises(ValueError):
    asyncio.run(_module_edge_query(found=False).update_reference('E1', weight=2.0))


# ── migration invariant: ref_count recompute stays symmetric ────────────────

def test_remove_and_update_recompute_uses_same_reinforcing_kinds():
  """remove and update must recompute ref_count with the SAME cites/supports
  set that add uses — otherwise authority drifts. Guard the migration text."""
  repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  path = os.path.join(repo, 'migrations', 'v0.13.6.0_memory_graph_read.sql')
  with open(path, encoding='utf-8') as f:
    sql = f.read()
  # Both maintenance queries recompute with the cites/supports reinforcing set.
  assert sql.count("pub_ref_kind IN (N''cites'', N''supports'')") >= 2
