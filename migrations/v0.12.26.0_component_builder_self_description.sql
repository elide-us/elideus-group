-- ============================================================================
-- v0.12.25.0 Hotfix — ContractPanel GUID Correction + Tree Nodes
--
-- The ContractPanel component was inserted with a typo'd GUID:
--   Wrong:   0FB4B481-AEB9-504D-AAEC-1B376A50DC72
--   Correct: 0FB4B481-AEB9-504D-AAEC-1B37650DC722
--
-- This script corrects it and then inserts the tree nodes (Block 2).
-- ============================================================================



MERGE INTO system_objects_components AS target
USING (VALUES
  (N'3181D03C-15F6-554D-841C-623CD51635AA', N'ComponentPreview',    N'section', N'Canvas-based abstract visual preview of the selected component layout and composition. Pan/zoom/drag interaction.'),
  (N'CE8C2A85-BD51-5994-8278-005D0D4A4C1D', N'PropertyPanel',      N'section', N'Property editor for the selected component. Shows name, category, description, default type, type controls, timestamps.'),
  (N'BE00786B-C289-5963-A8C8-3D0AFFC6D6A7', N'ComponentTreePanel', N'section', N'Recursive tree editor for component composition. Add, delete, reorder child components within a container.'),
  (N'4475FF51-0E31-5CE6-AFDA-DB3EC760200D', N'QueryPreviewPanel',  N'section', N'Read-only display of the derived SQL query from data bindings. Shows the query that ContractQueryBuilder generates.'),
  (N'0FB4B481-AEB9-504D-AAEC-1B376A50DC722', N'ContractPanel',      N'section', N'Split panel showing inbound (request) and outbound (response) data contracts for the component.')
) AS src (key_guid, pub_name, pub_category, pub_description)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_category = src.pub_category,
  pub_description = src.pub_description,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_category, pub_description)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_category, src.pub_description);



-- Step 1: Fix the ContractPanel GUID
UPDATE system_objects_components
SET key_guid = N'0FB4B481-AEB9-504D-AAEC-1B37650DC722',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'0FB4B481-AEB9-504D-AAEC-1B376A50DC72';


-- Step 2: Insert the ComponentBuilder composition tree (Block 2 retry)

-- 2a. Root node — ComponentBuilder itself
MERGE INTO system_objects_component_tree AS target
USING (SELECT
  N'832BCD2B-DCB4-5472-91A5-289D50D64A19' AS key_guid,
  NULL AS ref_parent_guid,
  N'DA34C586-1FA2-54DB-B573-01DF70E4D3E3' AS ref_component_guid,
  0 AS pub_sequence
) AS src
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  ref_component_guid = TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER),
  pub_sequence = src.pub_sequence,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_parent_guid, ref_component_guid, pub_sequence)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_parent_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER),
   src.pub_sequence);

-- 2b. Child slots
MERGE INTO system_objects_component_tree AS target
USING (VALUES
  (N'38FD4EA5-53BA-543F-A24B-2D2B2269D136', N'832BCD2B-DCB4-5472-91A5-289D50D64A19', N'3181D03C-15F6-554D-841C-623CD51635AA', N'Preview', 1),
  (N'4B1E71A4-511B-574C-B4BE-C397A6412D84', N'832BCD2B-DCB4-5472-91A5-289D50D64A19', N'CE8C2A85-BD51-5994-8278-005D0D4A4C1D', N'Properties', 2),
  (N'3E218169-0A74-5C8A-8BC3-420B35E72FEB', N'832BCD2B-DCB4-5472-91A5-289D50D64A19', N'BE00786B-C289-5963-A8C8-3D0AFFC6D6A7', N'Component Tree', 3),
  (N'04F0599A-DDBE-52BB-9D90-213FF01A7973', N'832BCD2B-DCB4-5472-91A5-289D50D64A19', N'4475FF51-0E31-5CE6-AFDA-DB3EC760200D', N'Query Preview', 4),
  (N'EA861C00-B174-592F-A060-0E05FA7649E7', N'832BCD2B-DCB4-5472-91A5-289D50D64A19', N'0FB4B481-AEB9-504D-AAEC-1B37650DC722', N'Contracts', 5)
) AS src (key_guid, ref_parent_guid, ref_component_guid, pub_label, pub_sequence)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  ref_parent_guid = TRY_CAST(src.ref_parent_guid AS UNIQUEIDENTIFIER),
  ref_component_guid = TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER),
  pub_label = src.pub_label,
  pub_sequence = src.pub_sequence,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_parent_guid, ref_component_guid, pub_label, pub_sequence)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_parent_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER),
   src.pub_label,
   src.pub_sequence);


-- Step 3: Verify

-- ContractPanel GUID should be correct now
SELECT key_guid, pub_name
FROM system_objects_components
WHERE pub_name = N'ContractPanel';

-- Tree nodes (should be 6: root + 5 children)
SELECT t.key_guid, c.pub_name, t.pub_label, t.pub_sequence
FROM system_objects_component_tree t
JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
WHERE t.key_guid = N'832BCD2B-DCB4-5472-91A5-289D50D64A19'
   OR t.ref_parent_guid = N'832BCD2B-DCB4-5472-91A5-289D50D64A19'
ORDER BY t.pub_sequence;