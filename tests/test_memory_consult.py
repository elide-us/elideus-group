"""Unit tests for the anti-decay consult loop (FDD-ORACLE-MEM-CONFLICT-01 Phase 2).

Pure logic — no DB. Covers the edge-kind / resolution validators, the consult
signature, and the authority formula (which must mirror the SQL in
memory.entries.consult).
"""

import inspect

import pytest

from server.modules.memory_module import (
  MemoryModule,
  _VALID_REF_KINDS,
  _VALID_RESOLUTIONS,
)

ref_kind = MemoryModule._validate_ref_kind
resolution = MemoryModule._validate_resolution
authority = MemoryModule._authority


# ── reference-edge kind validation ─────────────────────────────────────────

def test_ref_kind_defaults_to_cites():
  assert ref_kind(None) == 'cites'
  assert ref_kind('') == 'cites'


def test_ref_kind_normalises_case_and_whitespace():
  assert ref_kind('  Supports ') == 'supports'


def test_every_valid_ref_kind_passes():
  for k in _VALID_REF_KINDS:
    assert ref_kind(k) == k


def test_invalid_ref_kind_raises():
  with pytest.raises(ValueError):
    ref_kind('endorses')


# ── contradiction resolution validation ────────────────────────────────────

def test_every_valid_resolution_passes():
  for r in _VALID_RESOLUTIONS:
    assert resolution(r) == r


def test_resolution_normalises_case():
  assert resolution('Correction') == 'correction'


def test_missing_or_unknown_resolution_raises():
  for bad in (None, '', 'ignore', 'merge'):
    with pytest.raises(ValueError):
      resolution(bad)


def test_resolution_set_is_exactly_the_fdd_five():
  assert set(_VALID_RESOLUTIONS) == {
    'correction', 'new_version', 'typo', 'contradiction', 'misunderstanding',
  }


# ── authority formula (must mirror memory.entries.consult SQL) ──────────────

def test_authority_is_confidence_times_one_plus_refcount():
  assert authority(0.90, 0) == pytest.approx(0.90)
  assert authority(0.90, 1) == pytest.approx(1.80)
  assert authority(0.60, 4) == pytest.approx(3.00)


def test_reinforcement_can_outrank_higher_base_confidence():
  # A 0.60 note referenced 3x (authority 2.4) outranks a fresh 0.90 invariant
  # (authority 0.90). That is the anti-decay point: reinforcement wins.
  assert authority(0.60, 3) > authority(0.90, 0)


def test_consult_memory_dropped_the_kinds_and_project_params():
  # v0.13.4.0: consult (memory_coderules) filters by the 'rule' tag, not kind,
  # so the kinds knob is gone. v0.13.14.0: project is a label, not a partition,
  # so the project knob is gone too — rules are universal. query/limit remain.
  params = inspect.signature(MemoryModule.consult_memory).parameters
  assert 'kinds' not in params
  assert 'project' not in params
  assert {'query', 'limit'} <= set(params)


def test_no_read_path_takes_a_project_filter():
  # v0.13.14.0 — the whole point: the bank is one graph. Every READ method
  # is project-blind; project survives only as an optional LABEL on writes.
  for reader in ('search_memory', 'list_recent_memory', 'consult_memory',
                 'list_contradictions', 'export_graph', 'get_memory',
                 'get_neighbors', 'list_references', 'get_thread'):
    params = inspect.signature(getattr(MemoryModule, reader)).parameters
    assert 'project' not in params, reader
    assert 'include_general' not in params, reader
  for writer in ('store_memory', 'create_thread', 'thread_memory', 'open_contradiction'):
    param = inspect.signature(getattr(MemoryModule, writer)).parameters['project']
    assert param.default is None, writer   # optional, never required


def test_project_label_defaults_to_general():
  label = MemoryModule._label_project
  assert label(None) == 'general'
  assert label('') == 'general'
  assert label('   ') == 'general'
  assert label(' flicker ') == 'flicker'
