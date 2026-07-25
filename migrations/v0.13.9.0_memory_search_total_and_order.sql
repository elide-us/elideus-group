-- ============================================================================
-- elideus-group v0.13.9.0 — memory_search: honest total + ordering modes
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 §C5 (paging fix) and the §C1 groundwork
--             that lets one memory_search absorb memory_coderules and
--             memory_list_recent.
--
-- ---------------------------------------------------------------------------
-- C5 — THE PAGING BUG, precisely
--   The old query carried the match count as a window function on each row:
--       COUNT(*) OVER() AS total
--   ... and memory_module.search_memory read it off the FIRST ROW:
--       total = int(rows[0].get('total') or 0) if rows else 0
--   So the count only exists while at least one row survives paging. An OFFSET
--   past the end returns zero rows, the total goes with them, and the caller
--   gets {entries: [], total: 0} — identical to "nothing matched". A client
--   cannot tell "you have paged off the end of 340 results" from "your search
--   found nothing", which is what makes client-side paging impossible.
--
--   The count was never computed after OFFSET, as one might assume from the
--   symptom — it was computed correctly and then discarded with the rows.
--
--   FIX: return a single object whose total is independent of the page:
--       {"total": <int>, "entries": [...]}
--   `filtered` is evaluated for the count and for the page separately, so an
--   empty page still reports the true total. entries is COALESCEd to [] so the
--   shape never varies.
--
-- ---------------------------------------------------------------------------
-- ORDERING MODES (@order)
--   relevance (default) — distinct query terms matched, then recency. A
--                         query-less browse falls through to recency, since
--                         match_count is 0 for every row.
--   authority           — confidence * (1 + LOG(1 + accrual)), the §A4 ranking.
--                         With kind='rule' this reproduces the memory_coderules
--                         bank exactly, which is what lets §C1 retire that tool.
--   recent              — priv_modified_on, reproducing memory_list_recent.
--
--   Authority uses pub_accrual, NOT pub_ref_count. accrual is the monotonic
--   ledger: it survives a link being retracted, so ranking does not lurch when
--   an edge is deactivated. The LOG damping stops a rule with a large inbound
--   count from crowding out the specific node a search is actually for.
--   No recency term, per §A4 — the corpus spans ~10 days and a decay curve over
--   that has no signal in it.
--
-- @node_state — defaults to 'active' when NULL. Passing it explicitly is what
--   makes memory_search(kind='conflict', node_state='draft') the open-conflicts
--   list from §A10, replacing memory_conflicts_list.
--
-- ---------------------------------------------------------------------------
-- @include_body — SEARCH IS A LOCATOR, NOT A READER (default 0)
--   §C3 says never summarise on read, and that stands for memory_get: a node
--   you asked for comes back verbatim. But applying it to SEARCH reproduces the
--   symptom this whole FDD opens with — a 10-entry list_recent measured 51KB,
--   and 20 hits at the 15000-char cap is ~300k characters of payload to answer
--   "which entry is it?". Bounded traversal caps memory_get depth; nothing
--   capped search.
--
--   Default now returns a STUB: pub_body_excerpt (300 chars) + body_length,
--   with pub_body NULL. include_body=1 restores verbatim bodies.
--
--   The excerpt is a SEPARATE COLUMN, never a truncated pub_body. Writing 300
--   chars into pub_body would hand callers something that looks like the body
--   and is not — the exact failure (a lossy summary passing as the real thing)
--   that cost these documents 68% of their text at import. A caller reading
--   pub_body gets the whole body or an explicit NULL; body_length always states
--   what is being withheld. This mirrors the neighbour STUBS already in §C1.
--
-- ---------------------------------------------------------------------------
-- PARAMS 7 -> 10:
--   query,project,kind,tags,tags_like,node_state,order,include_body,offset,limit
--
-- !! DEPLOY ORDER !!  Modules cache system_objects_queries at STARTUP and never
-- reload (see memory entry 18057D9A). Apply this migration, deploy the matching
-- memory_module.py, THEN restart the app. Old code (7 params) against this query
-- (10 params), or new code against the old query, both fail. The window between
-- migration and restart is safe: the running process keeps using its cached copy.
--
-- Idempotent UPDATE.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @query NVARCHAR(MAX)     = ?;
DECLARE @project NVARCHAR(128)    = ?;
DECLARE @kind NVARCHAR(32)        = ?;
DECLARE @tags NVARCHAR(512)       = ?;
DECLARE @tags_like NVARCHAR(512)  = ?;
DECLARE @node_state NVARCHAR(24)  = ?;
DECLARE @order NVARCHAR(16)       = ?;
DECLARE @include_body BIT         = ?;
DECLARE @offset INT               = ?;
DECLARE @limit INT                = ?;

