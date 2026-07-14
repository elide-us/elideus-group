"""Unit tests for the confidence weighting policy (FDD-ORACLE-MEM-CONFLICT-01).

Pure logic — no DB. Guards MemoryModule._resolve_confidence and the per-kind
base weights, which the migration's PHASE 2 backfill mirrors.
"""

from server.modules.memory_module import (
  MemoryModule,
  _BASE_CONFIDENCE,
  _DEFAULT_CONFIDENCE,
)

resolve = MemoryModule._resolve_confidence


def test_per_kind_base_confidence_when_unspecified():
  for kind, expected in _BASE_CONFIDENCE.items():
    value, source = resolve(kind, None, None)
    assert value == expected, kind
    assert source == 'agent'


def test_unknown_kind_falls_back_to_default():
  value, source = resolve('mystery', None, None)
  assert value == _DEFAULT_CONFIDENCE
  assert source == 'agent'


def test_human_source_pins_to_one_but_stays_a_source_property():
  # Human statement with no explicit confidence -> 1.0, source recorded as human.
  value, source = resolve('note', None, 'human')
  assert value == 1.0
  assert source == 'human'


def test_source_is_normalised_case_insensitively():
  value, source = resolve('note', None, '  Human ')
  assert value == 1.0
  assert source == 'human'


def test_unknown_source_coerced_to_agent():
  # A bogus source must not silently unlock the human 1.0 path.
  value, source = resolve('invariant', None, 'wizard')
  assert source == 'agent'
  assert value == _BASE_CONFIDENCE['invariant']


def test_derived_source_uses_base_weight_not_one():
  value, source = resolve('spec', None, 'derived')
  assert source == 'derived'
  assert value == _BASE_CONFIDENCE['spec']


def test_explicit_confidence_is_honoured():
  value, source = resolve('note', 0.42, None)
  assert value == 0.42
  assert source == 'agent'


def test_explicit_confidence_is_clamped_to_unit_interval():
  assert resolve('note', 5.0, None)[0] == 1.0
  assert resolve('note', -3.0, None)[0] == 0.0


def test_non_numeric_confidence_falls_back_to_default():
  value, _ = resolve('note', 'not-a-number', None)
  assert value == _DEFAULT_CONFIDENCE


def test_base_confidence_values_are_valid_scalars():
  # Every seeded weight must itself be a legal 0..1 confidence.
  for kind, weight in _BASE_CONFIDENCE.items():
    assert 0.0 <= weight <= 1.0, kind
