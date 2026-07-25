-- ============================================================================
-- elideus-group v0.13.10.0 — Memory Unification: Part C1 tool collapse 18 -> 7
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 §C1, plus two corrections to it.
--
-- THE SURFACE AFTER THIS MIGRATION
--   memory_get          covering read      (absorbs memory_links/_neighbors/_graph)
--   memory_search       filtered read      (absorbs memory_coderules/_list_recent)
--   memory_store        write
--   memory_update       write
--   memory_link         edge upsert        (absorbs _link_add/_link_update/_link_remove)
--   memory_thread       thread upsert/read (absorbs _thread_create/_thread_get)
--   memory_maintenance  ops queue          (absorbs _conflict_open/_resolve/_conflicts_list)
--
--   14 bindings retired, 3 added, 4 kept -> 7. The retired METHODS stay
--   registered and callable; only their gateway bindings go. That is
--   deliberate: if the new surface misbehaves, re-inserting a binding row
--   restores the old tool without a code deploy.
--
-- ---------------------------------------------------------------------------
-- CORRECTION 1 — 'general' fold. §C1 claims kind='rule' + order='authority'
--   "reproduces the coderules bank exactly". It does not. memory.entries.consult
--   passes @project TWICE and folds in the universal 'general' project:
--       (@project IS NULL OR pub_project = @project OR pub_project = 'general')
--   memory.entries.search filtered pub_project exactly. Retiring memory_coderules
--   without this would silently drop EVERY general rule from the rules bank —
--   including the highest-authority rule in the corpus ("Enhance the existing
--   system; never build a parallel reimplementation", accrual 29, project
--   'general'). An agent grounding a session on rules would stop seeing the very
--   rule this FDD exists to enforce.
--   @include_general (default 1) restores it. Set 0 for a strictly single-project
--   search.
--
-- CORRECTION 2 — leaner projection. v0.13.9.0 made search return stubs, but a
--   41-rule listing still measured 47KB because ~20 metadata columns rode along
--   with each 300-char excerpt: metadata outweighed content. A locator does not
--   need ref_thread_guid, pub_source, pub_confidence_source, pub_canonical_name,
--   pub_is_active or priv_created_on. Dropped here; memory_get remains the
--   full-record read. Same 41 rules should now land near 20KB.
--
-- PARAMS 10 -> 11 (include_general inserted after project):
--   query,project,include_general,kind,tags,tags_like,node_state,order,
--   include_body,offset,limit
--
-- !! DEPLOY ORDER !!  Apply migration -> deploy code -> restart -> reconnect.
-- Modules cache queries at startup (memory entry 18057D9A); the tool list
-- refreshes on MCP reconnect, no new session needed (entry FD26ABA6).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- 1) memory.entries.search — general fold + leaner projection
-- ============================================================================

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
         e.pub_tags, e.pub_confidence, e.pub_node_state, e.pub_ref_count,
         e.pub_accrual, e.priv_modified_on,
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
           f.pub_tags, f.pub_confidence, f.pub_node_state,
           f.pub_ref_count, f.pub_accrual, f.authority,
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
  [pub_description]     = N'Filter and paginate entries. Returns {total, entries[]}; total is independent of paging. order: relevance|authority|recent. kind=rule + order=authority IS the coderules bank. include_general (default 1) folds the universal general project in alongside @project. include_body=0 returns pub_body_excerpt + body_length with pub_body null.'
WHERE [pub_name] = N'memory.entries.search';
GO


-- ============================================================================
-- 1b) Two queries memory_link needs
--
--   memory.references.resolve — (from,to,kind) -> edge_guid. Retraction is
--     expressed as a triple, not an edge_guid: the caller retracting a link
--     knows what it linked, not the surrogate key. Without this, "retract"
--     would have to INSERT the edge just to learn its guid, creating a
--     soft-deleted row for a link that never existed.
--
--   memory.entries.accrue — the monotonic ledger increment. Nothing wrote to
--     pub_accrual before this: B3 seeded it and it would have stayed frozen
--     forever, so authority could never grow from reinforcement and the
--     anti-decay design would be inert. Fired ONLY on an inactive->active
--     edge transition, so re-adding an existing active link does not inflate.
--     Never decremented — retracting a link lowers ref_count, never accrual.
-- ============================================================================

DECLARE @MEMORY_MODULE_Q UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';

