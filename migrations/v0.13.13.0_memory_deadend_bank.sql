-- ============================================================================
-- elideus-group v0.13.13.0 — the DEAD-END BANK
-- Date: 2026-08-07
--
-- WHY THIS EXISTS
--   The bank records rules, decisions, specs and conflicts. It has no way to
--   say "this approach was tried and it did not work". So a session that
--   reverts an attempt, ends, and is replaced by a fresh session solving the
--   same problem reaches for the most-likely approach — which is the one that
--   was just reverted. The loop is structural, not a lapse of attention.
--
--   The knowledge is already being written down: 3CC28776 (erosion rework
--   reverted), 66B17B51 (removed same day), 5FB3EEF6 (fan approach superseded).
--   Three things are missing, and this migration adds exactly those three:
--
--   1. NO TYPED EDGE from an attempt to the problem it attacked, so "what has
--      been tried for P?" is a free-text search and a hope.
--   2. FAILURE IS NOT MECHANICALLY DISTINGUISHABLE from history. 66B17B51 is
--      kind='decision' with a hand-typed marker in its title. The warning lives
--      in prose, and invariant B84ECCEF measured that advisory constraints do
--      not hold while mechanical ones do.
--   3. NO RETRIEVAL CHANNEL THAT FIRES WITHOUT BEING ASKED. The code-rules bank
--      works because it is a standing consult. Dead ends had no equivalent.
--
-- WHAT LANDS
--   kind='deadend'            a first-class entry kind (A1 enum + 1)
--   edge 'attempted_for'      deadend -> the problem entry (A7 enum + 1)
--   pub_verdict               fundamental | conditional, REQUIRED on a deadend
--   IX_amr_to_kind            the to-side index the two reads below need
--   memory.entries.get        returns attached dead ends UNCONDITIONALLY
--   memory.entries.search     stubs carry deadend_count + pub_verdict
--
-- THE TRIP-WIRE IS THE POINT
--   The dead ends ride on memory.entries.get with NO FLAG TO PASS. You cannot
--   read the entry describing problem P without being handed what has already
--   been tried and reverted on P. A tool argument you must remember to set is
--   the same advisory constraint this migration exists to replace.
--
-- THE FAILURE MODE THIS DESIGN MUST SURVIVE
--   A dead-end bank that never expires becomes a bank of superstitions. Left
--   unguarded it blocks an approach permanently — including after the reason it
--   failed was fixed — turning a retry cost into a silent, permanent loss of
--   capability. That is strictly worse than the loop being closed here. Two
--   mechanical guards, both fail-closed:
--
--   * pub_verdict is REQUIRED on a deadend and forbidden elsewhere (a
--     biconditional CHECK, not a convention). 'conditional' obliges the body to
--     name the condition, so a future session can test whether it still holds.
--   * Both reads filter d.pub_node_state = 'active'. Overturning a dead end is
--     the EXISTING supersession vocabulary — link the new working approach
--     'supersedes' the deadend and flip it to 'historical' — and it then stops
--     warning. Nothing new to learn, and the release valve is a state change
--     rather than a delete, so the history survives.
--
-- ONE RECORDED SIDE-EFFECT (deliberate, not overlooked)
--   MemoryModule.link_memory increments pub_accrual on ANY inactive->active
--   edge, not only cites/supports, and memory.entries.search ranks authority on
--   pub_accrual. So each attempted_for edge raises the PROBLEM entry's search
--   authority. Left as-is: a problem attacked five times legitimately deserves
--   to surface above one attacked never. Recorded here so a later reader finds
--   a decision rather than a surprise. pub_ref_count is untouched — it filters
--   on cites/supports (v0.13.3.0 memory.entries.recompute_refcount), so a
--   failed attempt never reinforces a claim.
--
-- DRIVE-BY (additive, called out rather than smuggled): memory.entries.get also
--   starts returning pub_accrual. It was never added there when v0.13.8.0
--   introduced it, so the field authority is computed from was invisible to the
--   covering read while search showed it.
--
-- PARAM CHANGES — both need the matching memory_module.py:
--   memory.entries.insert   9 -> 10  (verdict appended)
--   memory.entries.update   7 ->  8  (verdict inserted before the key_guids)
--   memory.entries.get      1 ->  1  (unchanged)
--   memory.entries.search  11 -> 11  (unchanged)
--
-- UUID5 namespace (reflection rows): DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   column:agent_memory_entries.pub_verdict
--   index:agent_memory_references.IX_amr_to_kind
--
-- Additive and idempotent (safe to re-run). No pub_body is read or written.
--
-- !! DEPLOY ORDER !!  Apply -> deploy memory_module.py + mcp_io_service_module.py
-- -> restart -> reconnect. Modules cache query text at startup and never reload
-- it (memory entry 18057D9A); the tool list refreshes on reconnect, no new
-- session needed (entry FD26ABA6).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- PHASE 1: Schema — the column, the two enum widenings, the index
-- ============================================================================

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'pub_verdict') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries] ADD [pub_verdict] NVARCHAR(16) NULL;
GO

