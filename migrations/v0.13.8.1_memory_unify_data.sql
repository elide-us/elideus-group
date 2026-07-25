-- ============================================================================
-- elideus-group v0.13.8.1 — Memory Unification: Part B data migration
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 §4 B2-B6 (step 4 of §7)
--
-- PREREQUISITES, in order:
--   1. v0.13.8.0_memory_unify_foundation.sql applied, PHASE 6 green
--   2. scripts/load_memory_documents.py --apply          (B0.6)
--   3. scripts/extract_memory_wikilinks.py --apply       (B1)
--   B2 recomputes counts FROM the edge table, so B1 must have promoted the
--   inline [[8HEX]] citations into real edges first or the counts will be
--   recomputed against the pre-migration graph and B3 will seed a floor that
--   is too low. B3 cannot be re-run to fix that (see below).
--
-- This script does not read or write pub_body. B4 sets pub_node_state only.
--
-- Idempotent, with one deliberate exception that is guarded rather than
-- repeatable: B3.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- B2: Recompute derived counts from the edge table
--   Semantic edges only — structural edges (contains/next) are spec-section
--   chaining and must not inflate authority.
-- ============================================================================

UPDATE e SET
    e.pub_ref_count    = x.cnt,
    e.priv_last_ref_on = x.last_on
FROM [dbo].[agent_memory_entries] e
CROSS APPLY (
    SELECT COUNT(*) AS cnt, MAX(r.priv_created_on) AS last_on
      FROM [dbo].[agent_memory_references] r
     WHERE r.ref_to_guid       = e.key_guid
       AND r.pub_is_active     = 1
       AND r.pub_is_structural = 0
) x;
GO

SELECT N'B2 recomputed' AS [step],
       COUNT(*) AS [entries],
       SUM(CASE WHEN pub_ref_count > 0 THEN 1 ELSE 0 END) AS [with_inbound],
       MAX(pub_ref_count) AS [max_ref_count]
  FROM [dbo].[agent_memory_entries];
GO


-- ============================================================================
-- B3: Seed the accrual ledger  — RUN ONCE, NEVER AGAIN
--   pub_accrual is a monotonic incident ledger: nothing may decrement it, and
--   re-running this would silently overwrite accumulated increments with the
--   current (lower) inbound count, destroying the ledger.
--   Guard: only fires while the ledger is untouched (every row still 0).
--   Seeding from the measured inbound count rather than mining narrative
--   history means every subsequent increment is an observed event, not a guess.
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entries] WHERE [pub_accrual] > 0)
BEGIN
    UPDATE [dbo].[agent_memory_entries] SET [pub_accrual] = [pub_ref_count];
    PRINT 'B3: accrual ledger seeded from pub_ref_count.';
END
ELSE
    PRINT 'B3: SKIPPED — ledger already seeded (some pub_accrual > 0). This is correct on a re-run.';
GO


-- ============================================================================
-- B4: Flag legacy
--   No batch decomposition. Cold nodes stay cold; the WITH NOCHECK size cap
--   forces decomposition on first update, and the sleep cycle queues proposals
--   for the hot ones.
-- ============================================================================

UPDATE [dbo].[agent_memory_entries]
   SET [pub_node_state] = N'legacy'
 WHERE LEN([pub_body]) > 15000
   AND [pub_node_state] = N'active';
GO

SELECT N'B4 flagged legacy' AS [step], COUNT(*) AS [legacy_entries]
  FROM [dbo].[agent_memory_entries] WHERE [pub_node_state] = N'legacy';
GO


-- ============================================================================
-- B5: Orphan sweep
--   FK_agent_memory_references_from / _to already guarantee both endpoints
--   resolve to a live entry, so a GUID-orphaned edge is structurally
--   impossible. This is therefore a verification, not a repair: it asserts the
--   invariant rather than pretending to fix it. An UPDATE here could never
--   fire, and writing one would imply a risk that the schema has already
--   eliminated.
-- ============================================================================

SELECT N'B5 orphan edges (expect 0)' AS [step], COUNT(*) AS [orphans]
  FROM [dbo].[agent_memory_references] r
 WHERE NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entries] e WHERE e.key_guid = r.ref_from_guid)
    OR NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entries] e WHERE e.key_guid = r.ref_to_guid);
GO