DELETE FROM [dbo].[system_objects_queries]
 WHERE [pub_name] IN (N'memory.references.resolve', N'memory.entries.accrue');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid],
   [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
(N'C629DC71-7C65-5EC5-9C89-1B83BA5C3A26', N'memory.references.resolve',
 N'SELECT TOP 1 key_guid, ref_from_guid, ref_to_guid, pub_ref_kind, pub_weight, pub_is_active
FROM [dbo].[agent_memory_references]
WHERE ref_from_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND ref_to_guid   = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND pub_ref_kind  = ?
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
 N'Resolve a (from,to,kind) triple to its edge row, active or not. Returns empty when the edge has never existed.',
 @MEMORY_MODULE_Q, 1, N'from_guid,to_guid,kind', 1),

(N'67C37834-0FBE-5276-B09A-EC6ACC0DAA91', N'memory.entries.accrue',
 N'SET NOCOUNT ON;
UPDATE [dbo].[agent_memory_entries]
   SET pub_accrual      = pub_accrual + 1,
       priv_last_ref_on = SYSUTCDATETIME()
 WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT key_guid, pub_accrual, pub_ref_count
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
 N'Increment the monotonic accrual ledger for an entry. MONOTONIC — nothing in the codebase may decrement pub_accrual.',
 @MEMORY_MODULE_Q, 1, N'key_guid,key_guid', 1);
GO


-- ============================================================================
-- 1c) The maintenance queue read/decide pair (§A8)
--   The queue table exists but nothing writes to it yet — the Part D sleep
--   cycle is the producer and is not built. These are registered now so the
--   TOOL SURFACE does not have to change again when Part D lands: adding a
--   producer later needs no new tool, no new binding, and no reconnect.
--   Until then 'list' correctly returns an empty queue.
-- ============================================================================

DECLARE @MEMORY_MODULE_M UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';

DELETE FROM [dbo].[system_objects_queries]
 WHERE [pub_name] IN (N'memory.maintenance.list', N'memory.maintenance.decide');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid],
   [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
(N'5F234FF0-852D-5523-BC0B-969C3476F91D', N'memory.maintenance.list',
 N'SELECT TOP (?) q.key_guid, q.pub_op, q.pub_state, q.pub_trigger, q.pub_rationale,
       q.ref_subject_guid, s.pub_title AS subject_title, s.pub_kind AS subject_kind,
       q.ref_object_guid,  o.pub_title AS object_title,
       q.pub_payload, q.priv_created_on
FROM [dbo].[agent_memory_maintenance_queue] q
LEFT JOIN [dbo].[agent_memory_entries] s ON s.key_guid = q.ref_subject_guid
LEFT JOIN [dbo].[agent_memory_entries] o ON o.key_guid = q.ref_object_guid
WHERE q.pub_state = N''pending''
ORDER BY q.priv_created_on ASC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
 N'Pending maintenance proposals, oldest first, with subject/object titles resolved so the queue is readable without a second fetch.',
 @MEMORY_MODULE_M, 1, N'limit', 1),

(N'354976A5-309F-592D-8FB1-237B66E9B8ED', N'memory.maintenance.decide',
 N'SET NOCOUNT ON;
UPDATE [dbo].[agent_memory_maintenance_queue]
   SET pub_state       = ?,
       pub_rationale   = COALESCE(?, pub_rationale),
       priv_decided_on = SYSUTCDATETIME()
 WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
   AND pub_state = N''pending'';
SELECT @@ROWCOUNT AS decided
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
 N'Apply or reject a pending queue item. Only transitions from pending, so a double-decide is a no-op returning decided=0 rather than silently re-deciding.',
 @MEMORY_MODULE_M, 1, N'state,rationale,queue_guid', 1);
GO


-- ============================================================================
-- 2) Method registration for the three consolidated methods
-- ============================================================================

DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';

DELETE FROM [dbo].[system_objects_module_methods]
 WHERE [key_guid] IN (N'5A5E6C2F-57E9-540F-867E-E6B61224F64C',
                      N'D91C1E82-A26E-561C-B1EA-F7444BED9351',
                      N'F56561F8-8677-51B7-9E29-B1DF119524C6');

INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active]) VALUES
(N'5A5E6C2F-57E9-540F-867E-E6B61224F64C', @MEMORY_MODULE, N'link_memory',
 N'Idempotent edge upsert on (from,to,kind); retraction via is_active=false. Recomputes ref_count and increments accrual only on inactive->active (memory_link).', 1),
