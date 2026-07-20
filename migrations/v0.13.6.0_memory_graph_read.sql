-- ============================================================================
-- elideus-group v0.13.6.0 — Memory Graph READ/TRAVERSE + edge maintenance
-- Date: 2026-07-20
-- FDD: FDD-ORACLE-MEM-CONFLICT-01 (read half of the graph the write half built)
--
-- Finding: the memory graph (agent_memory_references) is directed, typed,
--   weighted, soft-deletable, deduped and indexed BOTH ways, but the tool
--   surface only WRITES it (memory_link_add). It could not be read or walked,
--   and a mislinked edge could never be retracted. This migration adds the
--   read/traverse + edge-maintenance surface. PURELY ADDITIVE — no change to
--   existing tables; one additive index; scopes reuse mcp:memory:read/write
--   (NO OAuth-router change).
--
-- New registered queries (6):
--   memory.references.list         incident edges for one node (+neighbor join)
--   memory.references.edges_batch  raw edges touching a CSV frontier (BFS/graph)
--   memory.entries.get_many        node payloads for a CSV of guids
--   memory.references.remove       soft-delete an edge + recompute ref_count
--   memory.references.update       patch an edge + recompute ref_count
--   memory.graph.nodes             project sub-graph node set
-- New methods (5) + MCP bindings (5):
--   memory_links, memory_neighbors, memory_link_remove, memory_link_update,
--   memory_graph. (memory_get gains include_links via the existing get_memory
--   binding — no new binding needed.)
-- New index (1): IX_agent_memory_references_from_active (ref_from_guid,
--   pub_is_active) — mirrors the existing ...to (ref_to_guid, pub_is_active).
--
-- Semantics locked: reads return explicit edge direction (out/in) + both
--   endpoints; ref_count recompute is symmetric with add (only cites/supports
--   reinforce); pub_is_active respected on both nodes and edges.
--
-- MemoryModule reloads queries at startup, so APPLY THIS MIGRATION BEFORE
-- redeploying code. Idempotent: scoped DELETE + INSERT / guarded CREATE INDEX.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
-- ============================================================================
-- 1) Additive index — symmetric partner to IX_agent_memory_references_to.
--    Speeds direction=out + active-edge filtering. Purely additive.
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_references_from_active'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE INDEX [IX_agent_memory_references_from_active]
    ON [dbo].[agent_memory_references] ([ref_from_guid], [pub_is_active]);
GO

-- Register the index in the reflection mirror (web CMS / object-tree read it;
-- oracle_* reads live sys.* so it sees the index regardless). Idempotent.
DELETE FROM [dbo].[system_objects_database_indexes] WHERE [key_guid] = N'5730C1B2-0EEE-5D96-AE01-54860284B708';
INSERT INTO [dbo].[system_objects_database_indexes]
  ([key_guid], [ref_table_guid], [pub_name], [pub_columns], [pub_is_unique])
VALUES
  (N'5730C1B2-0EEE-5D96-AE01-54860284B708', N'0D52ACB1-CE0F-5878-908E-314AD41A0A12', N'IX_agent_memory_references_from_active', N'ref_from_guid,pub_is_active', 0);
