-- ============================================================================
-- v0.12.26.1 — Deterministic GUID Correction (v4 — all FKs)
--
-- Two tables reference system_objects_module_methods.key_guid:
--   FK_sorf_method  on system_objects_rpc_functions
--   FK_sogmb_method on system_objects_gateway_method_bindings
--
-- Disable both, update all references + PKs, re-enable both.
-- ============================================================================

-- Disable both FK constraints
ALTER TABLE system_objects_rpc_functions NOCHECK CONSTRAINT FK_sorf_method;
ALTER TABLE system_objects_gateway_method_bindings NOCHECK CONSTRAINT FK_sogmb_method;

-- Update gateway_method_bindings references (6 rows)
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'8E3A9839-AB0D-57C5-B790-F4A3FF9957BA' WHERE ref_method_guid = N'C7C9F53E-2F31-52A0-923F-5E17CC34C1D0';
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'0354C2B0-B9AB-59DC-86F0-AD7CA8636161' WHERE ref_method_guid = N'4A3681CD-8323-574F-975D-34D48AD01893';
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'DE6B7EFD-07F9-5EC6-AEF7-FECDB07030D8' WHERE ref_method_guid = N'811868C6-593D-5B7A-B38C-E8AEDFD744DF';
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'5DD32ED3-D401-53F9-A7B9-890C57BD2367' WHERE ref_method_guid = N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84';
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'95E402B8-22A3-51E4-8D81-3E93C880882F' WHERE ref_method_guid = N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9';
UPDATE system_objects_gateway_method_bindings SET ref_method_guid = N'BF0A9BC7-A15B-5B9D-9CD6-73966FB78C8D' WHERE ref_method_guid = N'A393E831-CA69-5F00-89A4-1FE5378CEE12';

-- Update rpc_functions references (5 rows — read_object_tree_categories has no rpc_function row)
UPDATE system_objects_rpc_functions SET ref_method_guid = N'0354C2B0-B9AB-59DC-86F0-AD7CA8636161' WHERE ref_method_guid = N'4A3681CD-8323-574F-975D-34D48AD01893';
UPDATE system_objects_rpc_functions SET ref_method_guid = N'DE6B7EFD-07F9-5EC6-AEF7-FECDB07030D8' WHERE ref_method_guid = N'811868C6-593D-5B7A-B38C-E8AEDFD744DF';
UPDATE system_objects_rpc_functions SET ref_method_guid = N'5DD32ED3-D401-53F9-A7B9-890C57BD2367' WHERE ref_method_guid = N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84';
UPDATE system_objects_rpc_functions SET ref_method_guid = N'95E402B8-22A3-51E4-8D81-3E93C880882F' WHERE ref_method_guid = N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9';
UPDATE system_objects_rpc_functions SET ref_method_guid = N'BF0A9BC7-A15B-5B9D-9CD6-73966FB78C8D' WHERE ref_method_guid = N'A393E831-CA69-5F00-89A4-1FE5378CEE12';

-- Update the method PKs (6 rows)
UPDATE system_objects_module_methods SET key_guid = N'8E3A9839-AB0D-57C5-B790-F4A3FF9957BA' WHERE key_guid = N'C7C9F53E-2F31-52A0-923F-5E17CC34C1D0';
UPDATE system_objects_module_methods SET key_guid = N'0354C2B0-B9AB-59DC-86F0-AD7CA8636161' WHERE key_guid = N'4A3681CD-8323-574F-975D-34D48AD01893';
UPDATE system_objects_module_methods SET key_guid = N'DE6B7EFD-07F9-5EC6-AEF7-FECDB07030D8' WHERE key_guid = N'811868C6-593D-5B7A-B38C-E8AEDFD744DF';
UPDATE system_objects_module_methods SET key_guid = N'5DD32ED3-D401-53F9-A7B9-890C57BD2367' WHERE key_guid = N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84';
UPDATE system_objects_module_methods SET key_guid = N'95E402B8-22A3-51E4-8D81-3E93C880882F' WHERE key_guid = N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9';
UPDATE system_objects_module_methods SET key_guid = N'BF0A9BC7-A15B-5B9D-9CD6-73966FB78C8D' WHERE key_guid = N'A393E831-CA69-5F00-89A4-1FE5378CEE12';

-- Re-enable with validation
ALTER TABLE system_objects_rpc_functions WITH CHECK CHECK CONSTRAINT FK_sorf_method;
ALTER TABLE system_objects_gateway_method_bindings WITH CHECK CHECK CONSTRAINT FK_sogmb_method;

-- Verify
SELECT m.key_guid, m.pub_name
FROM system_objects_module_methods m
WHERE m.ref_module_guid = N'CF85FB11-5981-56B7-8E43-9D453E611D43'
ORDER BY m.pub_name;