-- ============================================================================
-- elideus-group v0.13.4.0 — memory_coderules: an explicit RULES surface
-- Date: 2026-07-13
-- FDD lineage: FDD-ORACLE-MEM-CONFLICT-01 (the rule/idea split, made legible)
--
-- Capability this creates: an agent that, just by reading the tool list, sees
-- two distinct things to reach for — a place to explore project IDEAS
-- (memory_search / memory_list_recent) and a RULES bank for HOW to write code
-- (memory_coderules) — and reaches for the rulebook before it makes choices.
--
-- This rebrands the consult surface rather than adding a parallel path (single
-- source of truth for the retrieval engine): the memory.entries.consult query
-- and the consult_memory method are reused; only two things change —
--   1. the query now returns entries TAGGED 'rule' (the constraining subset),
--      folding in the universal 'general' rules when a project is named, and
--      no longer keys off pub_kind (rule/idea is orthogonal to kind);
--   2. the MCP operation is renamed memory_consult -> memory_coderules.
--
-- No backfill (maintainer's call): the bank fills as rules are tagged 'rule'
-- going forward, rather than sweeping the existing corpus.
--
-- Idempotent: UPDATE of the registered query + scoped DELETE/INSERT of the
-- gateway binding. Apply BEFORE redeploying code (the module reloads the query
-- at startup and the wrapper dispatches to 'memory_coderules').
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- PHASE 1: Repoint the consult query at the RULE class (tag = 'rule')
--   - EXISTS over STRING_SPLIT(pub_tags,' ') = 'rule'  → only rules
--   - project clause folds in 'general' (universal rules always apply)
--   - kinds param dropped; params now: limit, project, project, query, query
-- ============================================================================

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority,
       priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND pub_node_state = N''active''
  AND EXISTS (SELECT 1 FROM STRING_SPLIT(COALESCE(pub_tags, N''''), N'' '') t
              WHERE LTRIM(RTRIM(t.value)) = N''rule'')
  AND (? IS NULL OR pub_project = ? OR pub_project = N''general'')
  AND (? IS NULL OR NOT EXISTS (
        SELECT 1 FROM STRING_SPLIT(?, N'' '') s
        WHERE s.value <> N''''
          AND pub_title NOT LIKE N''%'' + s.value + N''%''
          AND pub_body  NOT LIKE N''%'' + s.value + N''%''
          AND COALESCE(pub_tags, N'''') NOT LIKE N''%'' + s.value + N''%''))
ORDER BY authority DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'limit,project,project,query,query',
  [pub_description] = N'Code-rules bank (backs memory_coderules): authority-ranked (confidence*(1+ref_count)) active entries tagged ''rule'', folding in universal ''general'' rules when a project is given; optional tokenized query. Rule/idea is orthogonal to kind, so this filters on the tag, not pub_kind.'
WHERE [pub_name] = N'memory.entries.consult';
GO


-- ============================================================================
-- PHASE 2: Rename the MCP operation memory_consult -> memory_coderules
--   Same method (consult_memory, 8AF6B3EC...), same read scope. New binding
--   GUID is uuid5(NS,'gateway_binding:mcp.memory_coderules') so registration
--   stays re-derivable. The old memory_consult binding is removed.
-- ============================================================================

DECLARE @MCP_GATEWAY UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

DELETE FROM [dbo].[system_objects_gateway_method_bindings]
WHERE [ref_gateway_guid] = @MCP_GATEWAY
  AND ([pub_operation_name] IN (N'memory_consult', N'memory_coderules')
       OR [key_guid] IN (N'1A3F233E-0947-5752-933E-110FC1D044DB',
                         N'F2196295-B616-53B3-8104-04E1C714E0D0'));

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [ref_method_guid], [pub_operation_name], [pub_required_scope], [pub_is_read_only], [pub_is_active])
VALUES
(N'F2196295-B616-53B3-8104-04E1C714E0D0', @MCP_GATEWAY,
 N'8AF6B3EC-C159-50AC-A552-9DA5139792B0', N'memory_coderules', N'mcp:memory:read', 1, 1);


-- ============================================================================
-- PHASE 3: Verification
-- ============================================================================

-- Operation renamed; old name gone, new name present on the read scope
SELECT pub_operation_name, pub_required_scope, pub_is_read_only, pub_is_active
FROM [dbo].[system_objects_gateway_method_bindings]
WHERE ref_gateway_guid = @MCP_GATEWAY AND pub_operation_name LIKE 'memory_%'
ORDER BY pub_operation_name;

-- Query now advertises the rule-filtered param set
SELECT pub_name, pub_parameter_names
FROM [dbo].[system_objects_queries]
WHERE pub_name = N'memory.entries.consult';

-- Preview what the rules bank will return today (entries tagged 'rule')
SELECT pub_project, pub_kind, pub_title,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1 AND pub_node_state = N'active'
  AND EXISTS (SELECT 1 FROM STRING_SPLIT(COALESCE(pub_tags, N''), N' ') t
              WHERE LTRIM(RTRIM(t.value)) = N'rule')
ORDER BY authority DESC;
GO
