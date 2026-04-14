-- ============================================================================
-- v0.12.26.0 — service:objects Data Registration
--
-- Registers:
--   1. The 'objects' subdomain under the 'service' domain
--   2. 18 module methods for CmsWorkbenchModule (9 existing unregistered +
--      9 new from ComponentBuilder work)
--   3. 23 RPC function entries linking operations to methods
--
-- All new GUIDs are deterministic:
--   uuid5(DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67, '{entity_type}:{natural_key}')
--
-- CmsWorkbenchModule: CF85FB11-5981-56B7-8E43-9D453E611D43
-- Service domain:     DBC16219-905A-58C8-8F69-3EFFF6E0424A
-- ROLE_SERVICE_ADMIN: E8E1A4CC-0898-59F4-8B03-B2C9804516C0
-- ============================================================================


-- ============================================================================
-- 1. Register 'objects' subdomain under 'service' domain
-- ============================================================================

MERGE INTO system_objects_rpc_subdomains AS target
USING (SELECT
  N'65663AC2-81EE-529E-82E4-F5166D9066F2' AS key_guid,
  N'objects' AS pub_name,
  N'DBC16219-905A-58C8-8F69-3EFFF6E0424A' AS ref_domain_guid,
  1 AS pub_is_active
) AS src
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_is_active = src.pub_is_active,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, ref_domain_guid, pub_is_active)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name,
   TRY_CAST(src.ref_domain_guid AS UNIQUEIDENTIFIER), src.pub_is_active);


-- ============================================================================
-- 2. Register module methods for CmsWorkbenchModule
--    All methods that exist in code but have no module_methods row.
--    Existing methods (read_object_tree_*, upsert_type, etc.) are already
--    registered — we only add the ones that are missing.
-- ============================================================================