-- A1 + 'deadend'. DROP/ADD is the only way to widen a CHECK. WITH NOCHECK
-- preserves the grandfathering semantics the original carried in v0.13.8.0 --
-- re-adding WITH CHECK would validate every existing row and fail the migration
-- on any legacy kind, which is exactly the breakage the original avoided.
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_entries_kind')
  ALTER TABLE [dbo].[agent_memory_entries] DROP CONSTRAINT [CK_agent_memory_entries_kind];
GO

ALTER TABLE [dbo].[agent_memory_entries] WITH NOCHECK
  ADD CONSTRAINT [CK_agent_memory_entries_kind] CHECK ([pub_kind] IN (
      N'rule', N'decision', N'invariant', N'spec', N'note',
      N'session_summary', N'snippet', N'reference',
      N'incident', N'concept', N'conflict',
      N'deadend'));                                        -- new in v0.13.13.0
GO

-- A7 + 'attempted_for'. SEMANTIC, not structural: pub_is_structural stays
-- (contains, next), so traversal follows attempted_for by default and walking
-- out from a problem reaches the things already tried on it.
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_references_ref_kind')
  ALTER TABLE [dbo].[agent_memory_references] DROP CONSTRAINT [CK_agent_memory_references_ref_kind];
GO

ALTER TABLE [dbo].[agent_memory_references] WITH NOCHECK
  ADD CONSTRAINT [CK_agent_memory_references_ref_kind] CHECK ([pub_ref_kind] IN (
      N'cites', N'supports', N'supersedes', N'derived_from', N'disambiguates',
      N'contradicts', N'violates', N'contains', N'next',
      N'attempted_for'));                                  -- new in v0.13.13.0
GO

-- The anti-superstition guard, as a biconditional. A deadend CANNOT be banked
-- without stating whether its failure is intrinsic or conditional, and no other
-- kind may carry a verdict. This is the whole reason the verdict is a column and
-- not a heading in the body: a body convention is advisory and would be skipped
-- exactly when the session is in a hurry, which is when dead ends get written.
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_entries_verdict')
  ALTER TABLE [dbo].[agent_memory_entries] DROP CONSTRAINT [CK_agent_memory_entries_verdict];
GO

ALTER TABLE [dbo].[agent_memory_entries] WITH NOCHECK
  ADD CONSTRAINT [CK_agent_memory_entries_verdict] CHECK (
      ([pub_kind] =  N'deadend' AND [pub_verdict] IN (N'fundamental', N'conditional'))
   OR ([pub_kind] <> N'deadend' AND [pub_verdict] IS NULL));
GO

-- IX_amr_from_semantic (v0.13.8.0) covers the FROM side. Both new reads walk
-- the TO side -- "which dead ends point AT this entry" -- and would otherwise
-- scan the edge table once per row of a search page.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_amr_to_kind'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE INDEX [IX_amr_to_kind]
      ON [dbo].[agent_memory_references] ([ref_to_guid], [pub_ref_kind], [pub_is_active])
   INCLUDE ([ref_from_guid]);
GO


-- ============================================================================
-- PHASE 2: Registered queries
-- ============================================================================

-- 2a) memory.entries.insert — verdict appended (9 -> 10 params)
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SET NOCOUNT ON;
DECLARE @guid UNIQUEIDENTIFIER = NEWID();
INSERT INTO [dbo].[agent_memory_entries]
  ([key_guid], [ref_thread_guid], [pub_project], [pub_kind], [pub_title], [pub_body], [pub_tags], [pub_source], [pub_confidence], [pub_confidence_source], [pub_verdict])
VALUES
  (@guid, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, ?, ?, TRY_CAST(? AS DECIMAL(19,5)), ?, ?);
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
  [pub_parameter_names] = N'thread_guid,project,kind,title,body,tags,source,confidence,confidence_source,verdict',
  [pub_description]     = N'Insert a memory entry. verdict is REQUIRED when kind=deadend (fundamental|conditional) and must be NULL otherwise -- enforced by CK_agent_memory_entries_verdict.'
