-- ============================================================================
-- v0.12.18.0 — Seed ModulesBuilder Queries
--
-- Adds 5 data-driven queries to system_objects_queries for the
-- CmsWorkbenchModule (CF85FB11-5981-56B7-8E43-9D453E611D43).
--
-- These power the ModulesBuilder CRUD operations:
--   cms.modules.get_methods       — methods grid with joined model names
--   cms.modules.upsert_module     — update module description/active
--   cms.modules.upsert_method     — insert or update a module method
--   cms.modules.delete_method     — delete a module method
--   cms.modules.get_method_contract — contract info for a method
--
-- Idempotent: uses MERGE pattern. Safe to re-run.
-- ============================================================================

SET NOCOUNT ON;

-- --------------------------------------------------------
-- 1. cms.modules.get_methods
-- --------------------------------------------------------
MERGE [dbo].[system_objects_queries] AS target
USING (SELECT
  N'7A1B2C3D-4E5F-5A6B-7C8D-9E0F1A2B3C4D' AS [key_guid],
  N'cms.modules.get_methods'                AS [pub_name],
  N'SELECT
  m.key_guid AS guid,
  m.pub_name AS name,
  m.pub_description AS description,
  m.pub_is_active AS isActive,
  m.ref_request_model_guid AS requestModelGuid,
  m.ref_response_model_guid AS responseModelGuid,
  rm_req.pub_name AS requestModelName,
  rm_res.pub_name AS responseModelName
FROM system_objects_module_methods m
LEFT JOIN system_objects_rpc_models rm_req
  ON rm_req.key_guid = m.ref_request_model_guid
LEFT JOIN system_objects_rpc_models rm_res
  ON rm_res.key_guid = m.ref_response_model_guid
WHERE m.ref_module_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY m.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;' AS [pub_query_text],
  N'Return methods for a module with joined request/response model names.' AS [pub_description],
  N'CF85FB11-5981-56B7-8E43-9D453E611D43'  AS [ref_module_guid],
  1                                         AS [pub_is_parameterized],
  N'module_guid'                            AS [pub_parameter_names],
  1                                         AS [pub_is_active]
) AS src
ON target.[key_guid] = TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  [pub_name]            = src.[pub_name],
  [pub_query_text]      = src.[pub_query_text],
  [pub_description]     = src.[pub_description],
  [ref_module_guid]     = TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER),
  [pub_is_parameterized]= src.[pub_is_parameterized],
  [pub_parameter_names] = src.[pub_parameter_names],
  [pub_is_active]       = src.[pub_is_active],
  [priv_modified_on]    = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_query_text], [pub_description],
   [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
  (TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER), src.[pub_name], src.[pub_query_text], src.[pub_description],
   TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER), src.[pub_is_parameterized], src.[pub_parameter_names], src.[pub_is_active]);

PRINT 'Seeded: cms.modules.get_methods';
GO


-- --------------------------------------------------------
-- 2. cms.modules.upsert_module
-- --------------------------------------------------------
MERGE [dbo].[system_objects_queries] AS target
USING (SELECT
  N'8B2C3D4E-5F6A-5B7C-8D9E-0F1A2B3C4D5E' AS [key_guid],
  N'cms.modules.upsert_module'              AS [pub_name],
  N'UPDATE system_objects_modules
SET pub_description = ?,
    pub_is_active = ?,
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);' AS [pub_query_text],
  N'Update module description and is_active. Modules are code-loaded — no INSERT from UI.' AS [pub_description],
  N'CF85FB11-5981-56B7-8E43-9D453E611D43'  AS [ref_module_guid],
  1                                         AS [pub_is_parameterized],
  N'description,is_active,key_guid'         AS [pub_parameter_names],
  1                                         AS [pub_is_active]
) AS src
ON target.[key_guid] = TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  [pub_name]            = src.[pub_name],
  [pub_query_text]      = src.[pub_query_text],
  [pub_description]     = src.[pub_description],
  [ref_module_guid]     = TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER),
  [pub_is_parameterized]= src.[pub_is_parameterized],
  [pub_parameter_names] = src.[pub_parameter_names],
  [pub_is_active]       = src.[pub_is_active],
  [priv_modified_on]    = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_query_text], [pub_description],
   [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
  (TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER), src.[pub_name], src.[pub_query_text], src.[pub_description],
   TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER), src.[pub_is_parameterized], src.[pub_parameter_names], src.[pub_is_active]);

PRINT 'Seeded: cms.modules.upsert_module';
GO