GO
-- ============================================================================
-- 2) Registered queries (system_objects_queries, namespace memory.*)
-- ============================================================================
DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DELETE FROM [dbo].[system_objects_queries] WHERE [pub_name] IN (N'memory.references.list', N'memory.references.edges_batch', N'memory.entries.get_many', N'memory.references.remove', N'memory.references.update', N'memory.graph.nodes');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES(N'F72A5BA6-CBB2-5284-A799-C3240A8A976D', N'memory.references.list',
N'DECLARE @g UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @dir NVARCHAR(8) = LOWER(COALESCE(?, N''both''));
DECLARE @kinds NVARCHAR(256) = ?;
DECLARE @inc BIT = COALESCE(TRY_CAST(? AS BIT), 0);
SELECT r.key_guid AS edge_guid,
       r.pub_ref_kind AS kind,
       r.pub_weight AS weight,
       r.pub_is_active AS is_active,
       CASE WHEN r.ref_from_guid = @g THEN N''out'' ELSE N''in'' END AS direction,
       CASE WHEN r.ref_from_guid = @g THEN r.ref_to_guid ELSE r.ref_from_guid END AS other_guid,
       o.pub_title AS other_title,
       o.pub_kind AS other_kind,
       o.pub_project AS other_project,
       o.pub_node_state AS other_node_state,
       o.pub_is_active AS other_is_active,
       r.priv_created_on, r.priv_modified_on
FROM [dbo].[agent_memory_references] r
JOIN [dbo].[agent_memory_entries] o
  ON o.key_guid = CASE WHEN r.ref_from_guid = @g THEN r.ref_to_guid ELSE r.ref_from_guid END
WHERE (r.ref_from_guid = @g OR r.ref_to_guid = @g)
  AND (@inc = 1 OR r.pub_is_active = 1)
  AND (@dir = N''both''
       OR (@dir = N''out'' AND r.ref_from_guid = @g)
       OR (@dir = N''in''  AND r.ref_to_guid = @g))
  AND (@kinds IS NULL OR EXISTS (
        SELECT 1 FROM STRING_SPLIT(@kinds, N'','') k
        WHERE LTRIM(RTRIM(k.value)) = r.pub_ref_kind))
ORDER BY direction, r.pub_ref_kind, o.pub_title
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Incident reference edges for one entry, joined to the neighbor node. direction=both|out|in, optional kinds CSV, include_inactive. Returns edge+direction+other node fields (memory_links / memory_get.include_links).',
@MEMORY_MODULE, 1, N'node_guid,direction,kinds,include_inactive', 1),

(N'AAE60CBF-23F6-54F8-BF22-29CB9E3A8B38', N'memory.references.edges_batch',
N'SET NOCOUNT ON;
DECLARE @csv NVARCHAR(MAX) = ?;
DECLARE @kinds NVARCHAR(256) = ?;
DECLARE @inc BIT = COALESCE(TRY_CAST(? AS BIT), 0);
DECLARE @frontier TABLE (g UNIQUEIDENTIFIER PRIMARY KEY);
INSERT INTO @frontier (g)
SELECT DISTINCT TRY_CAST(LTRIM(RTRIM(value)) AS UNIQUEIDENTIFIER)
FROM STRING_SPLIT(@csv, N'','')
WHERE LTRIM(RTRIM(value)) <> N'''' AND TRY_CAST(LTRIM(RTRIM(value)) AS UNIQUEIDENTIFIER) IS NOT NULL;
SELECT r.key_guid AS edge_guid,
       r.ref_from_guid AS from_guid,
       r.ref_to_guid AS to_guid,
       r.pub_ref_kind AS kind,
       r.pub_weight AS weight,
       r.pub_is_active AS is_active
FROM [dbo].[agent_memory_references] r
WHERE (r.ref_from_guid IN (SELECT g FROM @frontier)
       OR r.ref_to_guid IN (SELECT g FROM @frontier))
  AND (@inc = 1 OR r.pub_is_active = 1)
  AND (@kinds IS NULL OR EXISTS (
        SELECT 1 FROM STRING_SPLIT(@kinds, N'','') k
        WHERE LTRIM(RTRIM(k.value)) = r.pub_ref_kind))
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Raw reference edges (no node join) touching ANY node in a CSV frontier; active-only by default, optional kinds CSV. Powers the neighbors BFS and graph induced-edge set.',
@MEMORY_MODULE, 1, N'guids_csv,kinds,include_inactive', 1),

(N'1EF5407E-9967-545E-A1DB-FD8A41D71B31', N'memory.entries.get_many',
N'DECLARE @csv NVARCHAR(MAX) = ?;
SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE key_guid IN (
      SELECT TRY_CAST(LTRIM(RTRIM(value)) AS UNIQUEIDENTIFIER)
      FROM STRING_SPLIT(@csv, N'','')
      WHERE LTRIM(RTRIM(value)) <> N'''')
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Fetch node payloads for a CSV of key_guids (BFS/graph assembly). No pub_is_active filter — reached inactive nodes are returned as leaves.',
@MEMORY_MODULE, 1, N'guids_csv', 1),