WHERE [pub_name] = N'memory.entries.insert';
GO


-- 2b) memory.entries.update — verdict inserted BEFORE the two trailing
--     key_guid params, which sit in WHERE clauses and must stay last.
--     COALESCE keeps the existing verdict when the param is NULL, so patching a
--     deadend's title does not have to restate its verdict.
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SET NOCOUNT ON;
UPDATE [dbo].[agent_memory_entries]
SET pub_title       = COALESCE(?, pub_title),
    pub_body        = COALESCE(?, pub_body),
    pub_tags        = COALESCE(?, pub_tags),
    pub_kind        = COALESCE(?, pub_kind),
    pub_node_state  = COALESCE(CASE TRY_CAST(? AS BIT) WHEN 1 THEN N''active'' WHEN 0 THEN N''retired'' END, pub_node_state),
    pub_verdict     = COALESCE(?, pub_verdict),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT key_guid
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
  [pub_parameter_names] = N'title,body,tags,kind,is_active,verdict,key_guid,key_guid',
  [pub_description]     = N'Patch a memory entry. COALESCE preserves existing values when a param is NULL. The is_active param drives pub_node_state (1=active, 0=retired); pub_is_active is a computed projection and cannot be written directly. verdict is constrained against pub_kind by CK_agent_memory_entries_verdict. Returns key_guid (empty if not found).'
WHERE [key_guid] = N'654F7A79-F7E9-5CD9-BCF6-28C8A943953B';
GO


-- 2c) memory.entries.get — THE TRIP-WIRE. Dead ends ride along unconditionally.
--     JSON_QUERY(COALESCE(..., ''[]'')) so "no dead ends" is an explicit empty
--     array rather than a null a caller has to interpret -- the same shape
--     memory.entries.search already uses for its entries collection.
--     Params unchanged (1).
--
--     TOP (50) is load-bearing twice over:
--       * T-SQL rejects ORDER BY in a subquery without TOP/OFFSET. The error
--         text names only "TOP, OFFSET or FOR XML", so relying on FOR JSON to
--         satisfy it is an assumption that would apply cleanly here and then
--         break EVERY memory_get at runtime -- the failure shape entry
--         18057D9A exists to warn about. TOP removes the question.
--       * It bounds the read. Every other query in this surface was bounded by
--         v0.13.11.0/v0.13.12.0; an unbounded correlated array on the covering
--         read would have quietly re-opened that.
--     deadend_count is the TRUE total, returned alongside, so a caller can see
--     len(deadends) < deadend_count and know it was capped. A silent cap reads
--     as "that is all of them", which on a warning channel is the worst
--     possible lie.
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @g UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT e.key_guid, e.ref_thread_guid, e.pub_project, e.pub_kind, e.pub_title, e.pub_body,
       e.pub_tags, e.pub_source, e.pub_confidence, e.pub_confidence_source,
       e.pub_verdict, e.pub_node_state, e.pub_ref_count, e.pub_accrual,
       e.pub_is_active, e.priv_created_on, e.priv_modified_on,
       (SELECT COUNT(*)
          FROM [dbo].[agent_memory_references] r
          JOIN [dbo].[agent_memory_entries] d ON d.key_guid = r.ref_from_guid
         WHERE r.ref_to_guid    = e.key_guid
           AND r.pub_ref_kind   = N''attempted_for''
           AND r.pub_is_active  = 1
           AND d.pub_node_state = N''active'') AS deadend_count,
       JSON_QUERY(COALESCE((
         SELECT TOP (50)
                d.key_guid, d.pub_project, d.pub_title, d.pub_verdict,
                LEFT(d.pub_body, 300) AS pub_body_excerpt,
                DATALENGTH(d.pub_body) / 2 AS body_length,
                d.priv_modified_on
           FROM [dbo].[agent_memory_references] r
           JOIN [dbo].[agent_memory_entries] d ON d.key_guid = r.ref_from_guid
          WHERE r.ref_to_guid    = e.key_guid
            AND r.pub_ref_kind   = N''attempted_for''
            AND r.pub_is_active  = 1
            AND d.pub_node_state = N''active''
          ORDER BY d.priv_modified_on DESC
          FOR JSON PATH, INCLUDE_NULL_VALUES), N''[]'')) AS deadends
FROM [dbo].[agent_memory_entries] e
WHERE e.key_guid = @g
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
  [pub_description] = N'Covering read of one entry, verbatim. ALWAYS returns deadends[] (up to 50 stubs, newest first) plus deadend_count (the true total, so a cap is visible) -- the active dead ends linked attempted_for THIS entry. No flag to pass: reading the problem hands you what was already tried and reverted on it. Overturned dead ends (node_state historical/superseded) drop out.'
