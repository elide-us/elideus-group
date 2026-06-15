-- ============================================================================
-- elideus-group v0.13.1.0 — Agent Memory Bank Registration (MCP wiring)
-- Date: 2026-06-14
-- Purpose:
--   Register the memory host module, its 7 methods, the 7 backing queries,
--   and the 7 MCP gateway bindings so dispatch('memory_*') resolves to
--   MemoryModule.<method> over the mcp gateway.
--
-- Depends on: v0.13.0.0_memory_foundation.sql (tables) and the MemoryModule
--   code (server/modules/memory_module.py, app.state attr = 'memory').
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   module  : uuid5(NS, 'module:memory')
--   method  : uuid5(NS, 'method:MemoryModule.<name>')
--   query   : uuid5(NS, 'query:<pub_name>')
--   binding : uuid5(NS, 'gateway_binding:mcp.<tool>')
--
-- Scopes: reads require mcp:memory:read, writes require mcp:memory:write.
--   These scopes are validated purely as binding text vs the identity scope
--   set granted in McpIoServiceModule.resolve_identity (static_token path
--   already extended in code).  There is no scope-enum table in this schema
--   (service_enum_categories has no 'scopes' category), so nothing else to seed.
--
-- Idempotent: scoped DELETE + INSERT (and MERGE for the single module row).
-- IMPORTANT: the binding cleanup is scoped to pub_operation_name LIKE
--   'memory_%' so the existing oracle_* bindings are left untouched.
-- ============================================================================

DECLARE @MEMORY_MODULE UNIQUEIDENTIFIER = N'C66296FA-6E27-5040-A2D5-34B5D2FF29C1';
DECLARE @MCP_GATEWAY   UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';


-- ============================================================================
-- 1) Module registration (system_objects_modules)
-- ============================================================================

MERGE INTO system_objects_modules AS target
USING (SELECT
  @MEMORY_MODULE             AS key_guid,
  N'MemoryModule'            AS pub_name,
  N'memory'                  AS pub_state_attr,
  N'server.modules.memory_module' AS pub_module_path,
  N'Persistent agent memory bank: store/search/retrieve working context across sessions.' AS pub_description,
  1                          AS pub_is_active
) AS src
ON target.key_guid = src.key_guid
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_state_attr = src.pub_state_attr,
  pub_module_path = src.pub_module_path,
  pub_description = src.pub_description,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_state_attr, pub_module_path, pub_description, pub_is_active)
VALUES
  (src.key_guid, src.pub_name, src.pub_state_attr, src.pub_module_path, src.pub_description, src.pub_is_active);


-- ============================================================================
-- 2) Method registration (system_objects_module_methods)
--    pub_name MUST equal the Python method name on MemoryModule.
-- ============================================================================

DELETE FROM system_objects_module_methods WHERE ref_module_guid = @MEMORY_MODULE;

INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, pub_description, pub_is_active) VALUES
(N'84FF4CB2-FAE7-5090-86D7-B2DCC7D4BE99', @MEMORY_MODULE, N'store_memory',       N'Insert a memory entry; returns key_guid.',                       1),
(N'C466D999-8458-59F2-BE1A-9A38BF2488A0', @MEMORY_MODULE, N'update_memory',      N'Patch a memory entry (COALESCE partial update); returns key_guid.',1),
(N'04D77F72-7BDC-570F-8C39-CB5999BD1408', @MEMORY_MODULE, N'get_memory',         N'Fetch a single memory entry by key_guid.',                       1),
(N'AC661350-F43C-5AE7-9B1F-447AE7FB6986', @MEMORY_MODULE, N'search_memory',      N'Filtered + paginated LIKE search; returns entries[] and total.', 1),
(N'FE61B29E-52F1-5AF7-BA8F-3BEF79101542', @MEMORY_MODULE, N'list_recent_memory', N'Most recently modified active entries (optional project).',      1),
(N'2510C314-A8D5-5C59-BD0D-6DFAA127286C', @MEMORY_MODULE, N'create_thread',      N'Create a memory thread; returns key_guid.',                      1),
(N'FFB5FE3C-126F-59DD-901B-EA6E6EFBFCDA', @MEMORY_MODULE, N'get_thread',         N'Fetch a thread and its active entries.',                         1);


-- ============================================================================
-- 3) Query registration (system_objects_queries)
--    Positional ? params; reads use FOR JSON PATH (+ WITHOUT_ARRAY_WRAPPER
--    for single-row). Param order matches MemoryModule's method calls.
-- ============================================================================

