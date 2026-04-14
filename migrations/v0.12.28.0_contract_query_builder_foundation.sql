-- ============================================================================
-- v0.12.28.0 — ContractQueryBuilder Foundation
--
-- 1. Schema changes: add derived query/model columns to system_objects_pages,
--    add ref_method_guid to system_objects_page_data_bindings
-- 2. Register ContractQueryBuilderModule in system_objects_modules
-- 3. Register module methods in system_objects_module_methods
-- 4. Register RPC functions in system_objects_rpc_functions
--
-- All GUIDs deterministic: uuid5(DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67, ...)
-- ============================================================================


-- ============================================================================
-- 1. Schema changes
-- ============================================================================

-- 1a. Add derived query storage to pages
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'system_objects_pages' AND COLUMN_NAME = 'pub_derived_query'
)
BEGIN
  ALTER TABLE system_objects_pages
    ADD pub_derived_query NVARCHAR(MAX) NULL;
END;

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'system_objects_pages' AND COLUMN_NAME = 'ref_derived_model_guid'
)
BEGIN
  ALTER TABLE system_objects_pages
    ADD ref_derived_model_guid UNIQUEIDENTIFIER NULL;
END;

-- FK: pages → rpc_models (only if column was just added and FK doesn't exist)
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_sop_derived_model'
)
BEGIN
  ALTER TABLE system_objects_pages
    ADD CONSTRAINT FK_sop_derived_model
      FOREIGN KEY (ref_derived_model_guid)
      REFERENCES system_objects_rpc_models(key_guid);
END;

-- 1b. Add method binding to page_data_bindings (for 'function' source type)
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'system_objects_page_data_bindings' AND COLUMN_NAME = 'ref_method_guid'
)
BEGIN
  ALTER TABLE system_objects_page_data_bindings
    ADD ref_method_guid UNIQUEIDENTIFIER NULL;
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_sopdb_method'
)
BEGIN
  ALTER TABLE system_objects_page_data_bindings
    ADD CONSTRAINT FK_sopdb_method
      FOREIGN KEY (ref_method_guid)
      REFERENCES system_objects_module_methods(key_guid);
END;


-- ============================================================================
-- 2. Register ContractQueryBuilderModule
-- ============================================================================

MERGE INTO system_objects_modules AS target
USING (SELECT
  N'5EB872F5-079A-55B2-A86C-72A435ACAF0E' AS key_guid,
  N'ContractQueryBuilderModule' AS pub_name,
  N'contract_query_builder' AS pub_state_attr,
  N'server.modules.contract_query_builder_module' AS pub_module_path,
  1 AS pub_is_active
) AS src
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_state_attr = src.pub_state_attr,
  pub_module_path = src.pub_module_path,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_state_attr, pub_module_path, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name,
   src.pub_state_attr, src.pub_module_path, src.pub_is_active);


-- ============================================================================
-- 3. Register module methods
-- ============================================================================

MERGE INTO system_objects_module_methods AS target
USING (VALUES
  (N'634DD5B5-11AE-5949-B870-BA6B7A905244', N'5EB872F5-079A-55B2-A86C-72A435ACAF0E', N'analyze_page',            N'Derive query and data contracts for a page from its data bindings. Returns query text, output model, input model, tables, and joins.'),
  (N'FFA37302-559F-502A-9F38-C295794702F5', N'5EB872F5-079A-55B2-A86C-72A435ACAF0E', N'derive_query',            N'Derive just the SQL query text for a page. Returns null when no column bindings exist.'),
  (N'472FA9FD-2C78-527D-9C87-1627C667AC34', N'5EB872F5-079A-55B2-A86C-72A435ACAF0E', N'save_derived_artifacts',  N'Commit derived query and model to database. UPSERTs rpc_models, model_fields, and updates pages with derived query and model link.')
) AS src (key_guid, ref_module_guid, pub_name, pub_description)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_description = src.pub_description,
  pub_is_active = 1,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_module_guid, pub_name, pub_description, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER),
   src.pub_name, src.pub_description, 1);


-- ============================================================================
-- 4. Register RPC functions (under service:objects subdomain)
--    Subdomain GUID: 65663AC2-81EE-529E-82E4-F5166D9066F2
-- ============================================================================

MERGE INTO system_objects_rpc_functions AS target
USING (VALUES
  (N'E4C11CAB-134F-5E79-B09A-D50CC70C89EC', N'analyze_page',  1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'634DD5B5-11AE-5949-B870-BA6B7A905244'),
  (N'1446B225-F627-5224-8615-F2E3B7DA24F5', N'derive_query',  1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'FFA37302-559F-502A-9F38-C295794702F5')
) AS src (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_version = src.pub_version,
  pub_is_active = 1,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_version,
   TRY_CAST(src.ref_subdomain_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_method_guid AS UNIQUEIDENTIFIER), 1);


-- ============================================================================
-- 5. Verify
-- ============================================================================

-- New columns on pages
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'system_objects_pages'
  AND COLUMN_NAME IN ('pub_derived_query', 'ref_derived_model_guid');

-- New column on page_data_bindings
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'system_objects_page_data_bindings'
  AND COLUMN_NAME = 'ref_method_guid';

-- Module
SELECT key_guid, pub_name, pub_state_attr
FROM system_objects_modules
WHERE key_guid = N'5EB872F5-079A-55B2-A86C-72A435ACAF0E';

-- Methods
SELECT key_guid, pub_name
FROM system_objects_module_methods
WHERE ref_module_guid = N'5EB872F5-079A-55B2-A86C-72A435ACAF0E'
ORDER BY pub_name;

-- RPC functions
SELECT f.pub_name, m.pub_name AS method_name
FROM system_objects_rpc_functions f
JOIN system_objects_module_methods m ON m.key_guid = f.ref_method_guid
WHERE f.key_guid IN (
  N'E4C11CAB-134F-5E79-B09A-D50CC70C89EC',
  N'1446B225-F627-5224-8615-F2E3B7DA24F5'
);
