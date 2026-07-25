"""SQL for the memory sleep cycle — ONE definition, two callers.

`scripts/memory_sleep.py` runs these synchronously via pyodbc for a hand run.
`MemoryModule.sleep_cycle()` runs the same statements asynchronously when the
automation scheduler fires the `memory_sleep` workflow. Both import from here.

That is the point: two entry points calling one definition is not duplication.
Duplication would be the maintenance pass existing twice, drifting, and the
scheduled run quietly doing something different from the hand run — the exact
failure rule DDD070C7 describes.

D1 statements are repairs and are safe to execute. D2 statements are SELECTs
only: they identify candidates, and every one becomes a PROPOSAL in
agent_memory_maintenance_queue. Nothing here writes pub_body, and nothing here
touches agent_memory_documents at all.
"""

from __future__ import annotations

BODY_CAP = 15000

# ── D1: mechanical repairs ──────────────────────────────────────────────────

D1_REFCOUNT_DRIFT = """
SELECT COUNT(*) AS drifted FROM dbo.agent_memory_entries e
CROSS APPLY (SELECT COUNT(*) AS cnt FROM dbo.agent_memory_references r
              WHERE r.ref_to_guid = e.key_guid AND r.pub_is_active = 1
                AND r.pub_is_structural = 0) x
WHERE e.pub_ref_count <> x.cnt
"""

D1_REFCOUNT_REPAIR = """
UPDATE e SET e.pub_ref_count = x.cnt, e.priv_last_ref_on = x.last_on
FROM dbo.agent_memory_entries e
CROSS APPLY (SELECT COUNT(*) AS cnt, MAX(r.priv_created_on) AS last_on
               FROM dbo.agent_memory_references r
              WHERE r.ref_to_guid = e.key_guid AND r.pub_is_active = 1
                AND r.pub_is_structural = 0) x
"""

D1_LEGACY_COUNT = """
SELECT COUNT(*) AS found FROM dbo.agent_memory_entries
WHERE LEN(pub_body) > ? AND pub_node_state = N'active'
"""

D1_LEGACY_FLAG = """
UPDATE dbo.agent_memory_entries SET pub_node_state = N'legacy'
WHERE LEN(pub_body) > ? AND pub_node_state = N'active'
"""

# FK_agent_memory_references_from/_to make a GUID-orphaned edge impossible.
# Asserted rather than "repaired" — an UPDATE here could never fire.
D1_ORPHAN_EDGES = """
SELECT COUNT(*) AS found FROM dbo.agent_memory_references r
WHERE NOT EXISTS (SELECT 1 FROM dbo.agent_memory_entries e WHERE e.key_guid = r.ref_from_guid)
   OR NOT EXISTS (SELECT 1 FROM dbo.agent_memory_entries e WHERE e.key_guid = r.ref_to_guid)
"""

# ── D2: proposal candidates (SELECT only) ───────────────────────────────────

D2_OVERSIZED = """
SELECT key_guid, pub_title, LEN(pub_body) AS body_len
FROM dbo.agent_memory_entries
WHERE LEN(pub_body) > ? ORDER BY LEN(pub_body) DESC
"""

D2_DUPLICATE_CANDIDATES = """
SELECT key_guid, pub_title, pub_body FROM dbo.agent_memory_entries
WHERE pub_node_state = N'active' AND LEN(pub_body) > 200
"""

# §C3b: a session_summary is progress state that LINKS OUT. Zero outbound edges
# means it is restating rather than citing.
D2_UNLINKED_SUMMARIES = """
SELECT e.key_guid, e.pub_title FROM dbo.agent_memory_entries e
WHERE e.pub_kind = N'session_summary' AND e.pub_node_state = N'active'
  AND NOT EXISTS (SELECT 1 FROM dbo.agent_memory_references r
                   WHERE r.ref_from_guid = e.key_guid AND r.pub_is_active = 1)
"""

# §A6b. Path-shaped pub_source only; the caller additionally verifies the path
# has git history, because a shaped string is not evidence a document exists.
D2_SPECS_WITHOUT_DOCUMENTS = """
SELECT e.key_guid, e.pub_title, e.pub_source FROM dbo.agent_memory_entries e
WHERE e.pub_kind = N'spec' AND e.pub_node_state = N'active'
  AND e.pub_source IS NOT NULL
  AND (e.pub_source LIKE N'%.md' OR e.pub_source LIKE N'%/%')
  AND NOT EXISTS (SELECT 1 FROM dbo.agent_memory_entry_documents ed
                   WHERE ed.ref_entry_guid = e.key_guid AND ed.pub_is_active = 1)
"""

# ── Queue write ─────────────────────────────────────────────────────────────
# UX_ammq_open makes (op, subject, object) unique WHERE pending, so repeated
# runs cannot pile up duplicates of the same proposal.

QUEUE_EXISTS = """
SELECT COUNT(*) AS n FROM dbo.agent_memory_maintenance_queue
WHERE pub_op = ? AND pub_state = N'pending'
  AND ((ref_subject_guid IS NULL AND ? IS NULL) OR ref_subject_guid = TRY_CAST(? AS UNIQUEIDENTIFIER))
  AND ((ref_object_guid  IS NULL AND ? IS NULL) OR ref_object_guid  = TRY_CAST(? AS UNIQUEIDENTIFIER))
"""

QUEUE_INSERT = """
INSERT INTO dbo.agent_memory_maintenance_queue
  (pub_op, pub_state, ref_subject_guid, ref_object_guid, pub_trigger, pub_rationale)
VALUES (?, N'pending', TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?)
"""