(N'B4AC0053-DE60-56FE-84DE-CBA0E85C37A1', N'memory.references.remove',
N'SET NOCOUNT ON;
DECLARE @edge UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @to UNIQUEIDENTIFIER = (SELECT ref_to_guid FROM [dbo].[agent_memory_references] WHERE key_guid = @edge);
UPDATE [dbo].[agent_memory_references]
SET pub_is_active = 0, priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = @edge;
UPDATE [dbo].[agent_memory_entries]
SET pub_ref_count = (SELECT COUNT(*) FROM [dbo].[agent_memory_references] r
                     WHERE r.ref_to_guid = @to AND r.pub_is_active = 1
                       AND r.pub_ref_kind IN (N''cites'', N''supports''))
WHERE key_guid = @to;
SELECT @edge AS edge_guid, @to AS to_guid,
       (SELECT pub_ref_count FROM [dbo].[agent_memory_entries] WHERE key_guid = @to) AS ref_count,
       CASE WHEN @to IS NULL THEN 0 ELSE 1 END AS found
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Soft-delete a reference edge (pub_is_active=0) and recompute the target''s ref_count (inverse of memory.references.insert). Returns {edge_guid,to_guid,ref_count,found}.',
@MEMORY_MODULE, 1, N'edge_guid', 1),

(N'E5547423-53AC-5F2E-B748-B6CC865B9826', N'memory.references.update',
N'SET NOCOUNT ON;
DECLARE @edge UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @wt DECIMAL(19,5) = TRY_CAST(? AS DECIMAL(19,5));
DECLARE @kind NVARCHAR(32) = ?;
DECLARE @active BIT = TRY_CAST(? AS BIT);
DECLARE @to UNIQUEIDENTIFIER = (SELECT ref_to_guid FROM [dbo].[agent_memory_references] WHERE key_guid = @edge);
UPDATE [dbo].[agent_memory_references]
SET pub_weight = COALESCE(@wt, pub_weight),
    pub_ref_kind = COALESCE(@kind, pub_ref_kind),
    pub_is_active = COALESCE(@active, pub_is_active),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = @edge;
UPDATE [dbo].[agent_memory_entries]
SET pub_ref_count = (SELECT COUNT(*) FROM [dbo].[agent_memory_references] r
                     WHERE r.ref_to_guid = @to AND r.pub_is_active = 1
                       AND r.pub_ref_kind IN (N''cites'', N''supports''))
WHERE key_guid = @to;
SELECT @edge AS edge_guid, @to AS to_guid,
       (SELECT pub_ref_count FROM [dbo].[agent_memory_entries] WHERE key_guid = @to) AS ref_count,
       CASE WHEN @to IS NULL THEN 0 ELSE 1 END AS found
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Patch a reference edge (weight/kind/is_active; only non-null fields change) and recompute the target''s ref_count. Returns {edge_guid,to_guid,ref_count,found}. (from,to,kind) is unique — retyping to a colliding kind errors.',
@MEMORY_MODULE, 1, N'edge_guid,weight,kind,is_active', 1),

(N'1B8B945F-6779-516D-B461-65F32E9E7AA4', N'memory.graph.nodes',
N'DECLARE @proj NVARCHAR(128) = ?;
DECLARE @kinds NVARCHAR(256) = ?;
DECLARE @lim INT = ?;
SELECT TOP (@lim) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (@proj IS NULL OR pub_project = @proj OR pub_project = N''general'')
  AND (@kinds IS NULL OR EXISTS (
        SELECT 1 FROM STRING_SPLIT(@kinds, N'','') k
        WHERE LTRIM(RTRIM(k.value)) = pub_kind))
ORDER BY pub_ref_count DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Active entries for a project sub-graph export (its ''general'' entries folded in), kind-filtered, most-referenced first, capped at limit. Node set for memory_graph.',
@MEMORY_MODULE, 1, N'project,kinds,limit', 1);
GO

-- ============================================================================
-- 3) Method registration (system_objects_module_methods)
-- ============================================================================
DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DELETE FROM [dbo].[system_objects_module_methods] WHERE [key_guid] IN (N'A24D7AED-A59E-5822-9F0C-C0F4E6A520B6', N'836F92E5-857B-535A-B697-5F41121F6A65', N'9910C401-644B-51EC-9A1C-E67C09D7A726', N'AD19E443-BFB4-5A8C-8DDC-94FC39865EFE', N'2E35EE8C-D601-51F5-AB85-05BB5184F135');

