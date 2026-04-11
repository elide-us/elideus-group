-- ==========================================================================
-- v0.12.10.0_seed
-- Phase 4: MCP IoService gateway method registrations + bindings
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- ==========================================================================

DECLARE @MCP_GATEWAY_GUID UNIQUEIDENTIFIER = N'1287363D-8093-564A-A8CA-D0AE6985BDBD';
DECLARE @RPCDISPATCH_MODULE_GUID UNIQUEIDENTIFIER = N'F13CB430-FA45-5BF2-BA53-B589FD00FD8A';
GO

DELETE FROM [dbo].[system_objects_gateway_method_bindings]
WHERE [ref_gateway_guid] = N'1287363D-8093-564A-A8CA-D0AE6985BDBD'
  AND [pub_operation_name] IN (
    N'oracle_list_tables',
    N'oracle_describe_table',
    N'oracle_list_views',
    N'oracle_get_full_schema',
    N'oracle_get_schema_version',
    N'oracle_dump_table',
    N'oracle_query_info_schema',
    N'oracle_list_domains',
    N'oracle_list_rpc_endpoints',
    N'oracle_list_rpc_domains',
    N'oracle_list_rpc_subdomains',
    N'oracle_list_rpc_functions',
    N'oracle_list_rpc_models',
    N'oracle_list_rpc_model_fields'
  );
GO

DELETE FROM [dbo].[system_objects_module_methods]
WHERE [ref_module_guid] = N'F13CB430-FA45-5BF2-BA53-B589FD00FD8A'
  AND [pub_name] IN (
    N'list_tables',
    N'describe_table',
    N'list_views',
    N'get_full_schema',
    N'get_schema_version',
    N'dump_table',
    N'query_info_schema',
    N'list_domains',
    N'list_subdomains',
    N'list_functions',
    N'list_models',
    N'list_model_fields',
    N'list_rpc_endpoints'
  );
GO

INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active])
VALUES
  (N'1B4DD965-EDBE-5F7B-AEBA-39940B311FA3', @RPCDISPATCH_MODULE_GUID, N'list_tables', N'List tables from object tree registry.', 1),
  (N'8A81189D-0269-563F-A7DB-3DDF61649E0A', @RPCDISPATCH_MODULE_GUID, N'describe_table', N'Describe table columns, indexes, and foreign keys.', 1),
  (N'543C4380-380F-58A6-930F-A376F483667F', @RPCDISPATCH_MODULE_GUID, N'list_views', N'List database views.', 1),
  (N'FF211FA9-C1C1-5C06-94A9-C147DDFBDD5C', @RPCDISPATCH_MODULE_GUID, N'get_full_schema', N'Get full reflection schema snapshot.', 1),
  (N'5E6EEF4A-E6A6-58A8-A44D-FB2D2A0E59CF', @RPCDISPATCH_MODULE_GUID, N'get_schema_version', N'Get current schema version.', 1),
  (N'29A7BA5E-9C01-5DC1-A9D7-3ED8C91AEB97', @RPCDISPATCH_MODULE_GUID, N'dump_table', N'Dump table rows as JSON.', 1),
  (N'CF109C28-CAE2-5E91-B801-EAFC5C98C41B', @RPCDISPATCH_MODULE_GUID, N'query_info_schema', N'Query INFORMATION_SCHEMA views.', 1),
  (N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', @RPCDISPATCH_MODULE_GUID, N'list_domains', N'List RPC domains.', 1),
  (N'7BE8F9DD-4AAB-5878-B3F5-A8FD3D5699A8', @RPCDISPATCH_MODULE_GUID, N'list_subdomains', N'List RPC subdomains.', 1),
  (N'FB89733C-2247-5B2C-BC77-40E6D1ECC2F4', @RPCDISPATCH_MODULE_GUID, N'list_functions', N'List RPC functions.', 1),
  (N'6E30AE44-1F16-5EA5-B27B-7E772CF4369E', @RPCDISPATCH_MODULE_GUID, N'list_models', N'List RPC models.', 1),
  (N'AEE2585E-818F-55F9-A7DB-F1DB83D05FA5', @RPCDISPATCH_MODULE_GUID, N'list_model_fields', N'List RPC model fields.', 1),
  (N'14D96194-29AB-577F-80B9-61DAD27265FB', @RPCDISPATCH_MODULE_GUID, N'list_rpc_endpoints', N'List top-level RPC endpoints.', 1);
GO

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid],
   [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid],
   [pub_is_read_only], [pub_is_active])
