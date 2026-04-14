-- ============================================================================
-- v0.12.28.1 — Seed missing cms.components.get_component_tree query
--
-- The module method and RPC function are registered, but the actual SQL
-- query text was never inserted into system_objects_queries. This is why
-- the ComponentTreePanel shows empty when viewing a component.
-- ============================================================================

MERGE INTO system_objects_queries AS target
USING (SELECT
  N'E192CEE9-E739-56E0-BE48-6CAB4133C45B' AS key_guid,
  N'cms.components.get_component_tree' AS pub_name,
  N'Recursive CTE walk of a component composition tree. Starts from the root node whose ref_component_guid matches and ref_parent_guid IS NULL.' AS pub_description,
  N'CF85FB11-5981-56B7-8E43-9D453E611D43' AS ref_module_guid,
  1 AS pub_is_parameterized,
  N'component_guid' AS pub_parameter_names,
  1 AS pub_is_active,
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
    WHERE t.ref_component_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND t.ref_parent_guid IS NULL
      AND t.ref_page_guid IS NULL

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
  FOR JSON PATH, INCLUDE_NULL_VALUES;' AS pub_query_text
) AS src
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_query_text = src.pub_query_text,
  pub_description = src.pub_description,
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
SELECT key_guid, pub_name
FROM system_objects_queries
WHERE pub_name = N'cms.components.get_component_tree';