(N'D91C1E82-A26E-561C-B1EA-F7444BED9351', @MEMORY_MODULE, N'thread_memory',
 N'Thread read or create: pass thread_guid to fetch, or project+title to create (memory_thread).', 1),
(N'F56561F8-8677-51B7-9E29-B1DF119524C6', @MEMORY_MODULE, N'maintenance_memory',
 N'Maintenance queue: list pending ops, apply/reject an item, purge the body archive (memory_maintenance).', 1);
GO


-- ============================================================================
-- 3) Gateway bindings — retire 14, add 3
--    Methods are intentionally NOT deleted: a retired tool can be restored by
--    re-inserting its binding row alone, with no code deploy.
-- ============================================================================

DECLARE @MCP_GATEWAY UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

DELETE FROM [dbo].[system_objects_gateway_method_bindings]
 WHERE [ref_gateway_guid] = @MCP_GATEWAY
   AND [pub_operation_name] IN (
     N'memory_coderules', N'memory_consult', N'memory_list_recent',
     N'memory_links', N'memory_neighbors', N'memory_graph',
     N'memory_link_add', N'memory_link_remove', N'memory_link_update',
     N'memory_thread_create', N'memory_thread_get',
     N'memory_conflict_open', N'memory_conflict_resolve', N'memory_conflicts_list');

DELETE FROM [dbo].[system_objects_gateway_method_bindings]
 WHERE [ref_gateway_guid] = @MCP_GATEWAY
   AND [pub_operation_name] IN (N'memory_link', N'memory_thread', N'memory_maintenance');

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [ref_method_guid], [pub_operation_name],
   [pub_required_scope], [pub_is_read_only], [pub_is_active]) VALUES
(N'E4DE4EF5-7FA2-5E87-9EC7-B64418969970', @MCP_GATEWAY, N'5A5E6C2F-57E9-540F-867E-E6B61224F64C',
 N'memory_link',        N'mcp:memory:write', 0, 1),
(N'C997CDA7-856E-5303-8A13-3064296BD8BD', @MCP_GATEWAY, N'D91C1E82-A26E-561C-B1EA-F7444BED9351',
 N'memory_thread',      N'mcp:memory:write', 0, 1),
(N'D2C6FF17-2B9A-5ACF-8346-2E3EEFCEF194', @MCP_GATEWAY, N'F56561F8-8677-51B7-9E29-B1DF119524C6',
 N'memory_maintenance', N'mcp:memory:write', 0, 1);
GO


-- ============================================================================
-- 4) Verification — these are ASSERTIONS, not a report.
--    Designed so a partial apply shows up as a non-zero failure count rather
--    than a plausible-looking table.
-- ============================================================================

SELECT N'search param count (expect 11)' AS [check],
       LEN(pub_parameter_names) - LEN(REPLACE(pub_parameter_names, N',', N'')) + 1 AS [params]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.search';

SELECT N'active memory_* tools (expect 7)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[system_objects_gateway_method_bindings]
 WHERE [pub_operation_name] LIKE N'memory[_]%' AND [pub_is_active] = 1;

SELECT [pub_operation_name], [pub_required_scope], [pub_is_read_only]
  FROM [dbo].[system_objects_gateway_method_bindings]
 WHERE [pub_operation_name] LIKE N'memory[_]%' AND [pub_is_active] = 1
 ORDER BY [pub_operation_name];
-- expect exactly: memory_get, memory_link, memory_maintenance, memory_search,
--                 memory_store, memory_thread, memory_update

-- Every surviving binding must resolve to a registered, active method. A row
-- here means a tool that will 500 at call time.
SELECT N'bindings with no live method (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[system_objects_gateway_method_bindings] b
  LEFT JOIN [dbo].[system_objects_module_methods] m
         ON m.key_guid = b.ref_method_guid AND m.pub_is_active = 1
 WHERE b.pub_operation_name LIKE N'memory[_]%' AND b.pub_is_active = 1
   AND m.key_guid IS NULL;

-- The retired methods must still exist, so a binding re-insert can restore a
-- tool without redeploying code.
SELECT N'retired methods still registered (expect 14)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[system_objects_module_methods]
 WHERE [ref_module_guid] = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1'
   AND [pub_name] IN (N'consult_memory', N'list_recent_memory', N'list_references',
                      N'get_neighbors', N'export_graph', N'add_reference',
                      N'remove_reference', N'update_reference', N'create_thread',
                      N'get_thread', N'open_contradiction', N'resolve_contradiction',
                      N'list_contradictions', N'get_memory');
GO
