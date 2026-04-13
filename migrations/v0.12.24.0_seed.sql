-- ============================================================================
-- Wire ComponentBuilder to the Components category
-- The ComponentBuilder is the universal component tree editor, not just pages
-- ============================================================================

UPDATE system_objects_tree_categories
SET pub_builder_component = N'ComponentBuilder',
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = N'EC86C8B6-7094-5916-A2C5-87584021CED3'; -- components category

-- Verify both categories now point to ComponentBuilder
SELECT pub_name, pub_display, pub_builder_component
FROM system_objects_tree_categories
WHERE pub_builder_component IS NOT NULL
ORDER BY pub_sequence;