-- ============================================================================
-- elideus-group v0.13.14.0 — Memory: `project` is a LABEL, not a partition
-- Date: 2026-09-04
-- Ruling: Aaron, 2026-09-04 — "remove the silos created by the concept of
--   project." The memory bank is ONE institutional-knowledge graph shared by
--   every repository in the tenant (elideus-group, elideus-group-unity, flicker,
--   clay-engine, prism). Those repos share wire protocols, back-end auth, and
--   database tables; a rule banked from one of them ("respect layer boundaries
--   for authentication") must be reachable — and LINKABLE — from every module
--   in every other project that shares that system. Filtering reads by
--   pub_project defeated exactly that: a session grounded on project X never
--   saw the protocol/auth/DB knowledge banked under project Y.
--
-- WHAT CHANGES
--   No registered read filters by pub_project any more. The column stays as a
--   DESCRIPTIVE label on the row ("which repo/product is this about"), still
--   returned on every stub so a reader knows the context — it just never
--   narrows a result set.
--
--   memory.entries.search        11 -> 9 params  (project, include_general gone)
--   memory.entries.consult        5 -> 3 params  (project x2 gone)   [retired tool]
--   memory.entries.recent         3 -> 1 param   (project x2 gone)   [retired tool]
--   memory.graph.nodes            3 -> 2 params  (project gone)      [retired tool]
--   memory.contradictions.list    5 -> 3 params  (project x2 gone)   [retired tool]
--
--   The retired-tool queries are swept too (rule 75E20D35 — sweep the solution
--   for the replaced pattern): a re-inserted binding must not resurrect the
--   silo. The paired Python signatures change in the same commit.
--
--   The three WRITE queries that take project (entries.insert, threads.insert,
--   contradictions.open) keep their SQL. The MODULE now defaults an omitted
--   label to N'general' — the label the universal rules already carry — so "not
--   tied to one repo" has exactly ONE representation (rule 1B64FF03: never two
--   representations of one concept). Only their descriptions change here.
--
--   include_general (v0.13.10.0 CORRECTION 1) is retired: it existed only to
--   patch the silo it lived in. With no project filter there is nothing to fold.
--
-- WHAT DOES NOT CHANGE (deliberately — flagged as design items, not done here)
--   * pub_project stays NVARCHAR(128) NOT NULL on all four tables. No DDL.
--   * IX_agent_memory_entries_project (pub_project, pub_is_active) is retained.
--     Nothing on the tool surface seeks on it after this migration.
--   * UX_agent_memory_entries_canonical / UX_agent_memory_aliases_alias remain
--     scoped (pub_project, name). If project is a label, uniqueness per label
--     is a question for the tenant-partition design, together with a tenant
--     key that does NOT exist yet. Do not reuse pub_project as the tenant key.
--
-- !! DEPLOY ORDER !!  Apply migration -> deploy code -> restart -> reconnect.
-- Modules cache query text at startup (entry 18057D9A): the 9-param search
-- text with the 11-param module, or vice versa, fails on every call. The tool
-- list refreshes on MCP reconnect (entry FD26ABA6).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- 1) memory.entries.search — drop @project / @include_general (11 -> 9)
--    Everything else is v0.13.13.0 2d verbatim: stub projection, authority,
--    deadend_count, pub_verdict, total independent of paging.
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @query NVARCHAR(MAX)      = ?;
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
           OR COALESCE(e.pub_tags, N'''') LIKE N''%'' + s.value + N''%''
           OR e.pub_project LIKE N''%'' + s.value + N''%'')
  ) m
  WHERE e.pub_node_state = COALESCE(@node_state, N''active'')
    AND (@query IS NULL OR LTRIM(RTRIM(@query)) = N'''' OR m.match_count > 0)
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
  [pub_parameter_names] = N'query,kind,tags,tags_like,node_state,order,include_body,offset,limit',
  [pub_description]     = N'Filter and paginate entries ACROSS EVERY PROJECT: one graph; pub_project on a stub is a label, never a filter. query tokens match title/body/tags AND the project label (a label in query surfaces, never narrows). Returns {total, entries[]}; total ignores paging. order: relevance|authority|recent. kind=rule+order=authority IS the coderules bank; kind=deadend IS the dead-end bank. Stubs carry deadend_count (active attempted_for edges). include_body=0: pub_body_excerpt + body_length, pub_body null.'
WHERE [pub_name] = N'memory.entries.search';
GO


-- ============================================================================
-- 2) memory.entries.consult — drop the project fold (5 -> 3)   [retired tool]
--    v0.13.5.0 text minus the (? IS NULL OR pub_project = ? OR 'general') line.
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority,
       priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND pub_node_state = N''active''
  AND pub_kind = N''rule''
  AND (? IS NULL OR NOT EXISTS (
        SELECT 1 FROM STRING_SPLIT(?, N'' '') s
        WHERE s.value <> N''''
          AND pub_title NOT LIKE N''%'' + s.value + N''%''
          AND pub_body  NOT LIKE N''%'' + s.value + N''%''
          AND COALESCE(pub_tags, N'''') NOT LIKE N''%'' + s.value + N''%''))
ORDER BY authority DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'limit,query,query',
  [pub_description]     = N'Code-rules bank (retired tool memory_coderules; live path is memory_search kind=rule order=authority): authority-ranked (confidence*(1+ref_count)) active entries of KIND rule across every project; optional tokenized query. No project filter -- rules are universal.'
WHERE [pub_name] = N'memory.entries.consult';
GO


-- ============================================================================
-- 3) memory.entries.recent — drop project (3 -> 1)   [retired tool]
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
ORDER BY priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'limit',
  [pub_description]     = N'Most recently modified active entries across every project (retired tool memory_list_recent; live path is memory_search order=recent).'
WHERE [pub_name] = N'memory.entries.recent';
GO


-- ============================================================================
-- 4) memory.graph.nodes — drop @proj (3 -> 2)   [retired tool]
--    The node set for a graph export is now the whole active graph, kind-
--    filtered, most-referenced first, capped at @lim (the module clamps it).
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @kinds NVARCHAR(256) = ?;
DECLARE @lim INT = ?;
SELECT TOP (@lim) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (@kinds IS NULL OR EXISTS (
        SELECT 1 FROM STRING_SPLIT(@kinds, N'','') k
        WHERE LTRIM(RTRIM(k.value)) = pub_kind))