WITH filtered AS (
  SELECT e.key_guid, e.ref_thread_guid, e.pub_project, e.pub_kind, e.pub_title, e.pub_body,
         e.pub_tags, e.pub_source, e.pub_confidence, e.pub_confidence_source,
         e.pub_node_state, e.pub_ref_count, e.pub_accrual, e.pub_canonical_name,
         e.pub_is_active, e.priv_created_on, e.priv_modified_on,
         m.match_count,
         CAST(e.pub_confidence * (1 + LOG(1 + e.pub_accrual)) AS DECIMAL(12,5)) AS authority
  FROM [dbo].[agent_memory_entries] e
  CROSS APPLY (
    SELECT COUNT(DISTINCT LTRIM(RTRIM(s.value))) AS match_count
    FROM STRING_SPLIT(COALESCE(@query, N''''), N'' '') s
    WHERE LTRIM(RTRIM(s.value)) <> N''''
      AND (e.pub_title LIKE N''%'' + s.value + N''%''
           OR e.pub_body LIKE N''%'' + s.value + N''%''
           OR COALESCE(e.pub_tags, N'''') LIKE N''%'' + s.value + N''%'')
  ) m
  WHERE e.pub_node_state = COALESCE(@node_state, N''active'')
    AND (@query IS NULL OR LTRIM(RTRIM(@query)) = N'''' OR m.match_count > 0)
    AND (@project IS NULL OR e.pub_project = @project)
    AND (@kind IS NULL OR e.pub_kind = @kind)
    AND (@tags IS NULL OR e.pub_tags LIKE @tags_like)
)
SELECT
  (SELECT COUNT(*) FROM filtered) AS total,
  JSON_QUERY(COALESCE((
    SELECT f.key_guid, f.ref_thread_guid, f.pub_project, f.pub_kind, f.pub_title,
           CASE WHEN @include_body = 1 THEN f.pub_body END AS pub_body,
           CASE WHEN @include_body = 1 THEN NULL
                ELSE LEFT(f.pub_body, 300) END AS pub_body_excerpt,
           DATALENGTH(f.pub_body) / 2 AS body_length,
           f.pub_tags, f.pub_source, f.pub_confidence, f.pub_confidence_source,
           f.pub_node_state, f.pub_ref_count, f.pub_accrual, f.pub_canonical_name,
           f.pub_is_active, f.priv_created_on, f.priv_modified_on,
           f.match_count, f.authority
    FROM filtered f
    ORDER BY
      CASE WHEN @order = N''authority'' THEN f.authority END DESC,
      CASE WHEN @order = N''recent'' THEN f.priv_modified_on END DESC,
      CASE WHEN @order IS NULL OR @order NOT IN (N''authority'', N''recent'')
           THEN f.match_count END DESC,
      f.priv_modified_on DESC
    OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY
    FOR JSON PATH, INCLUDE_NULL_VALUES), N''[]'')) AS entries
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'query,project,kind,tags,tags_like,node_state,order,include_body,offset,limit',
  [pub_description]     = N'Filter and paginate entries. Returns {total, entries[]} where total is the full match count INDEPENDENT of paging, so an offset past the end reports the real total instead of 0. order: relevance|authority|recent. node_state defaults to active. include_body=0 (default) returns pub_body_excerpt (300 chars) + body_length and leaves pub_body null — search is a LOCATOR; read full text with memory_get. include_body=1 returns pub_body verbatim and nulls the excerpt.'
WHERE [pub_name] = N'memory.entries.search';
GO


-- ============================================================================
-- Verification
--   NOTE: the stored query uses ODBC '?' placeholders, which are bound by the
--   driver and are NOT valid T-SQL. It therefore cannot be exercised through
--   sp_executesql. The reproducer below is the same logic with the parameters
--   declared as literals, so it runs directly in SSMS. The ordering modes and
--   the JSON shape get their real test through the live tool after deploy.
-- ============================================================================

SELECT pub_name, pub_parameter_names
  FROM [dbo].[system_objects_queries]
 WHERE pub_name = N'memory.entries.search';   -- expect 10 comma-separated names

-- THE REGRESSION THIS MIGRATION EXISTS TO KILL.
-- Page far past the end of the corpus. Before the fix this reported total 0,
-- indistinguishable from "nothing matched". It must now report the real count
-- with an empty entries array.
DECLARE @query NVARCHAR(MAX)     = NULL;
DECLARE @project NVARCHAR(128)   = N'elideus-group';
DECLARE @kind NVARCHAR(32)       = NULL;
DECLARE @tags NVARCHAR(512)      = NULL;
DECLARE @tags_like NVARCHAR(512) = NULL;
DECLARE @node_state NVARCHAR(24) = NULL;
DECLARE @order NVARCHAR(16)      = N'recent';
DECLARE @include_body BIT        = 0;
DECLARE @offset INT              = 99999;      -- past the end, on purpose
DECLARE @limit INT               = 3;

;WITH filtered AS (
  SELECT e.key_guid, e.pub_project, e.pub_kind, e.pub_title, e.pub_body,
         e.pub_tags, e.pub_confidence, e.pub_accrual, e.priv_modified_on,
         m.match_count,
         CAST(e.pub_confidence * (1 + LOG(1 + e.pub_accrual)) AS DECIMAL(12,5)) AS authority
  FROM [dbo].[agent_memory_entries] e
  CROSS APPLY (
    SELECT COUNT(DISTINCT LTRIM(RTRIM(s.value))) AS match_count
    FROM STRING_SPLIT(COALESCE(@query, N''), N' ') s
    WHERE LTRIM(RTRIM(s.value)) <> N''
      AND (e.pub_title LIKE N'%' + s.value + N'%'
           OR e.pub_body LIKE N'%' + s.value + N'%'
           OR COALESCE(e.pub_tags, N'') LIKE N'%' + s.value + N'%')
  ) m
  WHERE e.pub_node_state = COALESCE(@node_state, N'active')
    AND (@query IS NULL OR LTRIM(RTRIM(@query)) = N'' OR m.match_count > 0)
    AND (@project IS NULL OR e.pub_project = @project)
    AND (@kind IS NULL OR e.pub_kind = @kind)
    AND (@tags IS NULL OR e.pub_tags LIKE @tags_like)
)
SELECT N'offset past end' AS [check],
       (SELECT COUNT(*) FROM filtered) AS [total_MUST_BE_NONZERO],
       (SELECT COUNT(*) FROM (
          SELECT f.key_guid FROM filtered f
           ORDER BY f.priv_modified_on DESC
          OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY) z) AS [rows_on_page_expect_0];

-- Authority ordering, kind='rule' — this is what replaces memory_coderules.
-- Eyeball that it is NOT flat: before Part B, ref_count was 0 almost everywhere
-- and every rule scored the same.
SELECT TOP 10
       LEFT(CONVERT(CHAR(36), key_guid), 8) AS [guid],
       pub_project, pub_ref_count, pub_accrual,
       CAST(pub_confidence * (1 + LOG(1 + pub_accrual)) AS DECIMAL(12,5)) AS authority,
       LEFT(pub_title, 68) AS title
  FROM [dbo].[agent_memory_entries]
 WHERE pub_kind = N'rule' AND pub_node_state = N'active'
 ORDER BY authority DESC, pub_ref_count DESC;
GO