WHERE [pub_name] = N'memory.entries.get';
GO


-- 2d) memory.entries.search — deadend_count + pub_verdict on the stubs.
--     The count sits in the OUTER projection, not the CTE, so it is computed
--     for the page (<= 100 rows) rather than for every filtered row. Params
--     unchanged (11), so no paired signature change in the module.
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @query NVARCHAR(MAX)      = ?;
DECLARE @project NVARCHAR(128)     = ?;
DECLARE @include_general BIT       = ?;
DECLARE @kind NVARCHAR(32)         = ?;
DECLARE @tags NVARCHAR(512)        = ?;
DECLARE @tags_like NVARCHAR(512)   = ?;
DECLARE @node_state NVARCHAR(24)   = ?;
DECLARE @order NVARCHAR(16)        = ?;
DECLARE @include_body BIT          = ?;
DECLARE @offset INT                = ?;
DECLARE @limit INT                 = ?;

WITH filtered AS (
  SELECT e.key_guid, e.pub_project, e.pub_kind, e.pub_title, e.pub_body,
         e.pub_tags, e.pub_confidence, e.pub_verdict, e.pub_node_state,
         e.pub_ref_count, e.pub_accrual, e.priv_modified_on,
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
    AND (@project IS NULL
         OR e.pub_project = @project
         OR (@include_general = 1 AND e.pub_project = N''general''))
    AND (@kind IS NULL OR e.pub_kind = @kind)
    AND (@tags IS NULL OR e.pub_tags LIKE @tags_like)
)
SELECT
  (SELECT COUNT(*) FROM filtered) AS total,
  JSON_QUERY(COALESCE((
    SELECT f.key_guid, f.pub_project, f.pub_kind, f.pub_title,
           CASE WHEN @include_body = 1 THEN f.pub_body END AS pub_body,
           CASE WHEN @include_body = 1 THEN NULL
                ELSE LEFT(f.pub_body, 300) END AS pub_body_excerpt,
           DATALENGTH(f.pub_body) / 2 AS body_length,
           f.pub_tags, f.pub_confidence, f.pub_verdict, f.pub_node_state,
           f.pub_ref_count, f.pub_accrual, f.authority,
           (SELECT COUNT(*)
              FROM [dbo].[agent_memory_references] r
              JOIN [dbo].[agent_memory_entries] d ON d.key_guid = r.ref_from_guid
             WHERE r.ref_to_guid    = f.key_guid
               AND r.pub_ref_kind   = N''attempted_for''
               AND r.pub_is_active  = 1
               AND d.pub_node_state = N''active'') AS deadend_count,
           f.match_count, f.priv_modified_on
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
  [pub_parameter_names] = N'query,project,include_general,kind,tags,tags_like,node_state,order,include_body,offset,limit',
  [pub_description]     = N'Filter and paginate entries. Returns {total, entries[]}; total is independent of paging. order: relevance|authority|recent. kind=rule + order=authority IS the coderules bank; kind=deadend IS the dead-end bank. Each stub carries deadend_count -- how many active dead ends point attempted_for at it. include_general (default 1) folds the universal general project in alongside @project. include_body=0 returns pub_body_excerpt + body_length with pub_body null.'
WHERE [pub_name] = N'memory.entries.search';
GO


-- ============================================================================
-- PHASE 3: Reflection registration (rule 4B634AAC — direct INSERT with
--   hardcoded EDT type GUIDs; never INFORMATION_SCHEMA discovery).
--   pub_is_active is ordinal 20 after v0.13.8.0 PHASE 3, so pub_verdict is 21.
-- ============================================================================

DECLARE @T_STR       UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2'; -- nvarchar
DECLARE @TBL_ENTRIES UNIQUEIDENTIFIER = N'07B0D4B9-4D3B-569E-926D-551035A6357B';
DECLARE @TBL_REFS    UNIQUEIDENTIFIER = N'0D52ACB1-CE0F-5878-908E-314AD41A0A12';

DELETE FROM [dbo].[system_objects_database_columns]
 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_verdict';
DELETE FROM [dbo].[system_objects_database_indexes]
 WHERE [ref_table_guid] = @TBL_REFS AND [pub_name] = N'IX_amr_to_kind';

INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'91DFB1C8-0EBA-5A5C-B46C-B28B51F112FF',@TBL_ENTRIES,@T_STR,N'pub_verdict',21,1,0,0,NULL,16);

INSERT INTO [dbo].[system_objects_database_indexes]
  ([key_guid],[ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'6108E444-C30B-5497-8251-D3CD6BCBADEF',@TBL_REFS,N'IX_amr_to_kind',N'ref_to_guid,pub_ref_kind,pub_is_active',0);
GO


-- ============================================================================
-- PHASE 4: Verification — ASSERTIONS, not a report. A partial apply must show
--   up as a failing row, never as a plausible-looking table.
-- ============================================================================

SELECT N'kind enum accepts deadend' AS [check],
       CASE WHEN EXISTS (SELECT 1 FROM sys.check_constraints
                          WHERE name = N'CK_agent_memory_entries_kind'
                            AND definition LIKE N'%deadend%')
            THEN N'PASS' ELSE N'FAIL' END AS [result];

SELECT N'ref_kind enum accepts attempted_for' AS [check],
       CASE WHEN EXISTS (SELECT 1 FROM sys.check_constraints
                          WHERE name = N'CK_agent_memory_references_ref_kind'
                            AND definition LIKE N'%attempted[_]for%')
            THEN N'PASS' ELSE N'FAIL' END AS [result];

SELECT N'verdict biconditional present' AS [check],
       CASE WHEN EXISTS (SELECT 1 FROM sys.check_constraints
                          WHERE name = N'CK_agent_memory_entries_verdict')
            THEN N'PASS' ELSE N'FAIL' END AS [result];

SELECT N'IX_amr_to_kind present' AS [check],
       CASE WHEN EXISTS (SELECT 1 FROM sys.indexes
                          WHERE name = N'IX_amr_to_kind'
                            AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
            THEN N'PASS' ELSE N'FAIL' END AS [result];

-- Param contracts. A mismatch against the deployed module is a runtime failure
-- on every call, so assert the counts rather than eyeballing the strings.
SELECT N'insert params (expect 10)' AS [check],
       LEN(pub_parameter_names) - LEN(REPLACE(pub_parameter_names, N',', N'')) + 1 AS [params]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.insert';

SELECT N'update params (expect 8)' AS [check],
       LEN(pub_parameter_names) - LEN(REPLACE(pub_parameter_names, N',', N'')) + 1 AS [params]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.update';

SELECT N'search params (expect 11, unchanged)' AS [check],
       LEN(pub_parameter_names) - LEN(REPLACE(pub_parameter_names, N',', N'')) + 1 AS [params]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.search';

-- The trip-wire is unconditional: get must reference attempted_for with no
-- parameter gating it. Positive markers only -- an earlier migration in this
-- family (v0.13.12.0 header) failed a CORRECT query with a NOT LIKE assertion.
SELECT N'get carries the trip-wire' AS [check],
       CASE WHEN pub_query_text LIKE N'%attempted[_]for%'
             AND pub_query_text LIKE N'%deadends%'
             AND pub_query_text LIKE N'%deadend[_]count%'
             AND pub_query_text LIKE N'%TOP (50)%'      -- ORDER BY legality + bound
             AND pub_query_text LIKE N'%pub_accrual%'
            THEN N'PASS' ELSE N'FAIL' END AS [result]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.get';

-- The trip-wire must be unconditional. If a parameter ever gates it, the count
-- below stops matching 1 and the feature has quietly become opt-in again.
SELECT N'get still takes exactly 1 param' AS [check],
       CASE WHEN pub_parameter_names = N'key_guid'
            THEN N'PASS' ELSE N'FAIL' END AS [result],
       pub_parameter_names
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.get';

SELECT N'search carries deadend_count' AS [check],
       CASE WHEN pub_query_text LIKE N'%deadend[_]count%'
             AND pub_query_text LIKE N'%pub_verdict%'
            THEN N'PASS' ELSE N'FAIL' END AS [result]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.search';

-- Every existing entry must still satisfy the new biconditional. A non-zero
-- count means live rows are now un-updatable -- the exact breakage v0.13.8.0
-- correction 2 was written about.
SELECT N'entries violating the verdict rule (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_entries]
 WHERE NOT ((pub_kind =  N'deadend' AND pub_verdict IN (N'fundamental', N'conditional'))
         OR (pub_kind <> N'deadend' AND pub_verdict IS NULL));

SELECT N'reflection rows registered (expect 2)' AS [check],
       (SELECT COUNT(*) FROM [dbo].[system_objects_database_columns]
         WHERE [pub_name] = N'pub_verdict')
     + (SELECT COUNT(*) FROM [dbo].[system_objects_database_indexes]
         WHERE [pub_name] = N'IX_amr_to_kind') AS [count];
GO
