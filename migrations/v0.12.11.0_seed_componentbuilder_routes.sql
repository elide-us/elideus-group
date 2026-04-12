-- =============================================================================
-- v0.12.11.0_seed_componentbuilder_routes (FIXED)
--
-- Phase 5d seeds:
-- 1) Register ComponentBuilder component definition
-- 2) Seed additional CMS routes for navigation tree grouping and role buckets
--
-- FIX: Variables cannot cross GO batch boundaries in SSMS.
--      Role GUIDs are inlined directly in the MERGE statement.
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- =============================================================================

-- 1) ComponentBuilder component
MERGE INTO system_objects_components AS target
USING (
    SELECT
        N'DA34C586-1FA2-54DB-B573-01DF70E4D3E3' AS key_guid,
        N'ComponentBuilder' AS pub_name,
        N'section' AS pub_category,
        N'Top-level container for the Object Tree Editor panels. Hosts the tree editor, toolbox, properties panel, and query preview.' AS pub_description
) AS source
ON target.key_guid = source.key_guid
WHEN MATCHED THEN
    UPDATE SET
        pub_name = source.pub_name,
        pub_category = source.pub_category,
        pub_description = source.pub_description
WHEN NOT MATCHED THEN
    INSERT (key_guid, pub_name, pub_category, pub_description)
    VALUES (source.key_guid, source.pub_name, source.pub_category, source.pub_description);
GO

-- 2) Route seeds
-- ROLE_SYSTEM_ADMIN = 20F0C823-4742-51BE-938B-7AA5B9D36B81
-- ROLE_SERVICE_ADMIN = E8E1A4CC-0898-59F4-8B03-B2C9804516C0
-- Workbench root = EE3B1A30-83A2-5990-96FE-99F8154138E3

MERGE INTO system_objects_routes AS target
USING (
    SELECT N'F2D4BD53-0B45-52F7-9F92-FB6114BC0642' AS key_guid, N'/gallery'               AS pub_path, N'Gallery'        AS pub_title, 20  AS pub_sequence, N'PhotoLibrary'        AS pub_icon, CAST(NULL AS UNIQUEIDENTIFIER) AS ref_required_role_guid
    UNION ALL SELECT N'3096E825-274F-5F48-A3A3-236A72903099', N'/products',             N'Products',              30, N'Store',               CAST(NULL AS UNIQUEIDENTIFIER)
    UNION ALL SELECT N'A2D3DEAA-75DC-576A-AA79-BABC66A72733', N'/wiki',                 N'Wiki',                  40, N'MenuBook',            CAST(NULL AS UNIQUEIDENTIFIER)
    UNION ALL SELECT N'7BF904C0-B330-5488-9E55-345CB12B05EE', N'/system/config',        N'Configuration',        100, N'Settings',            N'20F0C823-4742-51BE-938B-7AA5B9D36B81'
    UNION ALL SELECT N'63D12504-3793-5B26-AD80-6C696F2175E0', N'/system/users',         N'Users',                110, N'People',              N'20F0C823-4742-51BE-938B-7AA5B9D36B81'
    UNION ALL SELECT N'091D86E0-0202-5617-BB08-A2CFA4F78E28', N'/system/conversations', N'Conversations',        120, N'Chat',                N'20F0C823-4742-51BE-938B-7AA5B9D36B81'
    UNION ALL SELECT N'AC1969DD-EC1B-5693-A301-BFD86C46830F', N'/system/discord',       N'Discord',              130, N'SmartToy',            N'20F0C823-4742-51BE-938B-7AA5B9D36B81'
    UNION ALL SELECT N'7989BB7E-A8C6-5703-84C0-A3C12A750576', N'/service/management',   N'Management',           200, N'AdminPanelSettings',  N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0'
    UNION ALL SELECT N'62F75B6F-A3E0-5055-9695-5C82562CDD93', N'/service/schema',       N'Schema',               210, N'Schema',              N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0'
    UNION ALL SELECT N'ED68E3DF-D5D4-53E4-92E9-EA67A472885A', N'/service/routes',       N'Routes',               220, N'Route',               N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0'
) AS source
ON target.key_guid = source.key_guid
WHEN MATCHED THEN
    UPDATE SET
        pub_path = source.pub_path,
        pub_title = source.pub_title,
        ref_root_node_guid = N'EE3B1A30-83A2-5990-96FE-99F8154138E3',
        pub_sequence = source.pub_sequence,
        pub_icon = source.pub_icon,
        ref_required_role_guid = source.ref_required_role_guid,
        pub_is_active = 1
WHEN NOT MATCHED THEN
    INSERT (key_guid, pub_path, pub_title, ref_root_node_guid, pub_sequence, pub_icon, ref_required_role_guid, pub_is_active)
    VALUES (source.key_guid, source.pub_path, source.pub_title, N'EE3B1A30-83A2-5990-96FE-99F8154138E3', source.pub_sequence, source.pub_icon, source.ref_required_role_guid, 1);
GO

-- 3) Verify
SELECT pub_path, pub_title, pub_sequence, pub_icon, ref_required_role_guid, pub_is_active
FROM system_objects_routes
ORDER BY pub_sequence;
GO