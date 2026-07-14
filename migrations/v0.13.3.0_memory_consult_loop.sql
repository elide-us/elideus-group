-- ============================================================================
-- elideus-group v0.13.3.0 — Anti-Decay Consult Loop (memory Phase 2)
-- Date: 2026-07-13
-- FDD: FDD-ORACLE-MEM-CONFLICT-01 (Phase 2 — behaviour over the Phase-1 tables)
--
-- Purpose: make the memory bank ANTI-DECAY and usable as a consult surface.
--   "I need to perform a coding task -> consult the MCP -> it returns the rules
--    I must conform to." That workflow could not run before this migration
--   because memory_search matched the WHOLE query as one LIKE substring, so
--   multi-word consult queries returned nothing even when the rule existed.
--
-- This migration (NO new tables — Phase 1 created references + contradictions):
--   1. Fixes memory.entries.search to TOKENISE (STRING_SPLIT; every term must
--      match title/body/tags).
--   2. Adds 6 registered queries + 5 methods + 5 MCP bindings for:
--        memory_consult          (read)  authority-ranked rules to conform to
--        memory_link_add         (write) reinforce authority via a reference edge
--        memory_conflict_open    (write) record a contradiction (both -> conflict)
--        memory_conflict_resolve (write) classified transition (FDD §4)
--        memory_conflicts_list   (read)  the interrupt queue
--   Authority = pub_confidence * (1 + pub_ref_count) (maintainer-chosen).
--   Reinforcement raises authority via inbound cites/supports edges (anti-decay).
--
-- Scopes reuse mcp:memory:read/write (already advertised) — NO OAuth change.
-- All new tools follow wrapper -> dispatch -> binding -> method -> query, and
-- MemoryModule reloads queries at startup, so apply this migration BEFORE
-- redeploying code. Idempotent: scoped DELETE + INSERT / UPDATE.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DECLARE @MCP_GATEWAY   UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

