-- ============================================================================
-- ComponentBuilder Query GUID Correction
-- Replaces random key_guid values with deterministic uuid5(NS, 'query:{name}')
-- Also fixes create_tree_node query to remove NEWID() fallback
--
-- Namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Formula:   uuid5(NS, 'query:cms.pages.{operation}')
-- ============================================================================

-- The random GUIDs currently in the database (from the MERGE WHEN NOT MATCHED):
--   580F64CC-6265-4ADA-A933-67797A10B7B3  cms.pages.get_page_tree
--   E888CBF1-E478-459B-A729-E60EBE129921  cms.pages.list_components
--   E8376781-F097-43A9-8432-D4433E79C8EA  cms.pages.create_tree_node
--   2B6BBF1D-53CA-4ABB-9CBC-A42EE2781E0B  cms.pages.update_tree_node
--   30341463-B6D0-4545-A06E-06DF123F4F6B  cms.pages.delete_tree_node
--   3F7C8B75-3CFE-4300-A84D-EBF6CDD8183F  cms.pages.move_tree_node

-- Correct deterministic GUIDs:
--   E6081A1F-46DB-5000-98E6-7BF511B24AC4  query:cms.pages.get_page_tree
--   FAF53E94-C5D4-5EE2-8D97-484B829339DF  query:cms.pages.list_components
--   4C199681-B000-55CB-B447-882B927F3E7E  query:cms.pages.create_tree_node
--   71A85B36-8644-5A84-8498-FBEB0F852B33  query:cms.pages.update_tree_node
--   DD09A920-E5CA-595B-B8B2-226949F6EB73  query:cms.pages.delete_tree_node
--   4EBA6F22-B693-5B1D-A213-B1A92B917DB5  query:cms.pages.move_tree_node


-- Step 1: Update key_guid values to deterministic

UPDATE system_objects_queries
SET key_guid = N'E6081A1F-46DB-5000-98E6-7BF511B24AC4',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'580F64CC-6265-4ADA-A933-67797A10B7B3';

UPDATE system_objects_queries
SET key_guid = N'FAF53E94-C5D4-5EE2-8D97-484B829339DF',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'E888CBF1-E478-459B-A729-E60EBE129921';

UPDATE system_objects_queries
SET key_guid = N'4C199681-B000-55CB-B447-882B927F3E7E',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'E8376781-F097-43A9-8432-D4433E79C8EA';

UPDATE system_objects_queries
SET key_guid = N'71A85B36-8644-5A84-8498-FBEB0F852B33',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'2B6BBF1D-53CA-4ABB-9CBC-A42EE2781E0B';

UPDATE system_objects_queries
SET key_guid = N'DD09A920-E5CA-595B-B8B2-226949F6EB73',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'30341463-B6D0-4545-A06E-06DF123F4F6B';

UPDATE system_objects_queries
SET key_guid = N'4EBA6F22-B693-5B1D-A213-B1A92B917DB5',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'3F7C8B75-3CFE-4300-A84D-EBF6CDD8183F';


-- Step 2: Fix create_tree_node query to remove NEWID() fallback
-- The key_guid parameter is now REQUIRED (non-null), computed in Python before call

UPDATE system_objects_queries
SET pub_query_text = N'SET NOCOUNT ON;
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, pub_label, pub_field_binding, pub_sequence, ref_page_guid)
VALUES
  (TRY_CAST(? AS UNIQUEIDENTIFIER),
   TRY_CAST(? AS UNIQUEIDENTIFIER),
   TRY_CAST(? AS UNIQUEIDENTIFIER),
   ?,
   ?,
   TRY_CAST(? AS INT),
   TRY_CAST(? AS UNIQUEIDENTIFIER));
SELECT TRY_CAST(? AS UNIQUEIDENTIFIER) AS key_guid
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
    pub_parameter_names = N'key_guid,parent_guid,component_guid,label,field_binding,sequence,page_guid,key_guid_echo',
    pub_description = N'Insert a new component tree node. key_guid is REQUIRED — computed deterministically in Python before call. Returns the GUID for confirmation.',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'4C199681-B000-55CB-B447-882B927F3E7E';


-- Step 3: Verify all 6 rows now have deterministic GUIDs

SELECT key_guid, pub_name
FROM system_objects_queries
WHERE pub_name LIKE N'cms.pages.%'
ORDER BY pub_name;