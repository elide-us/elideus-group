-- ============================================================================
-- elideus-group v0.13.12.0 — page memory.threads.get
-- Date: 2026-07-25
-- Implements: the last unbounded read in the memory surface.
--
-- WHY
--   v0.13.11.0 turned thread entries into stubs and took a live call on thread
--   025FFA03 from 376,572 characters to 81,846 — a 76% cut, and the payload is
--   now entirely metadata and excerpts with no wasted bytes. It is still 82KB,
--   because the query has NO LIMIT: it returns every entry a thread has ever
--   held. That thread holds 98 and grows every session, so the number only goes
--   up. Stubs cannot fix an unbounded row count; only paging can.
--
--   This is the same fix memory.entries.search already has. entry_count is
--   already returned, so a caller can page deliberately instead of discovering
--   the size by being handed all of it.
--
--   Default limit 20 matches _DEFAULT_LIMIT elsewhere in the module: ~17KB for
--   a thread listing, which is an orientation read, not a bulk export.
--
-- PARAMS 1 -> 3: thread_guid, limit, offset
--
-- !! DEPLOY ORDER !!  Apply -> deploy the matching memory_module.py -> restart.
-- Modules cache queries at startup (memory entry 18057D9A).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @g UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @limit INT  = ?;
DECLARE @offset INT = ?;
SELECT t.key_guid, t.pub_project, t.pub_title, t.pub_summary, t.pub_is_active,
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
        OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY
        FOR JSON PATH, INCLUDE_NULL_VALUES) AS entries
FROM [dbo].[agent_memory_threads] t
WHERE t.key_guid = @g
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'thread_guid,limit,offset',
  [pub_description]     = N'Fetch a thread plus a PAGE of entry stubs (excerpt + body_length, no pub_body), newest first, with entry_count for paging. A thread listing is orientation — read a specific entry with memory_get.'
WHERE [pub_name] = N'memory.threads.get';
GO


-- ============================================================================
-- Verification — positive markers only. An earlier migration asserted with
-- NOT LIKE '%e.pub_body,%' and failed on a CORRECT query, because
-- LEFT(e.pub_body, 300) contains that substring. Markers below appear only in
-- the paged version.
-- ============================================================================

SELECT N'threads.get is paged' AS [check],
       CASE WHEN pub_query_text LIKE N'%FETCH NEXT @limit%'
             AND pub_query_text LIKE N'%pub_body_excerpt%'
             AND pub_query_text LIKE N'%entry_count%'
            THEN N'PASS' ELSE N'FAIL' END AS [result],
       pub_parameter_names
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.threads.get';

-- What the largest thread now costs at the default page size, against what it
-- cost before stubs (376,572 chars measured live) and after stubs (81,846).
SELECT TOP 5 t.pub_title,
       COUNT(e.key_guid) AS entries,
       SUM(CASE WHEN DATALENGTH(e.pub_body) / 2 > 300
                THEN 300 ELSE DATALENGTH(e.pub_body) / 2 END) AS stub_chars_all,
       CASE WHEN COUNT(e.key_guid) > 20 THEN 20 ELSE COUNT(e.key_guid) END AS entries_per_page
  FROM [dbo].[agent_memory_threads] t
  JOIN [dbo].[agent_memory_entries] e
    ON e.ref_thread_guid = t.key_guid AND e.pub_is_active = 1
 GROUP BY t.key_guid, t.pub_title
 ORDER BY COUNT(e.key_guid) DESC;
GO
