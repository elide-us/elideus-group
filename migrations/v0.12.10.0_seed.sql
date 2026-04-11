-- ==========================================================================
-- v0.12.10.0_seed — Phase 4: MCP IoService Gateway Bindings
-- 
-- 1) Register RpcdispatchModule methods in system_objects_module_methods
-- 2) Seed MCP gateway method bindings in system_objects_gateway_method_bindings
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Method GUIDs:  uuid5(NS, 'method:RpcdispatchModule.{method_name}')
-- Binding GUIDs: uuid5(NS, 'gateway_binding:mcp.{tool_name}')
-- ==========================================================================

DECLARE @RPCDISPATCH_MODULE UNIQUEIDENTIFIER = N'F13CB430-FA45-5BF2-BA53-B589FD00FD8A';
DECLARE @MCP_GATEWAY        UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

-- ==========================================================================
-- 1) RpcdispatchModule method registrations
-- ==========================================================================

DELETE FROM system_objects_module_methods WHERE ref_module_guid = @RPCDISPATCH_MODULE;

INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, pub_description) VALUES
(N'1B4DD965-EDBE-5F7B-AEBA-39940B311FA3', @RPCDISPATCH_MODULE, N'list_tables',        N'List tables from object tree registry.'),
(N'8A81189D-0269-563F-A7DB-3DDF61649E0A', @RPCDISPATCH_MODULE, N'describe_table',     N'Describe table columns, indexes, and foreign keys.'),
(N'543C4380-380F-58A6-930F-A376F483667F', @RPCDISPATCH_MODULE, N'list_views',          N'List database views from reflection metadata.'),
(N'FF211FA9-C1C1-5C06-94A9-C147DDFBDD5C', @RPCDISPATCH_MODULE, N'get_full_schema',    N'Return full reflection schema snapshot.'),
(N'5E6EEF4A-E6A6-58A8-A44D-FB2D2A0E59CF', @RPCDISPATCH_MODULE, N'get_schema_version', N'Return current schema version from system_config.'),
(N'29A7BA5E-9C01-5DC1-A9D7-3ED8C91AEB97', @RPCDISPATCH_MODULE, N'dump_table',         N'Dump table rows as bounded JSON result set.'),
(N'CF109C28-CAE2-5E91-B801-EAFC5C98C41B', @RPCDISPATCH_MODULE, N'query_info_schema',  N'Query whitelisted INFORMATION_SCHEMA views.'),
(N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', @RPCDISPATCH_MODULE, N'list_domains',        N'Enumerate RPC domains from object tree.'),
(N'7BE8F9DD-4AAB-5878-B3F5-A8FD3D5699A8', @RPCDISPATCH_MODULE, N'list_subdomains',     N'List RPC subdomains with parent domain.'),
(N'FB89733C-2247-5B2C-BC77-40E6D1ECC2F4', @RPCDISPATCH_MODULE, N'list_functions',      N'List RPC functions with module and method bindings.'),
(N'6E30AE44-1F16-5EA5-B27B-7E772CF4369E', @RPCDISPATCH_MODULE, N'list_models',         N'List RPC Pydantic model registrations.'),
(N'AEE2585E-818F-55F9-A7DB-F1DB83D05FA5', @RPCDISPATCH_MODULE, N'list_model_fields',   N'List RPC model field registrations with types.'),
(N'14D96194-29AB-577F-80B9-61DAD27265FB', @RPCDISPATCH_MODULE, N'list_rpc_endpoints',  N'List top-level RPC domain handler endpoints.'),
(N'516DA43F-3C35-53D9-ABE5-D743067247AA', @RPCDISPATCH_MODULE, N'list_edt_mappings',   N'List EDT type mappings across platforms.');
GO

-- ==========================================================================
-- 2) MCP gateway method bindings
-- ==========================================================================

DELETE FROM system_objects_gateway_method_bindings WHERE ref_gateway_guid = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

INSERT INTO system_objects_gateway_method_bindings
  (key_guid, ref_gateway_guid, ref_method_guid, pub_operation_name, pub_required_scope, pub_is_read_only, pub_is_active)