VALUES
  (N'05DCB11A-1914-5D2B-B56A-83E774159B84', @MCP_GATEWAY_GUID, N'oracle_list_tables', N'1B4DD965-EDBE-5F7B-AEBA-39940B311FA3', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'C7C35732-2E3E-5E17-B69E-E16141485831', @MCP_GATEWAY_GUID, N'oracle_describe_table', N'8A81189D-0269-563F-A7DB-3DDF61649E0A', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'D12D173E-BE53-51BA-9EB3-F3ECB0D220CB', @MCP_GATEWAY_GUID, N'oracle_list_views', N'543C4380-380F-58A6-930F-A376F483667F', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'68AABBD7-FE6B-5BCE-A3D9-12763C9DBFF4', @MCP_GATEWAY_GUID, N'oracle_get_full_schema', N'FF211FA9-C1C1-5C06-94A9-C147DDFBDD5C', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'2805339D-B9A8-56DF-A243-A78A4E97ECCE', @MCP_GATEWAY_GUID, N'oracle_get_schema_version', N'5E6EEF4A-E6A6-58A8-A44D-FB2D2A0E59CF', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'38448328-9CD5-5FC2-9BAF-8C266AC3CA4B', @MCP_GATEWAY_GUID, N'oracle_dump_table', N'29A7BA5E-9C01-5DC1-A9D7-3ED8C91AEB97', N'mcp:data:read', NULL, NULL, 1, 1),
  (N'362D0200-53EB-55F6-94EE-69CB74C5010B', @MCP_GATEWAY_GUID, N'oracle_query_info_schema', N'CF109C28-CAE2-5E91-B801-EAFC5C98C41B', N'mcp:schema:read', NULL, NULL, 1, 1),
  (N'8FCCDE0E-3C22-5353-BB06-672BF952C7F9', @MCP_GATEWAY_GUID, N'oracle_list_domains', N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'5DFE30D7-E2C3-55A3-9D68-0BD4F71331C0', @MCP_GATEWAY_GUID, N'oracle_list_rpc_endpoints', N'14D96194-29AB-577F-80B9-61DAD27265FB', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'0943876D-05B3-5401-822D-FF4606F80CC0', @MCP_GATEWAY_GUID, N'oracle_list_rpc_domains', N'E3755263-5C66-5DF6-BBC2-AF2DC7DA94F0', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'633C5417-0EA2-5D9D-B99E-9E0385BCE425', @MCP_GATEWAY_GUID, N'oracle_list_rpc_subdomains', N'7BE8F9DD-4AAB-5878-B3F5-A8FD3D5699A8', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'F1BE9D88-49EE-559A-B17F-9EA6C1BA9FEE', @MCP_GATEWAY_GUID, N'oracle_list_rpc_functions', N'FB89733C-2247-5B2C-BC77-40E6D1ECC2F4', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'318D010D-1BC1-51A8-AB36-AA59BD09AD4A', @MCP_GATEWAY_GUID, N'oracle_list_rpc_models', N'6E30AE44-1F16-5EA5-B27B-7E772CF4369E', N'mcp:rpc:list', NULL, NULL, 1, 1),
  (N'F030DF6D-8C68-52A8-B6AC-D2D7AC9E4561', @MCP_GATEWAY_GUID, N'oracle_list_rpc_model_fields', N'AEE2585E-818F-55F9-A7DB-F1DB83D05FA5', N'mcp:rpc:list', NULL, NULL, 1, 1);
GO
