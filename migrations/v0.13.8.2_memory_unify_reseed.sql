-- ============================================================================
-- elideus-group v0.13.8.2 — Memory Unification: corrective re-seed
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 — repair of a failed B1/B3 sequence
--
-- WHY THIS EXISTS
--   The first Part B run appeared to succeed and did not. Both Python steps
--   (B0.6 document load, B1 wikilink extraction) opened their pyodbc
--   connections with autocommit=False and then issued an explicit
--   BEGIN TRANSACTION. That nests: @@TRANCOUNT went to 2, the explicit COMMIT
--   decremented it to 1 without durably committing, and closing the connection
--   rolled everything back. Each script still printed success, because a
--   connection sees its own uncommitted writes — the post-commit readback ran
--   inside the doomed transaction.
--
--   Consequence chain:
--     B1 rolled back        -> the wikilink edges were never inserted
--     B2 then ran in SSMS   -> pub_ref_count recomputed over the PRE-B1 graph
--     B3 then ran           -> pub_accrual seeded from those too-low counts
--     B3 is one-shot        -> its IF NOT EXISTS (pub_accrual > 0) guard is now
--                              tripped, so it will never re-seed on its own
--
--   The scripts are fixed (autocommit=True, matching seed_workflows.py). This
--   script repairs the ledger.
--
-- PREREQUISITES — run these first, in order, and confirm each:
--   1. python scripts/load_memory_documents.py --apply --project elideus-group
--   2. python scripts/load_memory_documents.py --verify      -> must print PASS
--   3. python scripts/extract_memory_wikilinks.py --apply    -> edges inserted
--   Only then run this script. Running it before step 3 re-seeds the ledger
--   from the same incomplete graph and wastes the correction.
--
-- SAFETY OF RE-SEEDING
--   pub_accrual is monotonic and must never be decremented — but nothing has
--   incremented it yet. Part C is not deployed and the Part D sleep cycle is
--   not running, so the only value it currently holds is the bad B3 seed.
--   Overwriting it now loses nothing real.
--   THIS WINDOW CLOSES WHEN PART C SHIPS. After that, memory_link increments
--   accrual on inactive->active transitions, those increments are observed
--   events, and a blanket re-seed would destroy them. Do not run this script
--   after Part C deploys.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- Pre-flight: refuse to proceed if B1's edges are still missing.
--   B1 promotes inline [[8HEX]] citations to 'cites' edges. If the entries that
--   contain wiki-links have no matching outbound cites edges, B1 did not land
--   and re-seeding now would bake in the same wrong floor.
-- ============================================================================

DECLARE @wikilink_hosts INT = (
    SELECT COUNT(*) FROM [dbo].[agent_memory_entries] WHERE [pub_body] LIKE N'%[[%');
DECLARE @cites_edges INT = (
    SELECT COUNT(*) FROM [dbo].[agent_memory_references]
     WHERE [pub_ref_kind] = N'cites' AND [pub_is_active] = 1);

PRINT CONCAT('entries containing [[ : ', @wikilink_hosts);
PRINT CONCAT('active cites edges    : ', @cites_edges);

IF @wikilink_hosts > 0 AND @cites_edges = 0
BEGIN
    RAISERROR('ABORT: entries contain [[8HEX]] links but there are no cites edges. Run scripts/extract_memory_wikilinks.py --apply first.', 16, 1);
    RETURN;
END
GO


-- ============================================================================
-- B2 (re-run): recompute derived counts over the now-complete edge table.
--   Semantic edges only; structural (contains/next) must not inflate authority.
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


-- ============================================================================
-- B3 (forced re-seed): unguarded ON PURPOSE.
--   The guard in v0.13.8.1 exists to stop an accidental second seed from
--   flattening real accumulated increments. Here the existing values ARE the
--   error being corrected, so the guard is deliberately bypassed.
-- ============================================================================

DECLARE @before_total BIGINT = (SELECT SUM(CAST([pub_accrual] AS BIGINT)) FROM [dbo].[agent_memory_entries]);

UPDATE [dbo].[agent_memory_entries] SET [pub_accrual] = [pub_ref_count];

DECLARE @after_total BIGINT = (SELECT SUM(CAST([pub_accrual] AS BIGINT)) FROM [dbo].[agent_memory_entries]);
PRINT CONCAT('accrual ledger re-seeded: ', @before_total, ' -> ', @after_total,
             '  (delta ', @after_total - @before_total, ')');
GO


-- ============================================================================
-- Verification — the B6 gate, re-run
-- ============================================================================

SELECT N'self-edges (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_references] WHERE [ref_from_guid] = [ref_to_guid];

SELECT N'ref_count drift (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] e
 CROSS APPLY (
    SELECT COUNT(*) AS cnt FROM [dbo].[agent_memory_references] r
     WHERE r.ref_to_guid = e.key_guid AND r.pub_is_active = 1 AND r.pub_is_structural = 0
 ) x
 WHERE e.pub_ref_count <> x.cnt;

SELECT N'accrual below ref_count (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] WHERE [pub_accrual] < [pub_ref_count];

-- These two are the ones that must NOT be zero. A zero here means the Python
-- steps rolled back again.
SELECT N'documents loaded (expect 58)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_documents];

SELECT N'entry<->document links (expect 81)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entry_documents];

SELECT N'specs with NO document (expect 2)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries] e
 WHERE e.pub_kind = N'spec'
   AND NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_entry_documents] ed
                    WHERE ed.ref_entry_guid = e.key_guid AND ed.pub_is_active = 1);

SELECT N'documents by fidelity' AS [check], [pub_fidelity], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_documents] GROUP BY [pub_fidelity];

-- Authority is no longer flat: this ordering should differ from the
-- pre-migration one, which was near-uniform because ref_count was 0 almost
-- everywhere.
SELECT TOP 20
       LEFT(CONVERT(CHAR(36), [key_guid]), 8) AS [guid],
       [pub_project], [pub_ref_count], [pub_accrual],
       CAST([pub_confidence] * (1 + LOG(1 + [pub_accrual])) AS DECIMAL(10,4)) AS [authority],
       LEFT([pub_title], 70) AS [title]
  FROM [dbo].[agent_memory_entries]
 WHERE [pub_kind] = N'rule' AND [pub_node_state] = N'active'
 ORDER BY [authority] DESC, [pub_ref_count] DESC;