-- ============================================================================
-- B6: Verification gate — every check below must return its expected value
--     before Part C deploys.
-- ============================================================================

-- Non-blocking: inline links remain in legacy bodies. B1 promoted them to real
-- edges but deliberately did not rewrite prose, because that is a body edit.
SELECT N'entries still containing [[  (reported, non-blocking)' AS [check],
       COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] WHERE [pub_body] LIKE N'%[[%';

SELECT N'self-edges (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_references] WHERE [ref_from_guid] = [ref_to_guid];

-- pub_ref_count must equal the recomputed value for every row.
SELECT N'ref_count drift (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] e
 CROSS APPLY (
    SELECT COUNT(*) AS cnt FROM [dbo].[agent_memory_references] r
     WHERE r.ref_to_guid = e.key_guid AND r.pub_is_active = 1 AND r.pub_is_structural = 0
 ) x
 WHERE e.pub_ref_count <> x.cnt;

-- The ledger is a floor: accrual may exceed inbound count, never trail it.
SELECT N'accrual below ref_count (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] WHERE [pub_accrual] < [pub_ref_count];

SELECT N'kind outside enum (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries]
 WHERE [pub_kind] NOT IN (N'rule',N'decision',N'invariant',N'spec',N'note',N'session_summary',
                          N'snippet',N'reference',N'incident',N'concept',N'conflict');

-- Guaranteed by FK_amed_entry's composite (key_guid, pub_kind) reference.
SELECT N'document links w/ mismatched kind (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entry_documents] ed
  JOIN [dbo].[agent_memory_entries] e ON e.key_guid = ed.ref_entry_guid
 WHERE e.pub_kind <> ed.pub_entry_kind;

-- V6b: a spec without verbatim text is a summary, not a spec. Each row here is
-- a durability defect and belongs in the maintenance queue as missing_document.
SELECT N'specs with NO document (work queue)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] e
 WHERE e.pub_kind = N'spec'
   AND NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entry_documents] ed
                    WHERE ed.ref_entry_guid = e.key_guid AND ed.pub_is_active = 1);

SELECT e.key_guid, e.pub_project, e.pub_title, e.pub_source
  FROM [dbo].[agent_memory_entries] e
 WHERE e.pub_kind = N'spec'
   AND NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entry_documents] ed
                    WHERE ed.ref_entry_guid = e.key_guid AND ed.pub_is_active = 1)
 ORDER BY e.pub_project, e.pub_title;

-- Hash verification is NOT done here, deliberately.
--   pub_content_sha256 is the SHA-256 of the source file's UTF-8 bytes.
--   pub_document is NVARCHAR(MAX) (UTF-16), and HASHBYTES over
--   CONVERT(VARCHAR(MAX), ...) would hash a codepage-converted string instead,
--   producing a different digest. 55 of the 58 recovered documents contain
--   non-ASCII, so that check would report 55 false mismatches and train the
--   reader to ignore it.
--   Verify with the tool that computed the digest:
--       python scripts/load_memory_documents.py --verify
-- What IS checkable here: UTF-8 length can never be less than the character
-- count, so a row failing this has a byte_length that does not describe its text.
SELECT N'document byte_length implausible (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_documents]
 WHERE [pub_byte_length] < DATALENGTH([pub_document]) / 2;

SELECT N'documents by fidelity' AS [check], [pub_fidelity], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_documents] GROUP BY [pub_fidelity];


-- ============================================================================
-- Post-migration authority snapshot.
--   Ranking is confidence * (1 + LOG(1 + accrual)); the log damping stops a hot
--   rule with hundreds of inbound edges from crowding out the specific node a
--   traversal is actually looking for. Applied in Part C — shown here so the
--   ordering can be eyeballed against the flat pre-migration one.
-- ============================================================================

SELECT TOP 20
       LEFT(CONVERT(CHAR(36), [key_guid]), 8) AS [guid],
       [pub_project], [pub_kind], [pub_ref_count], [pub_accrual],
       CAST([pub_confidence] * (1 + LOG(1 + [pub_accrual])) AS DECIMAL(10,4)) AS [authority],
       LEFT([pub_title], 72) AS [title]
  FROM [dbo].[agent_memory_entries]
 WHERE [pub_kind] = N'rule' AND [pub_node_state] = N'active'
 ORDER BY [authority] DESC, [pub_ref_count] DESC;