-- ============================================================================
-- 1) Fix memory.entries.search — tokenise the query (multi-term now works)
-- ============================================================================
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on,
       COUNT(*) OVER() AS total
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (? IS NULL OR NOT EXISTS (
        SELECT 1 FROM STRING_SPLIT(?, N'' '') s
        WHERE s.value <> N''''
          AND pub_title NOT LIKE N''%'' + s.value + N''%''
          AND pub_body  NOT LIKE N''%'' + s.value + N''%''
          AND COALESCE(pub_tags, N'''') NOT LIKE N''%'' + s.value + N''%''))
  AND (? IS NULL OR pub_project = ?)
  AND (? IS NULL OR pub_kind = ?)
  AND (? IS NULL OR pub_tags LIKE ?)
ORDER BY priv_modified_on DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'query,query,project,project,kind,kind,tags,tags_like,offset,limit'
WHERE [pub_name] = N'memory.entries.search';
GO

-- ============================================================================
-- 2) New registered queries (memory.entries.consult, references/contradictions)
-- ============================================================================
DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DELETE FROM [dbo].[system_objects_queries] WHERE [pub_name] IN (N'memory.entries.consult', N'memory.references.insert', N'memory.entries.recompute_refcount', N'memory.contradictions.open', N'memory.contradictions.resolve', N'memory.contradictions.list');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
(N'663CB8A0-B138-51E5-A4D5-D44D52519C22', N'memory.entries.consult',
N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority,
       priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND pub_node_state = N''active''
  AND (? IS NULL OR pub_project = ?)
  AND EXISTS (SELECT 1 FROM STRING_SPLIT(?, N'','') k WHERE LTRIM(RTRIM(k.value)) = pub_kind)
  AND (? IS NULL OR NOT EXISTS (
        SELECT 1 FROM STRING_SPLIT(?, N'' '') s
        WHERE s.value <> N''''
          AND pub_title NOT LIKE N''%'' + s.value + N''%''
          AND pub_body  NOT LIKE N''%'' + s.value + N''%''
          AND COALESCE(pub_tags, N'''') NOT LIKE N''%'' + s.value + N''%''))
ORDER BY authority DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Consult: authority-ranked (confidence*(1+ref_count)) active rules, kind-filtered (default set supplied by module), optional tokenized query.',
@MEMORY_MODULE, 1, N'limit,project,project,kinds,query,query', 1),

(N'88FE0E66-2CB2-5D92-B176-7D64E6DC9F85', N'memory.references.insert',
N'SET NOCOUNT ON;
DECLARE @from UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @to   UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @kind NVARCHAR(32)     = ?;
DECLARE @wt   DECIMAL(19,5)    = TRY_CAST(? AS DECIMAL(19,5));
DECLARE @guid UNIQUEIDENTIFIER = (SELECT key_guid FROM [dbo].[agent_memory_references]
                                  WHERE ref_from_guid = @from AND ref_to_guid = @to AND pub_ref_kind = @kind);
IF @guid IS NULL
BEGIN
  SET @guid = NEWID();
  INSERT INTO [dbo].[agent_memory_references] ([key_guid],[ref_from_guid],[ref_to_guid],[pub_ref_kind],[pub_weight])
  VALUES (@guid, @from, @to, @kind, COALESCE(@wt, 1.0));
END
ELSE
  UPDATE [dbo].[agent_memory_references]
  SET pub_weight = COALESCE(@wt, pub_weight), pub_is_active = 1, priv_modified_on = SYSUTCDATETIME()
  WHERE key_guid = @guid;
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Add (or reactivate) a directed reference edge from->to; idempotent on (from,to,kind). Returns edge key_guid.',
@MEMORY_MODULE, 1, N'from_guid,to_guid,kind,weight', 1),

(N'6A1AF33B-ACBB-554D-A0E3-95B9746A819F', N'memory.entries.recompute_refcount',
N'SET NOCOUNT ON;
DECLARE @node UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
UPDATE [dbo].[agent_memory_entries]
SET pub_ref_count = (SELECT COUNT(*) FROM [dbo].[agent_memory_references] r
                     WHERE r.ref_to_guid = @node AND r.pub_is_active = 1
                       AND r.pub_ref_kind IN (N''cites'', N''supports''))
WHERE key_guid = @node;
SELECT pub_ref_count FROM [dbo].[agent_memory_entries] WHERE key_guid = @node
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Recompute pub_ref_count for a node = count of active inbound cites/supports edges (authority rollup).',
@MEMORY_MODULE, 1, N'node_guid', 1),

(N'4E435013-B2D5-5AFC-BF7E-CDA3068AC89D', N'memory.contradictions.open',
N'SET NOCOUNT ON;
DECLARE @a UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @b UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @proj NVARCHAR(128) = ?;
DECLARE @note NVARCHAR(MAX)  = ?;
DECLARE @guid UNIQUEIDENTIFIER = NEWID();
INSERT INTO [dbo].[agent_memory_contradictions]
  ([key_guid],[pub_project],[ref_claim_a_guid],[ref_claim_b_guid],[pub_state],[pub_resolution_note])
VALUES (@guid, @proj, @a, @b, N''open'', @note);
UPDATE [dbo].[agent_memory_entries]
SET pub_node_state = N''conflict'', priv_modified_on = SYSUTCDATETIME()
WHERE key_guid IN (@a, @b) AND pub_node_state = N''active'';
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Open a contradiction record between two claims; flip both active nodes to conflict. Returns contradiction key_guid.',
@MEMORY_MODULE, 1, N'claim_a_guid,claim_b_guid,project,note', 1),

(N'82D763A8-121A-5E85-88E3-038E3B0F0874', N'memory.contradictions.resolve',
N'SET NOCOUNT ON;
DECLARE @cid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @res NVARCHAR(24)  = ?;
DECLARE @note NVARCHAR(MAX) = ?;
DECLARE @src NVARCHAR(128)  = ?;
DECLARE @a UNIQUEIDENTIFIER, @b UNIQUEIDENTIFIER;
SELECT @a = ref_claim_a_guid, @b = ref_claim_b_guid
FROM [dbo].[agent_memory_contradictions] WHERE key_guid = @cid;

UPDATE [dbo].[agent_memory_contradictions]
SET pub_state = N''resolved'', pub_resolution = @res,
    pub_resolution_note = COALESCE(@note, pub_resolution_note),
    pub_resolved_source = @src, priv_resolved_on = SYSUTCDATETIME(), priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = @cid;

IF @res = N''correction''
BEGIN
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''retired'', priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @a;
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''active'',  priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @b;
  IF NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_references] WHERE ref_from_guid = @b AND ref_to_guid = @a AND pub_ref_kind = N''supersedes'')
    INSERT INTO [dbo].[agent_memory_references] ([key_guid],[ref_from_guid],[ref_to_guid],[pub_ref_kind]) VALUES (NEWID(), @b, @a, N''supersedes'');
END
ELSE IF @res = N''new_version''
BEGIN
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''historical'', priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @a;
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''active'',     priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @b;
  IF NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_references] WHERE ref_from_guid = @b AND ref_to_guid = @a AND pub_ref_kind = N''supersedes'')
    INSERT INTO [dbo].[agent_memory_references] ([key_guid],[ref_from_guid],[ref_to_guid],[pub_ref_kind]) VALUES (NEWID(), @b, @a, N''supersedes'');
