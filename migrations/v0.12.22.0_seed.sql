-- ============================================================================
-- ComponentBuilder: Seed Queries + Category Wiring
-- Run against elideus-group database
-- CmsWorkbenchModule GUID: CF85FB11-5981-56B7-8E43-9D453E611D43
-- ============================================================================

-- 1. Wire the Pages category to ComponentBuilder
UPDATE system_objects_tree_categories
SET pub_builder_component = N'ComponentBuilder',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'19422ABD-0EF2-5EDB-8186-C6446FF2AC87'; -- pages category


-- 2. Data-driven queries for ComponentBuilder operations
-- All use ref_module_guid = CmsWorkbenchModule

-- 2a. Get page tree (recursive CTE walk from page's root component)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.get_page_tree' AS pub_name,
  N'WITH tree AS (
    SELECT
      t.key_guid AS guid,
      CAST(NULL AS UNIQUEIDENTIFIER) AS parent_guid,
      c.pub_name AS component_name,
      c.pub_category AS component_category,
      c.key_guid AS component_guid,
      t.pub_label AS label,
      t.pub_field_binding AS field_binding,
      t.pub_sequence AS sequence,
      t.pub_rpc_operation AS rpc_operation,
      t.pub_rpc_contract AS rpc_contract,
      t.pub_mutation_operation AS mutation_operation,
      t.pub_is_default_editable AS is_editable,
      0 AS depth
    FROM system_objects_component_tree t
    JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
    JOIN system_objects_pages p ON p.ref_root_component_guid = t.key_guid
    WHERE p.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)

    UNION ALL

    SELECT
      child.key_guid,
      child.ref_parent_guid,
      cc.pub_name,
      cc.pub_category,
      cc.key_guid,
      child.pub_label,
      child.pub_field_binding,
      child.pub_sequence,
      child.pub_rpc_operation,
      child.pub_rpc_contract,
      child.pub_mutation_operation,
      child.pub_is_default_editable,
      parent.depth + 1
    FROM system_objects_component_tree child
    JOIN tree parent ON parent.guid = child.ref_parent_guid
    JOIN system_objects_components cc ON cc.key_guid = child.ref_component_guid
  )
  SELECT * FROM tree
  ORDER BY depth, sequence
  FOR JSON PATH, INCLUDE_NULL_VALUES;' AS pub_query_text,
  N'Recursive CTE walk of a page component tree. Returns all nodes with component metadata.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'page_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2b. List all registered components (for the component picker)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.list_components' AS pub_name,
  N'SELECT
    key_guid AS guid,
    pub_name AS name,
    pub_category AS category,
    pub_description AS description
  FROM system_objects_components
  ORDER BY pub_category, pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;' AS pub_query_text,
  N'List all registered components for the component picker toolbox.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  0 AS pub_is_parameterized,
  NULL AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2c. Create tree node
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.create_tree_node' AS pub_name,
  N'SET NOCOUNT ON;
DECLARE @new_guid UNIQUEIDENTIFIER = ISNULL(TRY_CAST(? AS UNIQUEIDENTIFIER), NEWID());
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, pub_label, pub_field_binding, pub_sequence, ref_page_guid)
VALUES
  (@new_guid,
   TRY_CAST(? AS UNIQUEIDENTIFIER),
   TRY_CAST(? AS UNIQUEIDENTIFIER),
   ?,
   ?,
   TRY_CAST(? AS INT),
   TRY_CAST(? AS UNIQUEIDENTIFIER));
SELECT @new_guid AS key_guid
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;' AS pub_query_text,
  N'Insert a new component tree node. Returns the new GUID.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'key_guid,parent_guid,component_guid,label,field_binding,sequence,page_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2d. Update tree node
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.update_tree_node' AS pub_name,
  N'UPDATE system_objects_component_tree
SET pub_label = COALESCE(?, pub_label),
    pub_field_binding = COALESCE(?, pub_field_binding),
    pub_sequence = COALESCE(TRY_CAST(? AS INT), pub_sequence),
    pub_rpc_operation = COALESCE(?, pub_rpc_operation),
    pub_rpc_contract = COALESCE(?, pub_rpc_contract),
    ref_component_guid = COALESCE(TRY_CAST(? AS UNIQUEIDENTIFIER), ref_component_guid),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);' AS pub_query_text,
  N'Update tree node properties. COALESCE preserves existing values when param is NULL.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'label,field_binding,sequence,rpc_operation,rpc_contract,component_guid,key_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2e. Delete tree node (cascade descendants)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.delete_tree_node' AS pub_name,
  N'SET NOCOUNT ON;
WITH descendants AS (
    SELECT key_guid
    FROM system_objects_component_tree
    WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    UNION ALL
    SELECT child.key_guid
    FROM system_objects_component_tree child
    JOIN descendants parent ON parent.key_guid = child.ref_parent_guid
)
DELETE FROM system_objects_component_tree
WHERE key_guid IN (SELECT key_guid FROM descendants);' AS pub_query_text,
  N'Delete a tree node and all descendants via recursive CTE.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'key_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- 2f. Move tree node (reparent + resequence)
MERGE INTO system_objects_queries AS target
USING (SELECT
  N'cms.pages.move_tree_node' AS pub_name,
  N'UPDATE system_objects_component_tree
SET ref_parent_guid = TRY_CAST(? AS UNIQUEIDENTIFIER),
    pub_sequence = TRY_CAST(? AS INT),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);' AS pub_query_text,
  N'Move a tree node to a new parent and/or sequence position.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'new_parent_guid,new_sequence,key_guid' AS pub_parameter_names,
  1 AS pub_is_active
) AS src
ON target.pub_name = src.pub_name AND target.ref_module_guid = TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_parameterized = src.pub_is_parameterized,
  pub_parameter_names = src.pub_parameter_names,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (NEWID(), src.pub_name, src.pub_query_text, src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER), src.pub_is_parameterized, src.pub_parameter_names, src.pub_is_active);


-- Verify
SELECT pub_name, pub_is_active
FROM system_objects_queries
WHERE ref_module_guid = N'CF85FB11-5981-56B7-8E43-9D453E611D43'
  AND pub_name LIKE N'cms.pages.%'
ORDER BY pub_name;