-- --------------------------------------------------------
-- 3. cms.modules.upsert_method
-- --------------------------------------------------------
MERGE [dbo].[system_objects_queries] AS target
USING (SELECT
  N'9C3D4E5F-6A7B-5C8D-9E0F-1A2B3C4D5E6F' AS [key_guid],
  N'cms.modules.upsert_method'              AS [pub_name],
  N'MERGE system_objects_module_methods AS target
USING (SELECT
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS key_guid,
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_module_guid,
  ? AS pub_name,
  ? AS pub_description,
  CAST(? AS BIT) AS pub_is_active
) AS src
ON target.key_guid = src.key_guid
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_description = src.pub_description,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_module_guid, pub_name, pub_description, pub_is_active)
VALUES
  (ISNULL(src.key_guid, NEWID()), src.ref_module_guid, src.pub_name, src.pub_description, src.pub_is_active);' AS [pub_query_text],
  N'Insert or update a module method. MERGE pattern for idempotent upsert.' AS [pub_description],
  N'CF85FB11-5981-56B7-8E43-9D453E611D43'  AS [ref_module_guid],
  1                                         AS [pub_is_parameterized],
  N'key_guid,module_guid,name,description,is_active' AS [pub_parameter_names],
  1                                         AS [pub_is_active]
) AS src
ON target.[key_guid] = TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  [pub_name]            = src.[pub_name],
  [pub_query_text]      = src.[pub_query_text],
  [pub_description]     = src.[pub_description],
  [ref_module_guid]     = TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER),
  [pub_is_parameterized]= src.[pub_is_parameterized],
  [pub_parameter_names] = src.[pub_parameter_names],
  [pub_is_active]       = src.[pub_is_active],
  [priv_modified_on]    = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_query_text], [pub_description],
   [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
  (TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER), src.[pub_name], src.[pub_query_text], src.[pub_description],
   TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER), src.[pub_is_parameterized], src.[pub_parameter_names], src.[pub_is_active]);

PRINT 'Seeded: cms.modules.upsert_method';
GO


-- --------------------------------------------------------
-- 4. cms.modules.delete_method
-- --------------------------------------------------------
MERGE [dbo].[system_objects_queries] AS target
USING (SELECT
  N'AD4E5F6A-7B8C-5D9E-0F1A-2B3C4D5E6F7A' AS [key_guid],
  N'cms.modules.delete_method'              AS [pub_name],
  N'DELETE FROM system_objects_module_methods
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);' AS [pub_query_text],
  N'Delete a module method by GUID.'        AS [pub_description],
  N'CF85FB11-5981-56B7-8E43-9D453E611D43'  AS [ref_module_guid],
  1                                         AS [pub_is_parameterized],
  N'key_guid'                               AS [pub_parameter_names],
  1                                         AS [pub_is_active]
) AS src
ON target.[key_guid] = TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  [pub_name]            = src.[pub_name],
  [pub_query_text]      = src.[pub_query_text],
  [pub_description]     = src.[pub_description],
  [ref_module_guid]     = TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER),
  [pub_is_parameterized]= src.[pub_is_parameterized],
  [pub_parameter_names] = src.[pub_parameter_names],
  [pub_is_active]       = src.[pub_is_active],
  [priv_modified_on]    = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_query_text], [pub_description],
   [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
  (TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER), src.[pub_name], src.[pub_query_text], src.[pub_description],
   TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER), src.[pub_is_parameterized], src.[pub_parameter_names], src.[pub_is_active]);

PRINT 'Seeded: cms.modules.delete_method';
GO


-- --------------------------------------------------------
-- 5. cms.modules.get_method_contract
-- --------------------------------------------------------
MERGE [dbo].[system_objects_queries] AS target
USING (SELECT
  N'BE5F6A7B-8C9D-5E0F-1A2B-3C4D5E6F7A8B' AS [key_guid],
  N'cms.modules.get_method_contract'        AS [pub_name],
  N'SELECT
  c.key_guid AS contractGuid,
  c.pub_name AS contractName,
  c.pub_version AS version,
  c.pub_is_async AS isAsync,
  c.pub_is_internal_only AS isInternalOnly,
  c.pub_is_active AS isActive,
  c.ref_request_model_guid AS requestModelGuid,
  c.ref_response_model_guid AS responseModelGuid,
  rm_req.pub_name AS requestModelName,
  rm_res.pub_name AS responseModelName
FROM system_objects_module_contracts c
LEFT JOIN system_objects_rpc_models rm_req
  ON rm_req.key_guid = c.ref_request_model_guid
LEFT JOIN system_objects_rpc_models rm_res
  ON rm_res.key_guid = c.ref_response_model_guid
WHERE c.ref_method_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY c.pub_version DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;' AS [pub_query_text],
  N'Return contract info for a method with joined model names. Returns empty if no contract exists.' AS [pub_description],
  N'CF85FB11-5981-56B7-8E43-9D453E611D43'  AS [ref_module_guid],
  1                                         AS [pub_is_parameterized],
  N'method_guid'                            AS [pub_parameter_names],
  1                                         AS [pub_is_active]
) AS src
ON target.[key_guid] = TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  [pub_name]            = src.[pub_name],
  [pub_query_text]      = src.[pub_query_text],
  [pub_description]     = src.[pub_description],
  [ref_module_guid]     = TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER),
  [pub_is_parameterized]= src.[pub_is_parameterized],
  [pub_parameter_names] = src.[pub_parameter_names],
  [pub_is_active]       = src.[pub_is_active],
  [priv_modified_on]    = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_query_text], [pub_description],
   [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_is_active])
VALUES
  (TRY_CAST(src.[key_guid] AS UNIQUEIDENTIFIER), src.[pub_name], src.[pub_query_text], src.[pub_description],
   TRY_CAST(src.[ref_module_guid] AS UNIQUEIDENTIFIER), src.[pub_is_parameterized], src.[pub_parameter_names], src.[pub_is_active]);

PRINT 'Seeded: cms.modules.get_method_contract';
GO


-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT pub_name, pub_description, pub_parameter_names
FROM [dbo].[system_objects_queries]
WHERE ref_module_guid = N'CF85FB11-5981-56B7-8E43-9D453E611D43'
  AND pub_name LIKE N'cms.modules.%'
ORDER BY pub_name;

PRINT 'v0.12.18.0 seed complete: 5 ModulesBuilder queries seeded.';
GO