ORDER BY pub_ref_count DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'kinds,limit',
  [pub_description]     = N'Active entries for a graph export across every project, kind-filtered, most-referenced first, capped at limit. Node set for export_graph (retired tool memory_graph).'
WHERE [pub_name] = N'memory.graph.nodes';
GO


-- ============================================================================
-- 5) memory.contradictions.list — drop project (5 -> 3)   [retired tool]
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) c.key_guid, c.pub_project, c.pub_state, c.pub_resolution,
       c.pub_resolution_note, c.pub_resolved_source, c.priv_created_on, c.priv_resolved_on,
       c.ref_claim_a_guid, a.pub_title AS claim_a_title, a.pub_confidence AS claim_a_confidence, a.pub_node_state AS claim_a_state,
       c.ref_claim_b_guid, b.pub_title AS claim_b_title, b.pub_confidence AS claim_b_confidence, b.pub_node_state AS claim_b_state
FROM [dbo].[agent_memory_contradictions] c
LEFT JOIN [dbo].[agent_memory_entries] a ON a.key_guid = c.ref_claim_a_guid
LEFT JOIN [dbo].[agent_memory_entries] b ON b.key_guid = c.ref_claim_b_guid
WHERE (? IS NULL OR c.pub_state = ?)
ORDER BY c.priv_created_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'limit,state,state',
  [pub_description]     = N'List contradictions across every project (default state=open = the interrupt queue) with both claim titles/confidence/state.'
WHERE [pub_name] = N'memory.contradictions.list';
GO


-- ============================================================================
-- 6) Write-side descriptions — SQL unchanged; the registry must say what the
--    project param now means. The module supplies N'general' when omitted.
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_description] = N'Insert a memory entry. project is a DESCRIPTIVE LABEL (which repo/product the entry is about), never a partition -- no read filters by it; the module defaults an omitted label to general. verdict is REQUIRED when kind=deadend (fundamental|conditional) and must be NULL otherwise -- enforced by CK_agent_memory_entries_verdict.'
WHERE [pub_name] = N'memory.entries.insert';

UPDATE [dbo].[system_objects_queries] SET
  [pub_description] = N'Create a memory thread and return its new key_guid. project is a descriptive label, never a partition; the module defaults an omitted label to general.'
WHERE [pub_name] = N'memory.threads.insert';

UPDATE [dbo].[system_objects_queries] SET
  [pub_description] = N'Open a contradiction record between two claims; flip both active nodes to conflict. project is a descriptive label, never a partition; the module defaults an omitted label to general. Returns contradiction key_guid.'
WHERE [pub_name] = N'memory.contradictions.open';
GO


-- ============================================================================
-- 7) Method descriptions that named project as a scope
-- ============================================================================