VALUES
-- Schema read tools
(N'05DCB11A-1914-5D2B-B56A-83E774159B84', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'1B4DD965-EDBE-5F7B-AEBA-39940B311FA3', N'oracle_list_tables',        N'mcp:schema:read', 1, 1),
(N'C7C35732-2E3E-5E17-B69E-E16141485831', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'8A81189D-0269-563F-A7DB-3DDF61649E0A', N'oracle_describe_table',     N'mcp:schema:read', 1, 1),
(N'D12D173E-BE53-51BA-9EB3-F3ECB0D220CB', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'543C4380-380F-58A6-930F-A376F483667F', N'oracle_list_views',          N'mcp:schema:read', 1, 1),
(N'68AABBD7-FE6B-5BCE-A3D9-12763C9DBFF4', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'FF211FA9-C1C1-5C06-94A9-C147DDFBDD5C', N'oracle_get_full_schema',    N'mcp:schema:read', 1, 1),
(N'2805339D-B9A8-56DF-A243-A78A4E97ECCE', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'5E6EEF4A-E6A6-58A8-A44D-FB2D2A0E59CF', N'oracle_get_schema_version', N'mcp:schema:read', 1, 1),
(N'362D0200-53EB-55F6-94EE-69CB74C5010B', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'CF109C28-CAE2-5E91-B801-EAFC5C98C41B', N'oracle_query_info_schema',  N'mcp:schema:read', 1, 1),
-- Data read tools
(N'38448328-9CD5-5FC2-9BAF-8C266AC3CA4B', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'29A7BA5E-9C01-5DC1-A9D7-3ED8C91AEB97', N'oracle_dump_table',         N'mcp:data:read',   1, 1),
-- RPC list tools
(N'8FCCDE0E-3C22-5353-BB06-672BF952C7F9', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', N'oracle_list_domains',        N'mcp:rpc:list',    1, 1),
(N'5DFE30D7-E2C3-55A3-9D68-0BD4F71331C0', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'14D96194-29AB-577F-80B9-61DAD27265FB', N'oracle_list_rpc_endpoints',  N'mcp:rpc:list',    1, 1),
(N'0943876D-05B3-5401-822D-FF4606F80CC0', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', N'oracle_list_rpc_domains',    N'mcp:rpc:list',    1, 1),
(N'633C5417-0EA2-5D9D-B99E-9E0385BCE425', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'7BE8F9DD-4AAB-5878-B3F5-A8FD3D5699A8', N'oracle_list_rpc_subdomains', N'mcp:rpc:list',    1, 1),
(N'F1BE9D88-49EE-559A-B17F-9EA6C1BA9FEE', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'FB89733C-2247-5B2C-BC77-40E6D1ECC2F4', N'oracle_list_rpc_functions',  N'mcp:rpc:list',    1, 1),
(N'318D010D-1BC1-51A8-AB36-AA59BD09AD4A', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'6E30AE44-1F16-5EA5-B27B-7E772CF4369E', N'oracle_list_rpc_models',     N'mcp:rpc:list',    1, 1),
(N'F030DF6D-8C68-52A8-B6AC-D2D7AC9E4561', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'AEE2585E-818F-55F9-A7DB-F1DB83D05FA5', N'oracle_list_rpc_model_fields', N'mcp:rpc:list',  1, 1);
GO

-- ==========================================================================
-- Verification
-- ==========================================================================

SELECT 'rpcdispatch_methods' AS category, COUNT(*) AS [count]
FROM system_objects_module_methods
WHERE ref_module_guid = N'F13CB430-FA45-5BF2-BA53-B589FD00FD8A';

SELECT 'mcp_bindings' AS category, COUNT(*) AS [count]
FROM system_objects_gateway_method_bindings
WHERE ref_gateway_guid = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';

SELECT mb.pub_operation_name AS tool, mb.pub_required_scope AS scope,
       mm.pub_name AS method, mod.pub_state_attr AS module
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
JOIN system_objects_modules mod ON mod.key_guid = mm.ref_module_guid
WHERE mb.ref_gateway_guid = N'1287363D-8093-564A-A8CA-D0AE6985BDBD'
ORDER BY mb.pub_operation_name;
