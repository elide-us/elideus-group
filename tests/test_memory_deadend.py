"""Unit tests for the dead-end bank (v0.13.13.0).

Pure logic — no DB. Guards the two halves of the feature that live in Python:

  * MemoryModule._validate_verdict, which mirrors the biconditional
    CK_agent_memory_entries_verdict so a caller gets a sentence naming the fix
    instead of a raw SQL 547.
  * The 'attempted_for' edge kind's membership in the vocabulary — it must be
    accepted, must be traversed by default (semantic, not structural), and must
    not be mistaken for an authority-conferring kind.

The DB constraint remains the authority for verdicts; these tests guard the
friendly gate in front of it, and the migration asserts the constraint itself.
"""

import pytest

from server.modules.memory_module import (
  MemoryModule,
  _BASE_CONFIDENCE,
  _DEADEND_KIND,
  _STRUCTURAL_REF_KINDS,
  _VALID_REF_KINDS,
  _VALID_VERDICTS,
)

verdict = MemoryModule._validate_verdict


# ── The verdict biconditional ───────────────────────────────────────────────

def test_deadend_accepts_each_valid_verdict():
  for value in _VALID_VERDICTS:
    assert verdict(_DEADEND_KIND, value) == value


def test_deadend_without_a_verdict_is_rejected():
  # The anti-superstition guard. A dead end with no verdict is one nobody can
  # ever safely retire, which turns a record of what failed into a permanent
  # block on what might now work.
  with pytest.raises(ValueError, match='requires a verdict'):
    verdict(_DEADEND_KIND, None)


def test_deadend_with_an_empty_verdict_is_rejected_like_a_missing_one():
  # Whitespace must not satisfy the constraint by arriving as a truthy string.
  for blank in ('', '   ', '\t'):
    with pytest.raises(ValueError, match='requires a verdict'):
      verdict(_DEADEND_KIND, blank)


def test_verdict_on_a_non_deadend_kind_is_rejected():
  with pytest.raises(ValueError, match="only valid on kind='deadend'"):
    verdict('decision', 'fundamental')


def test_non_deadend_without_a_verdict_is_fine():
  for kind in ('rule', 'decision', 'incident', 'spec', 'note'):
    assert verdict(kind, None) is None


def test_unknown_verdict_is_rejected_not_coerced():
  # Silently coercing 'permanent' to 'fundamental' would record a confident,
  # wrong grading — the same reasoning _validate_node_state raises on.
  with pytest.raises(ValueError, match='Invalid verdict'):
    verdict(_DEADEND_KIND, 'permanent')


def test_verdict_is_normalised_case_and_whitespace_insensitively():
  assert verdict(_DEADEND_KIND, '  Fundamental ') == 'fundamental'
  assert verdict('  DeadEnd  ', 'CONDITIONAL') == 'conditional'


def test_unknown_verdict_error_names_the_valid_values():
  # The message is the caller's only guidance; it must carry the vocabulary.
  with pytest.raises(ValueError) as exc:
    verdict(_DEADEND_KIND, 'nope')
  for value in _VALID_VERDICTS:
    assert value in str(exc.value)


def test_kindless_patch_validates_the_value_but_not_the_pairing():
  # memory_update may patch without restating the kind. The value is still
  # checked; the pairing cannot be, so the DB constraint is the backstop.
  assert verdict(None, 'conditional') == 'conditional'
  assert verdict(None, None) is None
  with pytest.raises(ValueError, match='Invalid verdict'):
    verdict(None, 'sideways')


def test_restating_deadend_kind_requires_the_verdict():
  # Deliberate fail-closed: without reading the row there is no way to tell
  # "promoting a note to a deadend" from "restating an existing deadend's kind",
  # and requiring the verdict is the safe side of that ambiguity.
  with pytest.raises(ValueError, match='requires a verdict'):
    verdict(_DEADEND_KIND, None)


# ── The attempted_for edge ──────────────────────────────────────────────────

def test_attempted_for_is_a_valid_edge_kind():
  assert MemoryModule._validate_ref_kind('attempted_for') == 'attempted_for'


def test_attempted_for_is_semantic_so_traversal_follows_it_by_default():
  # Walking out from a problem entry must reach the approaches already tried on
  # it. If attempted_for were structural, the default traversal would skip it
  # and the graph would hide exactly what this feature exists to surface.
  assert 'attempted_for' not in _STRUCTURAL_REF_KINDS
  assert 'attempted_for' in MemoryModule._traversal_kinds(None)


def test_attempted_for_survives_the_kinds_filter_normaliser():
  assert MemoryModule._normalise_kinds('attempted_for') == 'attempted_for'
  assert MemoryModule._normalise_kinds(
    'attempted_for, supersedes') == 'attempted_for,supersedes'


def test_attempted_for_confers_no_authority():
  # pub_ref_count counts cites/supports only (v0.13.3.0
  # memory.entries.recompute_refcount). A failed attempt must never reinforce
  # the claim it targeted.
  assert 'attempted_for' not in ('cites', 'supports')


def test_edge_vocabulary_has_no_duplicates():
  assert len(_VALID_REF_KINDS) == len(set(_VALID_REF_KINDS))


# ── Kind wiring ─────────────────────────────────────────────────────────────

def test_deadend_carries_an_observed_event_confidence():
  # A dead end is watched, not inferred — it should not land on the unknown-kind
  # default the way an unregistered kind would.
  assert _BASE_CONFIDENCE[_DEADEND_KIND] == 0.90


def test_deadend_kind_constant_matches_the_stored_value():
  # The migration's CHECK constraint and the search tool description both spell
  # it this way; a drift here silently disables every deadend write.
  assert _DEADEND_KIND == 'deadend'