END
ELSE IF @res = N''typo''
BEGIN
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''active'',  priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @a;
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''retired'', priv_modified_on = SYSUTCDATETIME() WHERE key_guid = @b;
END
ELSE IF @res = N''misunderstanding''
BEGIN
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''active'', priv_modified_on = SYSUTCDATETIME() WHERE key_guid IN (@a, @b);
  IF NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_references] WHERE ref_from_guid = @a AND ref_to_guid = @b AND pub_ref_kind = N''disambiguates'')
    INSERT INTO [dbo].[agent_memory_references] ([key_guid],[ref_from_guid],[ref_to_guid],[pub_ref_kind]) VALUES (NEWID(), @a, @b, N''disambiguates'');
END
ELSE IF @res = N''contradiction''
BEGIN
  UPDATE [dbo].[agent_memory_entries] SET pub_node_state = N''active'', priv_modified_on = SYSUTCDATETIME() WHERE key_guid IN (@a, @b);
  IF NOT EXISTS (SELECT 1 FROM [dbo].[agent_memory_references] WHERE ref_from_guid = @a AND ref_to_guid = @b AND pub_ref_kind = N''contradicts'')
    INSERT INTO [dbo].[agent_memory_references] ([key_guid],[ref_from_guid],[ref_to_guid],[pub_ref_kind]) VALUES (NEWID(), @a, @b, N''contradicts'');
END

UPDATE e SET pub_ref_count = (SELECT COUNT(*) FROM [dbo].[agent_memory_references] r
                              WHERE r.ref_to_guid = e.key_guid AND r.pub_is_active = 1
                                AND r.pub_ref_kind IN (N''cites'', N''supports''))
FROM [dbo].[agent_memory_entries] e WHERE e.key_guid IN (@a, @b);

SELECT @cid AS key_guid, @res AS resolution FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Resolve a contradiction with a classified transition (correction|new_version|typo|contradiction|misunderstanding), apply node-state + edges, recompute ref counts.',
@MEMORY_MODULE, 1, N'conflict_guid,resolution,note,resolved_source', 1),

(N'24C01B71-4C72-5EB1-854A-988A88EC480C', N'memory.contradictions.list',
N'SELECT TOP (?) c.key_guid, c.pub_project, c.pub_state, c.pub_resolution,
       c.pub_resolution_note, c.pub_resolved_source, c.priv_created_on, c.priv_resolved_on,
       c.ref_claim_a_guid, a.pub_title AS claim_a_title, a.pub_confidence AS claim_a_confidence, a.pub_node_state AS claim_a_state,
       c.ref_claim_b_guid, b.pub_title AS claim_b_title, b.pub_confidence AS claim_b_confidence, b.pub_node_state AS claim_b_state
FROM [dbo].[agent_memory_contradictions] c
LEFT JOIN [dbo].[agent_memory_entries] a ON a.key_guid = c.ref_claim_a_guid
LEFT JOIN [dbo].[agent_memory_entries] b ON b.key_guid = c.ref_claim_b_guid
WHERE (? IS NULL OR c.pub_project = ?)
  AND (? IS NULL OR c.pub_state = ?)
ORDER BY c.priv_created_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'List contradictions (default state=open = the interrupt queue) with both claim titles/confidence/state.',
@MEMORY_MODULE, 1, N'limit,project,project,state,state', 1);
GO

-- ============================================================================
-- 3) Method registration (system_objects_module_methods)
-- ============================================================================
DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DELETE FROM [dbo].[system_objects_module_methods] WHERE [key_guid] IN (N'8AF6B3EC-C159-50AC-A552-9DA5139792B0', N'F94AC37C-F9A5-5157-8B75-6DFB1BAE452B', N'78CFCF4D-3465-5834-884B-05C6D88691E9', N'7329F6EB-BDA3-537E-8770-A7727856F57A', N'5C0A9AC0-5B8B-55B0-9076-4FD4DA04B643');