DELETE FROM system_objects_queries WHERE pub_name LIKE 'memory.%';

-- 3a: memory.entries.insert  (params: thread_guid, project, kind, title, body, tags, source)
INSERT INTO system_objects_queries
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
(N'882B0A79-BDF3-5C33-BAE5-D53574CB79EA', N'memory.entries.insert',
N'SET NOCOUNT ON;
DECLARE @guid UNIQUEIDENTIFIER = NEWID();
INSERT INTO [dbo].[agent_memory_entries]
  ([key_guid], [ref_thread_guid], [pub_project], [pub_kind], [pub_title], [pub_body], [pub_tags], [pub_source])
VALUES
  (@guid, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, ?, ?);
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Insert a memory entry and return its new key_guid.',
@MEMORY_MODULE, 1, N'thread_guid,project,kind,title,body,tags,source', 1),

-- 3b: memory.entries.update  (params: title, body, tags, kind, is_active, key_guid, key_guid)
(N'654F7A79-F7E9-5CD9-BCF6-28C8A943953B', N'memory.entries.update',
N'SET NOCOUNT ON;
UPDATE [dbo].[agent_memory_entries]
SET pub_title       = COALESCE(?, pub_title),
    pub_body        = COALESCE(?, pub_body),
    pub_tags        = COALESCE(?, pub_tags),
    pub_kind        = COALESCE(?, pub_kind),
    pub_is_active   = COALESCE(TRY_CAST(? AS BIT), pub_is_active),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT key_guid
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Patch a memory entry. COALESCE preserves existing values when a param is NULL. Returns key_guid (empty if not found).',
@MEMORY_MODULE, 1, N'title,body,tags,kind,is_active,key_guid,key_guid', 1),

-- 3c: memory.entries.get  (params: key_guid)
(N'AC5F44E2-08B4-57EF-B753-F1ABC6A24257', N'memory.entries.get',
N'SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
N'Fetch a single memory entry by key_guid (returns soft-deleted rows too).',
@MEMORY_MODULE, 1, N'key_guid', 1),

-- 3d: memory.entries.search
--   (params: query, query_like, query_like, query_like, project, project,
--            kind, kind, tags, tags_like, offset, limit)
(N'F5CCA37C-48AA-51D4-87AC-1797DCCDF03C', N'memory.entries.search',
N'SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_is_active, priv_created_on, priv_modified_on,
       COUNT(*) OVER() AS total
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (? IS NULL OR pub_title LIKE ? OR pub_body LIKE ? OR pub_tags LIKE ?)
  AND (? IS NULL OR pub_project = ?)
  AND (? IS NULL OR pub_kind = ?)
  AND (? IS NULL OR pub_tags LIKE ?)
ORDER BY priv_modified_on DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Filtered + paginated search over active entries. query=LIKE over title/body/tags; project/kind exact; tags LIKE. total = full match count via COUNT(*) OVER().',
@MEMORY_MODULE, 1, N'query,query_like,query_like,query_like,project,project,kind,kind,tags,tags_like,offset,limit', 1),

-- 3e: memory.entries.recent  (params: limit, project, project)
(N'4815F24D-AAD6-504C-8CA2-64B996F7D1AD', N'memory.entries.recent',
N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (? IS NULL OR pub_project = ?)
ORDER BY priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
N'Most recently modified active entries, optionally filtered to a project.',
@MEMORY_MODULE, 1, N'limit,project,project', 1),

-- 3f: memory.threads.insert  (params: project, title, summary)
(N'C67F591C-924E-5F05-9F8F-00E3FF9B82CF', N'memory.threads.insert',
N'SET NOCOUNT ON;
DECLARE @guid UNIQUEIDENTIFIER = NEWID();
INSERT INTO [dbo].[agent_memory_threads]
  ([key_guid], [pub_project], [pub_title], [pub_summary])
VALUES
  (@guid, ?, ?, ?);
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
N'Create a memory thread and return its new key_guid.',
@MEMORY_MODULE, 1, N'project,title,summary', 1),

