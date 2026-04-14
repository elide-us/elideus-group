-- ============================================================================
-- v0.12.28.3 — Properties System RPC Registration
--
-- Seeds data-driven queries for property CRUD and resolution.
-- Registers 6 module methods on CmsWorkbenchModule.
-- Registers 6 RPC functions under service:objects.
--
-- CmsWorkbenchModule GUID: CF85FB11-5981-56B7-8E43-9D453E611D43
-- Subdomain service.objects: 65663AC2-81EE-529E-82E4-F5166D9066F2
-- ============================================================================


-- ============================================================================
-- 1. Seed Queries
-- ============================================================================

MERGE INTO system_objects_queries AS target
USING (VALUES

  -- Property catalog (all available properties)
  (N'31266F1A-A412-53F5-9818-27779E98FFED',
   N'cms.properties.get_catalog',
   N'Return all property definitions from the catalog.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 0, NULL,
   N'SELECT
  p.key_guid AS guid,
  p.pub_name AS name,
  p.pub_category AS category,
  p.pub_description AS description,
  p.pub_default_value AS defaultValue,
  t.pub_name AS typeName,
  t.key_guid AS typeGuid
FROM system_objects_properties p
JOIN system_objects_types t ON t.key_guid = p.ref_type_guid
WHERE p.pub_is_active = 1
ORDER BY p.pub_category, p.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;'),

  -- Component defaults for a specific component
  (N'8AAA7F5A-B08B-526B-98BA-46222A1CC7C7',
   N'cms.properties.get_component_properties',
   N'Return property defaults declared by a component.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'component_guid',
   N'SELECT
  cp.key_guid AS guid,
  p.key_guid AS propertyGuid,
  p.pub_name AS name,
  p.pub_category AS category,
  cp.pub_value AS value,
  p.pub_default_value AS catalogDefault,
  t.pub_name AS typeName
FROM system_objects_component_properties cp
JOIN system_objects_properties p ON p.key_guid = cp.ref_property_guid
JOIN system_objects_types t ON t.key_guid = p.ref_type_guid
WHERE cp.ref_component_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY p.pub_category, p.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;'),

  -- Instance overrides for a specific tree node
  (N'498F86A8-CDAF-5F87-B1F0-EBF5CBC913DC',
   N'cms.properties.get_tree_node_properties',
   N'Return property overrides on a specific tree node instance.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'tree_node_guid',
   N'SELECT
  tnp.key_guid AS guid,
  p.key_guid AS propertyGuid,
  p.pub_name AS name,
  p.pub_category AS category,
  tnp.pub_value AS value,
  t.pub_name AS typeName
FROM system_objects_tree_node_properties tnp
JOIN system_objects_properties p ON p.key_guid = tnp.ref_property_guid
JOIN system_objects_types t ON t.key_guid = p.ref_type_guid
WHERE tnp.ref_tree_node_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY p.pub_category, p.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;'),

  -- Resolved properties for all nodes in a component tree
  -- Returns one row per (node, property) with the resolved value
  -- Resolution: instance override > component default > catalog default
  (N'4D6025C0-51EE-5AB7-953D-0127D5D78D9E',
   N'cms.properties.get_resolved_tree_properties',
   N'Return resolved properties for all nodes in a component tree. Merges instance overrides, component defaults, and catalog defaults.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'component_guid',
   N'WITH tree AS (
  SELECT t.key_guid AS node_guid, t.ref_component_guid AS component_guid
  FROM system_objects_component_tree t
  WHERE t.ref_component_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    AND t.ref_parent_guid IS NULL
    AND t.ref_page_guid IS NULL
  UNION ALL
  SELECT child.key_guid, child.ref_component_guid
  FROM system_objects_component_tree child
  JOIN tree parent ON parent.node_guid = child.ref_parent_guid
)
SELECT
  tree.node_guid AS nodeGuid,
  p.pub_name AS name,
  p.pub_category AS category,
  COALESCE(tnp.pub_value, cp.pub_value, p.pub_default_value) AS value,
  CASE
    WHEN tnp.pub_value IS NOT NULL THEN ''override''
    WHEN cp.pub_value IS NOT NULL THEN ''default''
    ELSE ''catalog''
  END AS source
FROM tree
CROSS JOIN system_objects_properties p
LEFT JOIN system_objects_tree_node_properties tnp
  ON tnp.ref_tree_node_guid = tree.node_guid
  AND tnp.ref_property_guid = p.key_guid
LEFT JOIN system_objects_component_properties cp
  ON cp.ref_component_guid = tree.component_guid
  AND cp.ref_property_guid = p.key_guid
WHERE p.pub_is_active = 1
  AND (tnp.pub_value IS NOT NULL OR cp.pub_value IS NOT NULL)
ORDER BY tree.node_guid, p.pub_category, p.pub_name
FOR JSON PATH, INCLUDE_NULL_VALUES;'),

  -- Upsert component property
  (N'2A0E3411-AA9E-5E39-8132-CAA02472CF3C',
   N'cms.properties.upsert_component_property',
   N'Set or update a component default property value.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'component_guid,property_guid,value',
   N'MERGE INTO system_objects_component_properties AS target
USING (SELECT
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_component_guid,
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_property_guid,
  ? AS pub_value
) AS src
ON target.ref_component_guid = src.ref_component_guid
  AND target.ref_property_guid = src.ref_property_guid
WHEN MATCHED THEN UPDATE SET
  pub_value = src.pub_value,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_component_guid, ref_property_guid, pub_value)
VALUES
  (NEWID(), src.ref_component_guid, src.ref_property_guid, src.pub_value);'),

  -- Upsert tree node property (instance override)
  (N'3B01417A-12D2-54BC-877D-8B01D7648264',
   N'cms.properties.upsert_tree_node_property',
   N'Set or update an instance override property value on a tree node.',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'tree_node_guid,property_guid,value',
   N'MERGE INTO system_objects_tree_node_properties AS target
USING (SELECT
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_tree_node_guid,
  TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_property_guid,
  ? AS pub_value
) AS src
ON target.ref_tree_node_guid = src.ref_tree_node_guid
  AND target.ref_property_guid = src.ref_property_guid
WHEN MATCHED THEN UPDATE SET
  pub_value = src.pub_value,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_tree_node_guid, ref_property_guid, pub_value)
VALUES
  (NEWID(), src.ref_tree_node_guid, src.ref_property_guid, src.pub_value);'),

  -- Delete component property
  (N'033F20C8-C2B4-5797-B24A-9B234F6C18DB',
   N'cms.properties.delete_component_property',
   N'Remove a component default property value (reverts to catalog default).',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'component_guid,property_guid',
   N'DELETE FROM system_objects_component_properties
WHERE ref_component_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND ref_property_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);'),

  -- Delete tree node property (remove instance override)
  (N'7262FDB0-719E-5530-8F44-986FCD656D1D',
   N'cms.properties.delete_tree_node_property',
   N'Remove an instance override (reverts to component default or catalog default).',
   N'CF85FB11-5981-56B7-8E43-9D453E611D43', 1, N'tree_node_guid,property_guid',
   N'DELETE FROM system_objects_tree_node_properties
WHERE ref_tree_node_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND ref_property_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);')

) AS src (key_guid, pub_name, pub_description, ref_module_guid,
          pub_is_parameterized, pub_parameter_names, pub_query_text)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
  pub_is_active = 1,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid,
   pub_is_parameterized, pub_parameter_names, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_query_text,
   src.pub_description, TRY_CAST(src.ref_module_guid AS UNIQUEIDENTIFIER),
   src.pub_is_parameterized, src.pub_parameter_names, 1);


-- ============================================================================
-- 2. Register Module Methods
-- ============================================================================

MERGE INTO system_objects_module_methods AS target
USING (VALUES
  (N'0726AA11-EC62-56EA-87EA-8A442C7CA02D', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_property_catalog',        N'Return all property definitions from the catalog.'),
  (N'DC997A4C-23FA-5EC6-801F-C783AB0046E9', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_resolved_properties',     N'Return resolved properties for all nodes in a component tree, merging instance overrides, component defaults, and catalog defaults.'),
  (N'7E0CE100-3C0C-531B-967B-DDB4BFF0D7C3', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_component_property',   N'Set or update a component default property value.'),
  (N'3F662F93-5CDF-56AE-9179-937F529C29D3', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_tree_node_property',   N'Set or update an instance override property value on a tree node.'),
  (N'1D1CE71E-9439-52E0-8301-8BC21A8931B8', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_component_property',   N'Remove a component default property (reverts to catalog default).'),
  (N'A3CA4639-D7E4-5E0D-BB3B-0E8CB6E9D046', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_tree_node_property',   N'Remove an instance override (reverts to component default or catalog default).')
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
-- 3. Register RPC Functions
-- ============================================================================

MERGE INTO system_objects_rpc_functions AS target
USING (VALUES
  (N'53E9C6A1-D876-59AC-A867-0D1032CE5446', N'get_property_catalog',        1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'0726AA11-EC62-56EA-87EA-8A442C7CA02D'),
  (N'F3319BAD-3AED-5335-8D8D-76CA31CB8C38', N'get_resolved_properties',     1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'DC997A4C-23FA-5EC6-801F-C783AB0046E9'),
  (N'65D7C93C-FDD4-513A-845C-E330518A7E8D', N'upsert_component_property',   1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'7E0CE100-3C0C-531B-967B-DDB4BFF0D7C3'),
  (N'24382870-46B0-5744-8AE8-AC6FB870CE4B', N'upsert_tree_node_property',   1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'3F662F93-5CDF-56AE-9179-937F529C29D3'),
  (N'96B2DA70-D183-5584-A82B-A088C000BF53', N'delete_component_property',   1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'1D1CE71E-9439-52E0-8301-8BC21A8931B8'),
  (N'3CB7314B-E1AC-5FDE-86E3-D65EA6E8D587', N'delete_tree_node_property',   1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'A3CA4639-D7E4-5E0D-BB3B-0E8CB6E9D046')
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
-- 4. Verify
-- ============================================================================

-- Queries (should be 8 new)
SELECT pub_name FROM system_objects_queries
WHERE pub_name LIKE N'cms.properties.%'
ORDER BY pub_name;

-- Methods (should be 6 new)
SELECT m.pub_name
FROM system_objects_module_methods m
WHERE m.key_guid IN (
  N'0726AA11-EC62-56EA-87EA-8A442C7CA02D',
  N'DC997A4C-23FA-5EC6-801F-C783AB0046E9',
  N'7E0CE100-3C0C-531B-967B-DDB4BFF0D7C3',
  N'3F662F93-5CDF-56AE-9179-937F529C29D3',
  N'1D1CE71E-9439-52E0-8301-8BC21A8931B8',
  N'A3CA4639-D7E4-5E0D-BB3B-0E8CB6E9D046'
)
ORDER BY m.pub_name;

-- RPC functions (should be 6 new)
SELECT f.pub_name, m.pub_name AS method_name
FROM system_objects_rpc_functions f
JOIN system_objects_module_methods m ON m.key_guid = f.ref_method_guid
WHERE f.key_guid IN (
  N'53E9C6A1-D876-59AC-A867-0D1032CE5446',
  N'F3319BAD-3AED-5335-8D8D-76CA31CB8C38',
  N'65D7C93C-FDD4-513A-845C-E330518A7E8D',
  N'24382870-46B0-5744-8AE8-AC6FB870CE4B',
  N'96B2DA70-D183-5584-A82B-A088C000BF53',
  N'3CB7314B-E1AC-5FDE-86E3-D65EA6E8D587'
)
ORDER BY f.pub_name;
