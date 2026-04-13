-- =============================================================================
-- v0.12.15.0_seed_database_builder_rpc
-- Date: 2026-04-13
-- Purpose:
--   1) Seed database metadata CRUD queries for CmsWorkbenchModule
--   2) Register CmsWorkbenchModule methods for database metadata CRUD
--   3) Register RPC gateway bindings for database metadata CRUD operations
-- =============================================================================

MERGE INTO [dbo].[system_objects_queries] AS target
USING (
  SELECT
    N'62D45D9F-C906-5B93-8FC3-4615DBFDCEB4' AS [key_guid],
    N'cms.database.upsert_table' AS [pub_name],
    N'DECLARE @key_guid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @pub_name NVARCHAR(128) = ?;
DECLARE @pub_schema NVARCHAR(128) = ?;
DECLARE @resolved_key UNIQUEIDENTIFIER = COALESCE(@key_guid, NEWID());

MERGE INTO [dbo].[system_objects_database_tables] AS target
USING (
  SELECT
    @resolved_key AS [key_guid],
    @pub_name AS [pub_name],
    @pub_schema AS [pub_schema]
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [pub_name] = source.[pub_name],
    [pub_schema] = source.[pub_schema],
    [priv_modified_on] = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT ([key_guid], [pub_name], [pub_schema])
  VALUES (source.[key_guid], source.[pub_name], source.[pub_schema]);

SELECT CAST(1 AS BIT) AS [ok]
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;' AS [pub_query_text],
    N'Upsert database table metadata row in system_objects_database_tables.' AS [pub_description],
    N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS [ref_module_guid],
    1 AS [pub_is_parameterized],
    N'key_guid,pub_name,pub_schema' AS [pub_parameter_names]

  UNION ALL SELECT
    N'C9285A8F-D9F6-5E6F-B471-9D9FCFBB5046',
    N'cms.database.delete_table',
    N'DECLARE @key_guid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);

IF EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_database_columns]
  WHERE [ref_table_guid] = @key_guid
)
BEGIN
  THROW 50001, ''Cannot delete table metadata while columns exist. Delete columns first.'', 1;
END;

DELETE FROM [dbo].[system_objects_database_tables]
WHERE [key_guid] = @key_guid;

SELECT CAST(1 AS BIT) AS [ok]
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
    N'Delete database table metadata row when no dependent columns exist.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'key_guid'

  UNION ALL SELECT
    N'938279F8-EC41-5C08-9742-BBFB08A7643B',
    N'cms.database.upsert_column',
    N'DECLARE @key_guid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @ref_table_guid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @ref_type_guid UNIQUEIDENTIFIER = TRY_CAST(? AS UNIQUEIDENTIFIER);
DECLARE @pub_name NVARCHAR(128) = ?;
DECLARE @pub_ordinal INT = ?;
DECLARE @pub_is_nullable BIT = ?;
DECLARE @pub_is_primary_key BIT = ?;
DECLARE @pub_is_identity BIT = ?;
DECLARE @pub_default NVARCHAR(512) = ?;
DECLARE @pub_max_length INT = ?;
DECLARE @resolved_key UNIQUEIDENTIFIER = COALESCE(@key_guid, NEWID());

MERGE INTO [dbo].[system_objects_database_columns] AS target
USING (
  SELECT
    @resolved_key AS [key_guid],
    @ref_table_guid AS [ref_table_guid],
    @ref_type_guid AS [ref_type_guid],
    @pub_name AS [pub_name],
    @pub_ordinal AS [pub_ordinal],
    @pub_is_nullable AS [pub_is_nullable],
    @pub_is_primary_key AS [pub_is_primary_key],
    @pub_is_identity AS [pub_is_identity],
    @pub_default AS [pub_default],
    @pub_max_length AS [pub_max_length]
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [ref_table_guid] = source.[ref_table_guid],
    [ref_type_guid] = source.[ref_type_guid],
    [pub_name] = source.[pub_name],
    [pub_ordinal] = source.[pub_ordinal],
    [pub_is_nullable] = source.[pub_is_nullable],
    [pub_is_primary_key] = source.[pub_is_primary_key],
    [pub_is_identity] = source.[pub_is_identity],
    [pub_default] = source.[pub_default],
    [pub_max_length] = source.[pub_max_length]
WHEN NOT MATCHED THEN
  INSERT (
    [key_guid], [ref_table_guid], [ref_type_guid], [pub_name], [pub_ordinal],
    [pub_is_nullable], [pub_is_primary_key], [pub_is_identity], [pub_default], [pub_max_length]
  )
  VALUES (
    source.[key_guid], source.[ref_table_guid], source.[ref_type_guid], source.[pub_name], source.[pub_ordinal],
    source.[pub_is_nullable], source.[pub_is_primary_key], source.[pub_is_identity], source.[pub_default], source.[pub_max_length]
  );

SELECT CAST(1 AS BIT) AS [ok]
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
    N'Upsert database column metadata row in system_objects_database_columns.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'key_guid,ref_table_guid,ref_type_guid,pub_name,pub_ordinal,pub_is_nullable,pub_is_primary_key,pub_is_identity,pub_default,pub_max_length'

  UNION ALL SELECT
    N'44A23C51-AB25-5C9A-94BA-FC32F9126CF7',
    N'cms.database.delete_column',
    N'DELETE FROM [dbo].[system_objects_database_columns]
WHERE [key_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER);

SELECT CAST(1 AS BIT) AS [ok]
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;',
    N'Delete database column metadata row.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'key_guid'

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
  (N'4861B5FC-C30B-56C4-A091-01269574FB53', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_database_table', N'Upsert database table metadata.'),
  (N'DDB0D57B-3962-539B-B466-786E031AE4EE', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_database_table', N'Delete database table metadata.'),
  (N'ED2F5575-BD09-5570-9BE0-BBDFB859A691', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_database_column', N'Upsert database column metadata.'),
  (N'A384CF5B-956A-5FDC-B245-24E8C3290B5F', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_database_column', N'Delete database column metadata.')
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
  (N'8AA4187A-7951-506B-912C-B5450EB47BEA', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:upsert_database_table:1',  N'4861B5FC-C30B-56C4-A091-01269574FB53', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT)),
  (N'30C5A3BC-B2DF-5E1C-AE50-8A9EAA0A4286', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:delete_database_table:1',  N'DDB0D57B-3962-539B-B466-786E031AE4EE', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT)),
  (N'67B4A241-5BD0-502C-8D96-8CFE31FA0A27', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:upsert_database_column:1', N'ED2F5575-BD09-5570-9BE0-BBDFB859A691', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT)),
  (N'9E88E84E-61F4-5B65-A0C9-70CA00505539', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:delete_database_column:1', N'A384CF5B-956A-5FDC-B245-24E8C3290B5F', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', CAST(NULL AS UNIQUEIDENTIFIER), CAST(0 AS BIT))
) AS source([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid], [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid], [pub_is_read_only])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_gateway_method_bindings] bindings
  WHERE bindings.[key_guid] = source.[key_guid]
);
GO