MERGE INTO system_objects_module_methods AS target
USING (VALUES
  -- Component tree operations
  (N'2BCB0862-8F63-535E-9CF7-4D4D633F53E3', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_page_tree',          N'Return recursive component tree for a page definition.'),
  (N'9EF7C060-B421-5E6C-B553-49EF96787856', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_component_tree',     N'Return composition tree for a component (walks from component GUID root node).'),
  (N'CBCB69F4-C8A7-556B-9AF6-25863730404C', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'create_tree_node',       N'Insert a new component tree node with deterministic GUID.'),
  (N'EDD68210-D4BA-5A45-BE63-EC45F4D3CF0D', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'update_tree_node',       N'Update tree node properties (COALESCE partial update).'),
  (N'8792EBF5-9F55-5827-A553-D7BF178315DC', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_tree_node',       N'Delete a tree node and cascade all descendants via recursive CTE.'),
  (N'D006C21D-8108-5428-B28C-DA1B02788344', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'move_tree_node',         N'Move a tree node to a new parent and/or sequence position.'),

  -- Component definition operations
  (N'AE6F01C7-CB9D-5552-8C4B-2A3EF5107A17', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_component_detail',  N'Return full detail for a single component with resolved type name.'),
  (N'299F028C-00DC-5FA8-8130-AFF121A24978', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'list_components',        N'Return all registered components for the component picker.'),
  (N'8CFB7CB7-FDB6-5615-AF0D-634D398782A8', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_component',      N'Update component description and default type.'),

  -- Database operations (already exist in code, not registered)
  (N'4861B5FC-C30B-56C4-A091-01269574FB53', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_database_table', N'Upsert a database table registration.'),
  (N'DDB0D57B-3962-539B-B466-786E031AE4EE', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_database_table', N'Delete a database table registration.'),
  (N'ED2F5575-BD09-5570-9BE0-BBDFB859A691', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_database_column',N'Upsert a database column registration.'),
  (N'A384CF5B-956A-5FDC-B245-24E8C3290B5F', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_database_column',N'Delete a database column registration.'),

  -- Module operations (already exist in code, not registered)
  (N'2CE4E5BD-50B4-5F2B-9849-E92FDEAAA7E0', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_module_methods',    N'Return methods for a module with joined model names.'),
  (N'8C950E98-B70A-5254-99D5-FDC6F5EE54A3', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_module',         N'Update module description and is_active.'),
  (N'6D67008B-E107-5EFE-85DE-7A1E125A344B', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'upsert_module_method',  N'Insert or update a module method.'),
  (N'5D78C187-9CEA-5B6F-A346-27A3D0279D95', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'delete_module_method',  N'Delete a module method by GUID.'),
  (N'E748561F-2316-56DF-B791-7057C63D0F26', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'get_method_contract',   N'Return contract info for a method with joined model names.')
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
-- 3. Register RPC functions
--    All operations in the service:objects dispatcher mapped to their methods.
--    Subdomain GUID: 65663AC2 (service.objects)
-- ============================================================================

MERGE INTO system_objects_rpc_functions AS target
USING (VALUES
  -- Component tree operations
  (N'699B88DF-B409-547C-9EFE-F3624AEA51B1', N'get_page_tree',             1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'2BCB0862-8F63-535E-9CF7-4D4D633F53E3'),
  (N'25348F61-9229-5461-B02C-ED66D6FEA821', N'get_component_tree',        1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'9EF7C060-B421-5E6C-B553-49EF96787856'),
  (N'83275F4C-4CC4-5337-B0A8-6C758E68FAD5', N'create_tree_node',          1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'CBCB69F4-C8A7-556B-9AF6-25863730404C'),
  (N'F7A3128D-F6A5-529E-A0BF-35D36C053E88', N'update_tree_node',          1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'EDD68210-D4BA-5A45-BE63-EC45F4D3CF0D'),
  (N'86E7AE72-3C58-5C19-93A9-26DF84954A21', N'delete_tree_node',          1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'8792EBF5-9F55-5827-A553-D7BF178315DC'),
  (N'CF0BC6C2-6172-565C-A477-0E9CA012A637', N'move_tree_node',            1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'D006C21D-8108-5428-B28C-DA1B02788344'),

  -- Component definition operations
  (N'9D98FFF0-AD0A-5DAB-B264-CDCC0ED6DC1A', N'get_component_detail',     1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'AE6F01C7-CB9D-5552-8C4B-2A3EF5107A17'),
  (N'22645C0B-FF16-5F6A-BB7C-F24B22E0B3A9', N'list_components',           1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'299F028C-00DC-5FA8-8130-AFF121A24978'),
  (N'20E51041-F6BA-5B2A-90A4-85414476AD03', N'upsert_component',          1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'8CFB7CB7-FDB6-5615-AF0D-634D398782A8'),

  -- Object tree browsing (existing code, was never registered)
  (N'20B81046-80A5-5799-BC24-710CCAB4448B', N'read_object_tree_children', 1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'4A3681CD-8323-574F-975D-34D48AD01893'),
  (N'4C98AD5F-5FBB-5D41-8051-B67697253108', N'read_object_tree_detail',   1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'811868C6-593D-5B7A-B38C-E8AEDFD744DF'),

  -- Database CRUD
  (N'002F7947-CC69-5094-8557-DB3527931C1F', N'upsert_database_table',     1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'4861B5FC-C30B-56C4-A091-01269574FB53'),
  (N'DE1C932D-B861-5C08-8EFC-EDD94AED5B33', N'delete_database_table',     1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'DDB0D57B-3962-539B-B466-786E031AE4EE'),
  (N'300E893C-7A1E-5A6C-99C8-DF689A7C6997', N'upsert_database_column',    1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'ED2F5575-BD09-5570-9BE0-BBDFB859A691'),
  (N'3BD8ABB2-EE54-5C26-9467-DB950A47EA71', N'delete_database_column',    1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'A384CF5B-956A-5FDC-B245-24E8C3290B5F'),

  -- Type CRUD
  (N'411E6BAF-CC4C-5F48-92AF-AD57839EC30B', N'upsert_type',               1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'60C88DA3-79BD-5BD9-BF5F-C16671FFDC84'),
  (N'9D69BE0A-1BD9-5808-BD6F-026522AF9077', N'delete_type',               1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'6E075002-1B6C-5BD4-BC73-6F9BB8ECD5B9'),
  (N'77A0C7B1-540C-554D-8D56-2C610996FCEE', N'get_type_controls',         1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'A393E831-CA69-5F00-89A4-1FE5378CEE12'),

  -- Module CRUD
  (N'5543C908-2B8F-55DB-B226-E409958336B4', N'get_module_methods',        1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'2CE4E5BD-50B4-5F2B-9849-E92FDEAAA7E0'),
  (N'028EAB5B-4EBD-5F5B-A60A-A3B87B0D2322', N'upsert_module',             1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'8C950E98-B70A-5254-99D5-FDC6F5EE54A3'),
  (N'B0C23F80-9339-5808-BC85-10A7EF6A4BF8', N'upsert_module_method',      1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'6D67008B-E107-5EFE-85DE-7A1E125A344B'),
  (N'33F7B66E-D929-539B-B78A-D0C1FF5B9D1B', N'delete_module_method',      1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'5D78C187-9CEA-5B6F-A346-27A3D0279D95'),
  (N'CF4AD276-AEFB-5DC8-861A-9AE4DBBF8350', N'get_method_contract',       1, N'65663AC2-81EE-529E-82E4-F5166D9066F2', N'E748561F-2316-56DF-B791-7057C63D0F26')
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

-- Subdomain count (should be 11: 10 existing + 1 new)
SELECT COUNT(*) AS subdomain_count FROM system_objects_rpc_subdomains;

-- New subdomain
SELECT key_guid, pub_name, ref_domain_guid
FROM system_objects_rpc_subdomains
WHERE pub_name = N'objects';

-- Methods for CmsWorkbenchModule (should include all 18 new + existing)
SELECT m.key_guid, m.pub_name, m.pub_description
FROM system_objects_module_methods m
WHERE m.ref_module_guid = N'CF85FB11-5981-56B7-8E43-9D453E611D43'
ORDER BY m.pub_name;

-- RPC functions under service.objects (should be 23)
SELECT f.key_guid, f.pub_name, f.pub_version, m.pub_name AS method_name
FROM system_objects_rpc_functions f
JOIN system_objects_module_methods m ON m.key_guid = f.ref_method_guid
WHERE f.ref_subdomain_guid = N'65663AC2-81EE-529E-82E4-F5166D9066F2'
ORDER BY f.pub_name;