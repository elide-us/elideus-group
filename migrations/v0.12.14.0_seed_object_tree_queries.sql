-- Object tree queries for CmsWorkbenchModule
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- query:cms.object_tree.get_categories -> 1CAC0976-063B-56FA-A314-A3C13968F5F8
-- query:cms.object_tree.get_category_tables -> A90D9592-8424-58E5-98B6-A750E478279A
-- query:cms.object_tree.get_table_columns -> 8FE9C76B-DE7E-5876-937E-C9EC3FD2E341

MERGE INTO system_objects_queries AS target
USING (
  SELECT
    N'1CAC0976-063B-56FA-A314-A3C13968F5F8' AS key_guid,
    N'cms.object_tree.get_categories' AS pub_name,
    N'SELECT
  sev.key_guid AS guid,
  sev.pub_name AS name,
  sev.pub_display AS display,
  sev.pub_icon AS icon,
  sev.pub_sequence AS sequence
FROM service_enum_values sev
WHERE sev.ref_category_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY sev.pub_sequence
FOR JSON PATH, INCLUDE_NULL_VALUES;' AS pub_query_text,
    N'Fetch object tree top-level categories from the object_tree_categories enum.' AS pub_description,
    N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
    1 AS pub_is_parameterized,
    N'category_enum_guid' AS pub_parameter_names

  UNION ALL SELECT
    N'A90D9592-8424-58E5-98B6-A750E478279A',
    N'cms.object_tree.get_category_tables',
    N'SELECT
  t.key_guid AS guid,
  t.pub_name AS name,
  t.pub_schema AS [schema],
  m.pub_is_root_table AS isRoot,
  m.pub_sequence AS sequence
FROM system_objects_tree_category_tables m
JOIN system_objects_database_tables t ON m.ref_table_guid = t.key_guid
WHERE m.ref_category_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY m.pub_sequence
FOR JSON PATH, INCLUDE_NULL_VALUES;',
    N'Fetch tables mapped to an object tree category.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'category_guid'

  UNION ALL SELECT
    N'8FE9C76B-DE7E-5876-937E-C9EC3FD2E341',
    N'cms.object_tree.get_table_columns',
    N'SELECT
  c.key_guid AS guid,
  c.pub_name AS name,
  c.pub_ordinal AS ordinal,
  c.pub_is_primary_key AS isPrimaryKey,
  c.pub_is_nullable AS isNullable,
  t.pub_name AS typeName,
  c.pub_max_length AS maxLength
FROM system_objects_database_columns c
LEFT JOIN system_objects_types t ON c.ref_type_guid = t.key_guid
WHERE c.ref_table_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY c.pub_ordinal
FOR JSON PATH, INCLUDE_NULL_VALUES;',
    N'Fetch columns for a specific table in the object tree.',
    N'CF85FB11-5981-56B7-8E43-9D453E611D43',
    1,
    N'table_guid'

) AS source (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names)
ON target.key_guid = TRY_CAST(source.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN
  UPDATE SET
    pub_name = source.pub_name,
    pub_query_text = source.pub_query_text,
    pub_description = source.pub_description,
    pub_is_parameterized = source.pub_is_parameterized,
    pub_parameter_names = source.pub_parameter_names,
    priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT (key_guid, pub_name, pub_query_text, pub_description, ref_module_guid, pub_is_parameterized, pub_parameter_names)
  VALUES (
    TRY_CAST(source.key_guid AS UNIQUEIDENTIFIER),
    source.pub_name,
    source.pub_query_text,
    source.pub_description,
    TRY_CAST(source.ref_module_guid AS UNIQUEIDENTIFIER),
    source.pub_is_parameterized,
    source.pub_parameter_names
  );
GO
