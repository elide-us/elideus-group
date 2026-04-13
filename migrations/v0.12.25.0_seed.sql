-- ============================================================================
-- v0.12.25.0 — Component Detail Queries
-- Adds get_component_detail and upsert_component data-driven queries
-- for the ComponentBuilder PropertyPanel.
--
-- Deterministic GUIDs:
--   uuid5(NS, 'query:cms.components.get_component_detail') → 73E3EDC9-1776-5BE7-B144-392A55F9FD45
--   uuid5(NS, 'query:cms.components.upsert_component')     → 3AEF8758-795C-5053-B7DA-AB4F045579FB
--
-- CmsWorkbenchModule GUID: CF85FB11-5981-56B7-8E43-9D453E611D43
-- ============================================================================


-- 1. Get component detail (single row, WITHOUT_ARRAY_WRAPPER)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'73E3EDC9-1776-5BE7-B144-392A55F9FD45' AS key_guid,
  N'cms.components.get_component_detail' AS pub_name,
  N'SELECT
  c.key_guid AS guid,
  c.pub_name AS name,
  c.pub_category AS category,
  c.pub_description AS description,
  c.ref_default_type_guid AS defaultTypeGuid,
  t.pub_name AS defaultTypeName,
  c.priv_created_on AS createdOn,
  c.priv_modified_on AS modifiedOn
FROM system_objects_components c
LEFT JOIN system_objects_types t ON t.key_guid = c.ref_default_type_guid
WHERE c.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;' AS pub_query_text,
  N'Return full detail for a single component with resolved type name.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'component_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name
   AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER),
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid,
   pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_query_text,
   src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER),
   src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2. Upsert component (update description and default type)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'3AEF8758-795C-5053-B7DA-AB4F045579FB' AS key_guid,
  N'cms.components.upsert_component' AS pub_name,
  N'UPDATE system_objects_components
SET pub_description = COALESCE(?, pub_description),
    ref_default_type_guid = COALESCE(TRY_CAST(? AS UNIQUEIDENTIFIER), ref_default_type_guid),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);' AS pub_query_text,
  N'Update component description and default type. COALESCE preserves existing when NULL.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'description,default_type_guid,key_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name
   AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER),
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid,
   pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_query_text,
   src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER),
   src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- Verify
SELECT key_guid, pub_name, pub_is_active
FROM system_objects_queries
WHERE pub_name LIKE N'cms.components.%'
ORDER BY pub_name;