-- 3g: memory.threads.get  (params: thread_guid)
(N'D252C0F7-2EC5-5082-A54F-5274E90B78D6', N'memory.threads.get',
N'SELECT t.key_guid, t.pub_project, t.pub_title, t.pub_summary, t.pub_is_active,
       t.priv_created_on, t.priv_modified_on,
       (SELECT e.key_guid, e.ref_thread_guid, e.pub_project, e.pub_kind, e.pub_title,
               e.pub_body, e.pub_tags, e.pub_source, e.pub_is_active,
               e.priv_created_on, e.priv_modified_on
        FROM [dbo].[agent_memory_entries] e
        WHERE e.ref_thread_guid = t.key_guid AND e.pub_is_active = 1
        ORDER BY e.priv_modified_on DESC
        FOR JSON PATH, INCLUDE_NULL_VALUES) AS entries
FROM [dbo].[agent_memory_threads] t
WHERE t.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
N'Fetch a thread plus its active entries (nested entries[] array).',
@MEMORY_MODULE, 1, N'thread_guid', 1);


-- ============================================================================
-- 4) MCP gateway bindings (system_objects_gateway_method_bindings)
--    Scoped cleanup so existing oracle_* bindings are NOT touched.
-- ============================================================================

DELETE FROM system_objects_gateway_method_bindings
WHERE ref_gateway_guid = @MCP_GATEWAY AND pub_operation_name LIKE 'memory_%';

INSERT INTO system_objects_gateway_method_bindings
  (key_guid, ref_gateway_guid, ref_method_guid, pub_operation_name, pub_required_scope, pub_is_read_only, pub_is_active)
VALUES
-- Writes (mcp:memory:write)
(N'225AB8EB-93E1-597E-9118-668B4D11154B', @MCP_GATEWAY, N'84FF4CB2-FAE7-5090-86D7-B2DCC7D4BE99', N'memory_store',         N'mcp:memory:write', 0, 1),
(N'026DF2E0-E22D-58FA-8B86-1FE1B7A849EE', @MCP_GATEWAY, N'C466D999-8458-59F2-BE1A-9A38BF2488A0', N'memory_update',        N'mcp:memory:write', 0, 1),
(N'52A3AA14-5AB1-51DD-9DDC-989569A10B92', @MCP_GATEWAY, N'2510C314-A8D5-5C59-BD0D-6DFAA127286C', N'memory_thread_create', N'mcp:memory:write', 0, 1),
-- Reads (mcp:memory:read)
(N'1226A1C0-C922-555B-8FB7-6AB62B7D6F10', @MCP_GATEWAY, N'04D77F72-7BDC-570F-8C39-CB5999BD1408', N'memory_get',           N'mcp:memory:read',  1, 1),
(N'FA1844D6-731A-52D6-A74E-F247A4E2DE54', @MCP_GATEWAY, N'AC661350-F43C-5AE7-9B1F-447AE7FB6986', N'memory_search',        N'mcp:memory:read',  1, 1),
(N'10859AEC-0CBD-52D2-B5A2-0A6A02727C20', @MCP_GATEWAY, N'FE61B29E-52F1-5AF7-BA8F-3BEF79101542', N'memory_list_recent',   N'mcp:memory:read',  1, 1),
(N'F67A864D-8749-5B13-A367-F9161EA1EE82', @MCP_GATEWAY, N'FFB5FE3C-126F-59DD-901B-EA6E6EFBFCDA', N'memory_thread_get',    N'mcp:memory:read',  1, 1);


-- ============================================================================
-- 5) Verification
-- ============================================================================

SELECT 'memory_module' AS category, pub_name, pub_state_attr, pub_module_path
FROM system_objects_modules WHERE key_guid = @MEMORY_MODULE;

SELECT 'memory_methods' AS category, COUNT(*) AS [count]
FROM system_objects_module_methods WHERE ref_module_guid = @MEMORY_MODULE;

SELECT 'memory_queries' AS category, COUNT(*) AS [count]
FROM system_objects_queries WHERE pub_name LIKE 'memory.%' AND pub_is_active = 1;

SELECT 'memory_bindings' AS category, COUNT(*) AS [count]
FROM system_objects_gateway_method_bindings
WHERE ref_gateway_guid = @MCP_GATEWAY AND pub_operation_name LIKE 'memory_%';

-- Full dispatch resolution (operation -> scope -> method -> module attr)
SELECT mb.pub_operation_name AS tool, mb.pub_required_scope AS scope,
       mb.pub_is_read_only AS read_only, mm.pub_name AS method, mod.pub_state_attr AS module
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
JOIN system_objects_modules mod ON mod.key_guid = mm.ref_module_guid
WHERE mb.ref_gateway_guid = @MCP_GATEWAY AND mb.pub_operation_name LIKE 'memory_%'
ORDER BY mb.pub_operation_name;