UPDATE [dbo].[system_objects_module_methods] SET
  [pub_description] = N'Thread read or create: pass thread_guid to fetch, or title (project label optional) to create (memory_thread).'
WHERE [key_guid] = N'D91C1E82-A26E-561C-B1EA-F7444BED9351';   -- thread_memory

UPDATE [dbo].[system_objects_module_methods] SET
  [pub_description] = N'Export the memory graph (every project) as nodes+edges, capped (retired tool memory_graph).'
WHERE [key_guid] = N'2E35EE8C-D601-51F5-AB85-05BB5184F135';   -- export_graph

UPDATE [dbo].[system_objects_module_methods] SET
  [pub_description] = N'Most recently modified active entries across every project (retired tool memory_list_recent).'
WHERE [key_guid] = N'FE61B29E-52F1-5AF7-BA8F-3BEF79101542';   -- list_recent_memory
GO


-- ============================================================================
-- 8) Verification — ASSERTIONS with expected values, so a partial apply shows
--    up as a mismatch rather than a plausible-looking table.
-- ============================================================================

-- 8a) Param counts. Every one of these five must match its module signature.
SELECT pub_name,
       LEN(pub_parameter_names) - LEN(REPLACE(pub_parameter_names, N',', N'')) + 1 AS [params],
       CASE pub_name
         WHEN N'memory.entries.search'       THEN 9
         WHEN N'memory.entries.consult'      THEN 3
         WHEN N'memory.entries.recent'       THEN 1
         WHEN N'memory.graph.nodes'          THEN 2
         WHEN N'memory.contradictions.list'  THEN 3
       END AS [expect]
  FROM [dbo].[system_objects_queries]
 WHERE pub_name IN (N'memory.entries.search', N'memory.entries.consult',
                    N'memory.entries.recent', N'memory.graph.nodes',
                    N'memory.contradictions.list')
 ORDER BY pub_name;

-- 8b) THE point of the migration: no active memory.* READ text predicates on
--     pub_project any more. '@project' cannot appear in any of the new READ
--     texts, so this NOT LIKE cannot be tripped by a correct read query (the
--     v0.13.11.0 lesson — a negative marker is only safe when the substring is
--     impossible in the right answer). The three WRITE queries are excluded by
--     name: they keep their SQL (see header), and memory.contradictions.open
--     legitimately declares @proj as the label VALUE it inserts. That is not a
--     filter — and it tripped this check as a false positive on the first
--     apply (2026-09-26, count 1). [offenders] names anything counted, so a
--     non-zero result is diagnostic on its own. Expect 0 / NULL.
SELECT N'active memory.* READ queries still filtering by project (expect 0)' AS [check],
       COUNT(*) AS [count],
       STRING_AGG(pub_name, N', ') AS [offenders]
  FROM [dbo].[system_objects_queries]
 WHERE pub_name LIKE N'memory.%' AND pub_is_active = 1
   AND pub_name NOT IN (N'memory.entries.insert', N'memory.threads.insert',
                        N'memory.contradictions.open')
   AND (pub_query_text LIKE N'%@project%'
        OR pub_query_text LIKE N'%@proj %'
        OR pub_query_text LIKE N'%pub_project = ?%'
        OR pub_query_text LIKE N'%pub_project = @%');

-- 8c) Positive markers: the new search is still the v0.13.13.0 search minus
--     the filter (deadend_count + verdict on the stubs), not an older text.
SELECT N'search keeps v0.13.13.0 features' AS [check],
       CASE WHEN pub_query_text LIKE N'%deadend_count%'
             AND pub_query_text LIKE N'%f.pub_verdict%'
             AND pub_query_text LIKE N'%pub_body_excerpt%'
            THEN N'PASS' ELSE N'FAIL' END AS [result]
  FROM [dbo].[system_objects_queries] WHERE pub_name = N'memory.entries.search';

-- 8d) The corpus this un-silos IS multi-project. Expect > 1 — if it is 1 the
--     assertion above passed over a trivial corpus and proves nothing.
SELECT N'distinct project labels among active entries (expect > 1)' AS [check],
       COUNT(DISTINCT pub_project) AS [count]
  FROM [dbo].[agent_memory_entries] WHERE pub_node_state = N'active';

-- 8e) Tool surface unchanged in SIZE: still the 7 of v0.13.10.0.
SELECT N'active memory_* tools (expect 7)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[system_objects_gateway_method_bindings]
 WHERE [pub_operation_name] LIKE N'memory[_]%' AND [pub_is_active] = 1;
GO