INSERT INTO [dbo].[system_objects_module_methods] ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active]) VALUES
(N'8AF6B3EC-C159-50AC-A552-9DA5139792B0', @MEMORY_MODULE, N'consult_memory', N'Authority-ranked rule retrieval for the consult-before-coding workflow.', 1),
(N'F94AC37C-F9A5-5157-8B75-6DFB1BAE452B', @MEMORY_MODULE, N'add_reference', N'Add a reference edge and recompute the target''s authority (ref_count).', 1),
(N'78CFCF4D-3465-5834-884B-05C6D88691E9', @MEMORY_MODULE, N'open_contradiction', N'Record a contradiction between two claims; both nodes enter conflict.', 1),
(N'7329F6EB-BDA3-537E-8770-A7727856F57A', @MEMORY_MODULE, N'resolve_contradiction', N'Resolve a contradiction with a classified transition.', 1),
(N'5C0A9AC0-5B8B-55B0-9076-4FD4DA04B643', @MEMORY_MODULE, N'list_contradictions', N'List contradictions (default open = the interrupt queue).', 1);
GO

-- ============================================================================
-- 4) MCP gateway bindings (system_objects_gateway_method_bindings)
-- ============================================================================
DECLARE @MCP_GATEWAY UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';
DELETE FROM [dbo].[system_objects_gateway_method_bindings]
WHERE [ref_gateway_guid] = @MCP_GATEWAY AND ([key_guid] IN (N'1A3F233E-0947-5752-933E-110FC1D044DB', N'D2FA2F5C-891C-57CD-B902-F3DDE77C52DB', N'6B36547B-D2D2-56A6-A916-DEDB9701DDA1', N'3CC43325-29A6-5534-8021-6513DDF5D960', N'861E3A33-1B6F-5A0A-8087-362525A84502') OR [pub_operation_name] IN (N'memory_consult', N'memory_link_add', N'memory_conflict_open', N'memory_conflict_resolve', N'memory_conflicts_list'));

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [ref_method_guid], [pub_operation_name], [pub_required_scope], [pub_is_read_only], [pub_is_active])
VALUES
(N'1A3F233E-0947-5752-933E-110FC1D044DB', @MCP_GATEWAY, N'8AF6B3EC-C159-50AC-A552-9DA5139792B0', N'memory_consult', N'mcp:memory:read', 1, 1),
(N'D2FA2F5C-891C-57CD-B902-F3DDE77C52DB', @MCP_GATEWAY, N'F94AC37C-F9A5-5157-8B75-6DFB1BAE452B', N'memory_link_add', N'mcp:memory:write', 0, 1),
(N'6B36547B-D2D2-56A6-A916-DEDB9701DDA1', @MCP_GATEWAY, N'78CFCF4D-3465-5834-884B-05C6D88691E9', N'memory_conflict_open', N'mcp:memory:write', 0, 1),
(N'3CC43325-29A6-5534-8021-6513DDF5D960', @MCP_GATEWAY, N'7329F6EB-BDA3-537E-8770-A7727856F57A', N'memory_conflict_resolve', N'mcp:memory:write', 0, 1),
(N'861E3A33-1B6F-5A0A-8087-362525A84502', @MCP_GATEWAY, N'5C0A9AC0-5B8B-55B0-9076-4FD4DA04B643', N'memory_conflicts_list', N'mcp:memory:read', 1, 1);
GO

-- ============================================================================
-- 5) Verification
-- ============================================================================
SELECT 'queries' AS category, COUNT(*) AS [count]
FROM system_objects_queries WHERE pub_name LIKE 'memory.%' AND pub_is_active = 1;   -- expect 13

SELECT 'methods' AS category, COUNT(*) AS [count]
FROM system_objects_module_methods WHERE ref_module_guid = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';               -- expect 12

SELECT mb.pub_operation_name AS tool, mb.pub_required_scope AS scope, mb.pub_is_read_only AS ro,
       mm.pub_name AS method
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
WHERE mb.ref_gateway_guid = N'1287363D-8093-564A-A8CA-D0AE6985BDBD' AND mb.pub_operation_name LIKE 'memory_%'
ORDER BY mb.pub_operation_name;                                                       -- expect 12 memory_* tools

