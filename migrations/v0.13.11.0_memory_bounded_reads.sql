-- ============================================================================
-- elideus-group v0.13.11.0 — bound the last two unbounded reads
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 §C1/§C3 — the "neighbour STUBS" the spec
--             actually specified, which v0.13.10.0 under-implemented.
--
-- WHY
--   After the 18->7 collapse, two reads still returned every body in full:
--
--   1. memory.threads.get  — a live call on thread 025FFA03 returned
--      376,572 characters. That is the exact symptom this FDD opens with
--      ("a five-node memory_list_recent returns ~20k tokens"), still present in
--      a tool that had just been shipped. The tool was collapsed without its
--      query being touched.
--
--   2. memory.entries.get_many — the BFS node payload behind memory_get(depth>0).
--      Bounded traversal caps the NODE COUNT, not the bytes per node: with the
--      50-node neighbour cap and the 15000-char body cap, depth 3 against a hub
--      is ~750,000 characters. Predictable is not the same as acceptable.
--
-- THE RULE THIS ENCODES
--   Verbatim on the node you ASKED for; stubs on the nodes you merely ARRIVED at.
--   §C3's "never summarise on read" governs the node a caller requested — that
--   one still comes back whole from memory_get. Orientation reads (a thread
--   listing, a traversal frontier) exist to answer "which one do I want?", and
--   answering that with a megabyte is the behaviour being corrected.
--
--   As in v0.13.9.0, the excerpt is a SEPARATE column and pub_body is set NULL —
--   never a truncated pub_body. A caller reading pub_body gets the whole body or
--   an explicit null, never a lossy value posing as the real one. body_length
--   always states what is withheld.
--
-- No parameter-list changes, so no paired code change is required beyond the
-- module already deployed. Apply -> restart -> reconnect.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- 1) memory.threads.get — entries become stubs
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT t.key_guid, t.pub_project, t.pub_title, t.pub_summary, t.pub_is_active,
       t.priv_created_on, t.priv_modified_on,
       (SELECT COUNT(*) FROM [dbo].[agent_memory_entries] c
         WHERE c.ref_thread_guid = t.key_guid AND c.pub_is_active = 1) AS entry_count,
       (SELECT e.key_guid, e.pub_project, e.pub_kind, e.pub_title,
               LEFT(e.pub_body, 300) AS pub_body_excerpt,
               DATALENGTH(e.pub_body) / 2 AS body_length,
               e.pub_tags, e.pub_node_state, e.pub_ref_count, e.pub_accrual,
               e.priv_modified_on
        FROM [dbo].[agent_memory_entries] e
        WHERE e.ref_thread_guid = t.key_guid AND e.pub_is_active = 1
        ORDER BY e.priv_modified_on DESC
        FOR JSON PATH, INCLUDE_NULL_VALUES) AS entries
FROM [dbo].[agent_memory_threads] t
WHERE t.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
  [pub_description] = N'Fetch a thread plus STUBS of its active entries (excerpt + body_length, no pub_body) and entry_count. A thread listing is orientation — read a specific entry with memory_get.'
WHERE [pub_name] = N'memory.threads.get';
GO


-- ============================================================================
-- 2) memory.entries.get_many — BFS frontier becomes stubs
--    Still no pub_is_active filter: reached inactive nodes are returned as
--    leaves, which the BFS relies on to stop expanding them.
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @csv NVARCHAR(MAX) = ?;
SELECT key_guid, pub_project, pub_kind, pub_title,
       LEFT(pub_body, 300) AS pub_body_excerpt,
       DATALENGTH(pub_body) / 2 AS body_length,
       pub_tags, pub_confidence, pub_node_state, pub_ref_count, pub_accrual,
       pub_is_active, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE key_guid IN (
      SELECT TRY_CAST(LTRIM(RTRIM(value)) AS UNIQUEIDENTIFIER)
      FROM STRING_SPLIT(@csv, N'','')
      WHERE LTRIM(RTRIM(value)) <> N'''')
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_description] = N'Fetch node STUBS for a CSV of key_guids (BFS/graph assembly): excerpt + body_length, no pub_body. No pub_is_active filter — reached inactive nodes are returned as leaves. The root of a memory_get is fetched separately and verbatim.'
WHERE [pub_name] = N'memory.entries.get_many';
GO


-- ============================================================================
-- 3) Verification — assertions, with expected NON-ZERO values so a partial
--    apply cannot look like success.
-- ============================================================================

-- POSITIVE MARKERS ONLY. An earlier draft added `NOT LIKE '%e.pub_body,%'` to
-- assert the bare column was gone — but LEFT(e.pub_body, 300) contains that
-- exact substring, so the assertion failed on a CORRECT query. Both markers
-- below appear only in the stub version and cannot appear in the old one, so a
-- PASS here cannot be a false positive and a FAIL cannot be a false negative.
SELECT N'threads.get returns stubs' AS [check],
       CASE WHEN pub_query_text LIKE N'%pub_body_excerpt%'
             AND pub_query_text LIKE N'%body_length%'
            THEN N'PASS' ELSE N'FAIL' END AS [result]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.threads.get';

SELECT N'get_many returns stubs' AS [check],
       CASE WHEN pub_query_text LIKE N'%pub_body_excerpt%'
             AND pub_query_text LIKE N'%body_length%'
            THEN N'PASS' ELSE N'FAIL' END AS [result]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.get_many';

-- Payload the biggest thread would now return, vs what it returned before.
-- Thread 025FFA03 measured 376,572 characters live. Expect a ~90% reduction.
SELECT N'largest thread stub payload' AS [check],
       t.pub_title,
       COUNT(e.key_guid)                                   AS entries,
       SUM(DATALENGTH(e.pub_body) / 2)                     AS chars_before,
       SUM(CASE WHEN DATALENGTH(e.pub_body) / 2 > 300
                THEN 300 ELSE DATALENGTH(e.pub_body) / 2 END) AS chars_after
  FROM [dbo].[agent_memory_threads] t
  JOIN [dbo].[agent_memory_entries] e
    ON e.ref_thread_guid = t.key_guid AND e.pub_is_active = 1
 GROUP BY t.key_guid, t.pub_title
 ORDER BY chars_before DESC;
GO