INSERT INTO [dbo].[system_objects_module_methods] ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active]) VALUES
(N'A24D7AED-A59E-5822-9F0C-C0F4E6A520B6', @MEMORY_MODULE, N'list_references', N'List incident reference edges for an entry (memory_links).', 1),
(N'836F92E5-857B-535A-B697-5F41121F6A65', @MEMORY_MODULE, N'get_neighbors', N'Breadth-first neighbor expansion of the memory graph (memory_neighbors).', 1),
(N'9910C401-644B-51EC-9A1C-E67C09D7A726', @MEMORY_MODULE, N'remove_reference', N'Soft-delete a reference edge and recompute the target''s ref_count (memory_link_remove).', 1),
(N'AD19E443-BFB4-5A8C-8DDC-94FC39865EFE', @MEMORY_MODULE, N'update_reference', N'Patch a reference edge (weight/kind/is_active) and recompute the target''s ref_count (memory_link_update).', 1),
(N'2E35EE8C-D601-51F5-AB85-05BB5184F135', @MEMORY_MODULE, N'export_graph', N'Export a project''s memory sub-graph as nodes+edges (memory_graph).', 1);
GO

-- ============================================================================
-- 4) MCP gateway bindings (system_objects_gateway_method_bindings)
-- ============================================================================
DECLARE @MCP_GATEWAY UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';
DELETE FROM [dbo].[system_objects_gateway_method_bindings]
WHERE [ref_gateway_guid] = @MCP_GATEWAY AND ([key_guid] IN (N'A8297BF7-246D-548A-B6A8-1CF88F1911B0', N'F03AB19D-EA48-54F6-8EB3-2F252CC0E57D', N'B20FAA67-2694-5759-B597-163B69A30386', N'0501C6F1-740E-57AE-B15A-BB3D204BB83B', N'CE6D2D83-9422-5026-AF06-903B6933D4C7') OR [pub_operation_name] IN (N'memory_links', N'memory_neighbors', N'memory_link_remove', N'memory_link_update', N'memory_graph'));

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [ref_method_guid], [pub_operation_name], [pub_required_scope], [pub_is_read_only], [pub_is_active])
VALUES
(N'A8297BF7-246D-548A-B6A8-1CF88F1911B0', @MCP_GATEWAY, N'A24D7AED-A59E-5822-9F0C-C0F4E6A520B6', N'memory_links', N'mcp:memory:read', 1, 1),
(N'F03AB19D-EA48-54F6-8EB3-2F252CC0E57D', @MCP_GATEWAY, N'836F92E5-857B-535A-B697-5F41121F6A65', N'memory_neighbors', N'mcp:memory:read', 1, 1),
(N'B20FAA67-2694-5759-B597-163B69A30386', @MCP_GATEWAY, N'9910C401-644B-51EC-9A1C-E67C09D7A726', N'memory_link_remove', N'mcp:memory:write', 0, 1),
(N'0501C6F1-740E-57AE-B15A-BB3D204BB83B', @MCP_GATEWAY, N'AD19E443-BFB4-5A8C-8DDC-94FC39865EFE', N'memory_link_update', N'mcp:memory:write', 0, 1),
(N'CE6D2D83-9422-5026-AF06-903B6933D4C7', @MCP_GATEWAY, N'2E35EE8C-D601-51F5-AB85-05BB5184F135', N'memory_graph', N'mcp:memory:read', 1, 1);
GO

-- ============================================================================
-- 5) Verification
-- ============================================================================
SELECT 'queries' AS category, COUNT(*) AS [count]
FROM system_objects_queries WHERE pub_name LIKE 'memory.%' AND pub_is_active = 1;   -- expect 19

SELECT 'methods' AS category, COUNT(*) AS [count]
FROM system_objects_module_methods WHERE ref_module_guid = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';                    -- expect 17

SELECT mb.pub_operation_name AS tool, mb.pub_required_scope AS scope, mb.pub_is_read_only AS ro, mm.pub_name AS method
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
WHERE mb.ref_gateway_guid = N'1287363D-8093-564A-A8CA-D0AE6985BDBD' AND mb.pub_operation_name LIKE 'memory_%'
ORDER BY mb.pub_operation_name;                                                      -- expect 17 memory_* tools

SELECT name AS new_index FROM sys.indexes
WHERE object_id = OBJECT_ID(N'[dbo].[agent_memory_references]') AND name = N'IX_agent_memory_references_from_active';
