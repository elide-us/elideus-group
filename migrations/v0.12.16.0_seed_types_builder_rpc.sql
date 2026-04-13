-- =============================================================================
-- v0.12.16.0_seed_types_builder_rpc
-- Date: 2026-04-13
-- Purpose:
--   1) Seed type metadata queries for CmsWorkbenchModule
--   2) Register CmsWorkbenchModule type methods
--   3) Register RPC gateway bindings for type metadata operations
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   query:cms.types.upsert_type                -> 85F84FE7-623D-5F58-B8DB-72C5687AD9BB
--   query:cms.types.delete_type                -> 3A0A9050-D079-51F6-A363-7E185FE464FA
--   query:cms.types.get_type_controls          -> C74E7A3F-2CFE-56FB-BE1D-B296599D44E3
--   CmsWorkbenchModule.upsert_type             -> 60C88DA3-79BD-5BD9-BF5F-C16671FFDC84
--   CmsWorkbenchModule.delete_type             -> 6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9
--   CmsWorkbenchModule.get_type_controls       -> A393E831-CA69-5F00-89A4-1FE5378CEE12
--   binding:urn:service:objects:upsert_type:1 -> DA6501ED-B272-54AE-BBE6-A35AD58B3F0F
--   binding:urn:service:objects:delete_type:1 -> 00560E3A-201C-582D-B3EB-38C7608498B9
--   binding:urn:service:objects:get_type_controls:1 -> D03F2FAA-89C7-562D-9138-DB79CFC134F3
-- =============================================================================

MERGE INTO [dbo].[system_objects_queries] AS target
USING (
  SELECT
    N'85F84FE7-623D-5F58-B8DB-72C5687AD9BB' AS [key_guid],
    N'cms.types.upsert_type' AS [pub_name],
    N'MERGE INTO [dbo].[system_objects_types] AS target
USING (SELECT
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS key_guid,
  ? AS pub_name,
  ? AS pub_mssql_type,
  ? AS pub_postgresql_type,
  ? AS pub_mysql_type,
  ? AS pub_python_type,
  ? AS pub_typescript_type,
  ? AS pub_json_type,
  TRY_CAST(? AS INT) AS pub_odbc_type_code,
  TRY_CAST(? AS INT) AS pub_max_length,
  ? AS pub_notes
) AS source
ON target.key_guid = source.key_guid
WHEN MATCHED THEN
  UPDATE SET
    pub_name = source.pub_name,
    pub_mssql_type = source.pub_mssql_type,
    pub_postgresql_type = source.pub_postgresql_type,
    pub_mysql_type = source.pub_mysql_type,
    pub_python_type = source.pub_python_type,
    pub_typescript_type = source.pub_typescript_type,
    pub_json_type = source.pub_json_type,
    pub_odbc_type_code = source.pub_odbc_type_code,
    pub_max_length = source.pub_max_length,
    pub_notes = source.pub_notes,
    priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT (key_guid, pub_name, pub_mssql_type, pub_postgresql_type, pub_mysql_type, pub_python_type, pub_typescript_type, pub_json_type, pub_odbc_type_code, pub_max_length, pub_notes)
  VALUES (ISNULL(source.key_guid, NEWID()), source.pub_name, source.pub_mssql_type, source.pub_postgresql_type, source.pub_mysql_type, source.pub_python_type, source.pub_typescript_type, source.pub_json_type, source.pub_odbc_type_code, source.pub_max_length, source.pub_notes);' AS [pub_query_text],
    N'Upsert type metadata in system_objects_types.' AS [pub_description],
    N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS [ref_module_guid],
    1 AS [pub_is_parameterized],
    N'key_guid,name,mssql_type,postgresql_type,mysql_type,python_type,typescript_type,json_type,odbc_type_code,max_length,notes' AS [pub_parameter_names]

  UNION ALL SELECT
    N'3A0A9050-D079-51F6-A363-7E185FE464FA',
    N'cms.types.delete_type',
    N'DELETE FROM [dbo].[system_objects_types]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);',
    N'Delete type metadata row.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'key_guid'

  UNION ALL SELECT
    N'C74E7A3F-2CFE-56FB-BE1D-B296599D44E3',
    N'cms.types.get_type_controls',
    N'SELECT
  tc.key_guid AS guid,
  c.pub_name AS componentName,
  tc.pub_is_default AS isDefault
FROM system_objects_type_controls tc
JOIN system_objects_components c ON c.key_guid = tc.ref_component_guid
WHERE tc.ref_type_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY c.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;',
    N'Read default component bindings for a type.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'type_guid'

) AS source ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names])
ON target.[key_guid] = TRY_CAST(source.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN
  UPDATE SET
    [pub_name] = source.[pub_name],
    [pub_query_text] = source.[pub_query_text],
    [pub_description] = source.[pub_description],
    [pub_is_parameterized] = source.[pub_is_parameterized],
    [pub_parameter_names] = source.[pub_parameter_names],
    [priv_modified_on] = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT ([key_guid], [pub_name], [pub_query_text], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names])
  VALUES (
    TRY_CAST(source.[key_guid] AS UNIQUEIDENTIFIER),
    source.[pub_name],
    source.[pub_query_text],
    source.[pub_description],
    TRY_CAST(source.[ref_module_guid] AS UNIQUEIDENTIFIER),
    source.[pub_is_parameterized],
    source.[pub_parameter_names]
  );
GO

INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active])
SELECT
  source.[key_guid],
  source.[ref_module_guid],
  source.[pub_name],
  source.[pub_description],
  CAST(1 AS BIT)
FROM (VALUES
  (N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_type', N'Upsert type metadata.'),
  (N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_type', N'Delete type metadata.'),
  (N'A393E831-CA69-5F00-89A4-1FE5378CEE12', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_type_controls', N'Read type control bindings metadata.')
) AS source([key_guid], [ref_module_guid], [pub_name], [pub_description])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_module_methods] methods
  WHERE methods.[key_guid] = source.[key_guid]
);
GO

INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid], [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid], [pub_is_read_only], [pub_is_active])
SELECT
  source.[key_guid],
  source.[ref_gateway_guid],
  source.[pub_operation_name],
  source.[ref_method_guid],
  source.[pub_required_scope],
  source.[ref_required_role_guid],
  source.[ref_required_entitlement_guid],
  source.[pub_is_read_only],
  CAST(1 AS BIT)
FROM (VALUES
  (N'DA6501ED-B272-54AE-BBE6-A35AD58B3F0F', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:upsert_type:1', N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT)),
  (N'00560E3A-201C-582D-B3EB-38C7608498B9', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:delete_type:1', N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT)),
  (N'D03F2FAA-89C7-562D-9138-DB79CFC134F3', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:get_type_controls:1', N'A393E831-CA69-5F00-89A4-1FE5378CEE12', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(1 AS BIT))
) AS source([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid], [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid], [pub_is_read_only])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_gateway_method_bindings] bindings
  WHERE bindings.[key_guid] = source.[key_guid]
);
GO
