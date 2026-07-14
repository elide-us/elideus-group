"""Unit tests for the anti-decay consult loop (FDD-ORACLE-MEM-CONFLICT-01 Phase 2).

Pure logic — no DB. Covers the edge-kind / resolution validators, the consult
default kinds, and the authority formula (which must mirror the SQL in
memory.entries.consult).
"""

import pytest

from server.modules.memory_module import (
  MemoryModule,
  _VALID_REF_KINDS,
  _VALID_RESOLUTIONS,
  _CONSULT_DEFAULT_KINDS,
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


def test_consult_defaults_to_rule_kinds():
  assert _CONSULT_DEFAULT_KINDS == 'invariant,decision,spec'
