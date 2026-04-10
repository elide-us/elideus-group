

-- ============================================================================
-- 5. Object Tree Registration — Tables
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(N'B036FE5D-81BD-5538-9FDD-96C1F15AE271', N'system_objects_components',     N'dbo'),
(N'8E6C9B81-98A7-596F-BC74-FFDE264D7763', N'system_objects_component_tree', N'dbo'),
(N'2C7AE44B-FE79-5B59-B848-21992A15C2B8', N'system_objects_routes',         N'dbo'),
(N'8FC3FA36-26DC-5513-A06D-035BFCD7DDFD', N'system_objects_type_controls',  N'dbo');
GO


-- ============================================================================
-- 6. Object Tree Registration — Columns
-- ============================================================================

-- Type GUIDs (convenience variables)
DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

-- Table GUIDs
DECLARE @TBL_COMP  UNIQUEIDENTIFIER = N'B036FE5D-81BD-5538-9FDD-96C1F15AE271';
DECLARE @TBL_TREE  UNIQUEIDENTIFIER = N'8E6C9B81-98A7-596F-BC74-FFDE264D7763';
DECLARE @TBL_ROUTE UNIQUEIDENTIFIER = N'2C7AE44B-FE79-5B59-B848-21992A15C2B8';
DECLARE @TBL_TC    UNIQUEIDENTIFIER = N'8FC3FA36-26DC-5513-A06D-035BFCD7DDFD';

-- system_objects_components columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'AAB3F365-5A33-54E2-8D23-35FA657A306E',@TBL_COMP,@T_UUID,N'key_guid',              1,0,1,0,NULL,              NULL),
(N'3023FA41-BA9D-5EE6-97E5-874835E86D46',@TBL_COMP,@T_STR, N'pub_name',              2,0,0,0,NULL,              128),
(N'A7A79903-F623-5DAC-9445-5B0022F58279',@TBL_COMP,@T_STR, N'pub_category',          3,0,0,0,NULL,              32),
(N'5EDE331A-A263-50AE-997B-999229976582',@TBL_COMP,@T_STR, N'pub_description',       4,1,0,0,NULL,              512),
(N'03760408-7CDE-564C-9129-4515BE08E392',@TBL_COMP,@T_UUID,N'ref_default_type_guid', 5,1,0,0,NULL,              NULL),
(N'BC98D1F2-AEC1-5F32-8278-218E9464F6ED',@TBL_COMP,@T_DTZ, N'priv_created_on',       6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'678B478F-BC76-52F0-8475-4AE38E5C9A22',@TBL_COMP,@T_DTZ, N'priv_modified_on',      7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_component_tree columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'8167528D-23A5-5C05-B8F4-C7DA0C3E0EDB',@TBL_TREE,@T_UUID,N'key_guid',                1, 0,1,0,NULL,               NULL),
(N'6AF58809-88E4-5ECA-8E20-DE6615DEFEF4',@TBL_TREE,@T_UUID,N'ref_parent_guid',         2, 1,0,0,NULL,               NULL),
(N'741861B8-7E1D-5868-AF62-9AD4514B4FA1',@TBL_TREE,@T_UUID,N'ref_component_guid',      3, 0,0,0,NULL,               NULL),
(N'A802C113-072F-5E9C-AB6D-D23F97CD5E28',@TBL_TREE,@T_UUID,N'ref_type_guid',           4, 1,0,0,NULL,               NULL),
(N'B2A8781F-9C83-554E-AF8E-A9785CB550E1',@TBL_TREE,@T_STR, N'pub_label',               5, 1,0,0,NULL,               256),
(N'627B8E1F-F423-5AC8-AC18-D3138F19C317',@TBL_TREE,@T_STR, N'pub_field_binding',       6, 1,0,0,NULL,               128),
(N'D72646C1-F7E6-5DEB-8294-932C0BFF078E',@TBL_TREE,@T_INT32,N'pub_sequence',           7, 0,0,0,N'0',              NULL),
(N'D5875C1B-6C8A-5C7C-AA33-03FE492A68A2',@TBL_TREE,@T_STR, N'pub_rpc_operation',       8, 1,0,0,NULL,               256),
(N'8B31F6F6-6618-5E93-B933-EEA54BDEBA64',@TBL_TREE,@T_STR, N'pub_rpc_contract',        9, 1,0,0,NULL,               256),
(N'C6A7D5B6-A167-5569-BEFF-0F18514E2FE4',@TBL_TREE,@T_STR, N'pub_mutation_operation',  10,1,0,0,NULL,               256),
(N'98B5B0E4-35C4-5B7F-9419-CC152F1548FA',@TBL_TREE,@T_BOOL,N'pub_is_default_editable', 11,0,0,0,N'0',              NULL),
(N'813078A3-3C5D-515A-8D8F-3311B2DC0B6F',@TBL_TREE,@T_DTZ, N'priv_created_on',         12,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'0CBA5420-FC6F-5770-81F5-C487902A2840',@TBL_TREE,@T_DTZ, N'priv_modified_on',        13,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_routes columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'822FFFA2-1B2F-5A61-9091-824D94D9817E',@TBL_ROUTE,@T_UUID,N'key_guid',                1, 0,1,0,NULL,               NULL),
(N'FB893E7C-B5EF-599A-948C-2BEE14E4A3D3',@TBL_ROUTE,@T_STR, N'pub_path',                2, 0,0,0,NULL,               512),
(N'C4762782-99C6-53D5-980E-6795895B1601',@TBL_ROUTE,@T_STR, N'pub_title',               3, 1,0,0,NULL,               256),
(N'F016772E-5615-5EB4-B28C-D0DACC6702FB',@TBL_ROUTE,@T_UUID,N'ref_root_node_guid',      4, 0,0,0,NULL,               NULL),
(N'2A6B85DD-4184-5CE1-A410-5A3EB9E3D86D',@TBL_ROUTE,@T_INT32,N'pub_sequence',           5, 0,0,0,N'0',              NULL),
(N'0B765912-BCF1-54E1-92DE-0927F124BE26',@TBL_ROUTE,@T_STR, N'pub_icon',                6, 1,0,0,NULL,               64),
(N'D0EF96FB-FB47-575E-ACA7-803628D04424',@TBL_ROUTE,@T_UUID,N'ref_parent_route_guid',   7, 1,0,0,NULL,               NULL),
(N'FD2F5359-237B-57F8-882D-3E4A19CDB707',@TBL_ROUTE,@T_UUID,N'ref_required_role_guid',  8, 1,0,0,NULL,               NULL),
(N'2DC61F7D-BD79-5888-8166-747BCD329B48',@TBL_ROUTE,@T_BOOL,N'pub_is_active',           9, 0,0,0,N'1',              NULL),
(N'C84B8BDE-9D4E-550C-89A9-882F7229E223',@TBL_ROUTE,@T_DTZ, N'priv_created_on',         10,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'15D50CFB-27F6-5B39-87A4-FE142B3A163E',@TBL_ROUTE,@T_DTZ, N'priv_modified_on',        11,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_type_controls columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'65D0A7CC-7A49-5393-83B8-5B3211FA83F9',@TBL_TC,@T_UUID,N'key_guid',           1,0,1,0,NULL,               NULL),
(N'6D71F07B-4B89-5BBE-A61E-7C48DEA4F0BC',@TBL_TC,@T_UUID,N'ref_type_guid',      2,0,0,0,NULL,               NULL),
(N'FFCA15F5-C7EB-5DE7-AC04-893A5ABB91C7',@TBL_TC,@T_UUID,N'ref_component_guid', 3,0,0,0,NULL,               NULL),
(N'08F7FA33-B607-5C20-8BAE-50768884D2D2',@TBL_TC,@T_BOOL,N'pub_is_default',     4,0,0,0,N'0',              NULL),
(N'3F211875-07D3-51C9-9056-3640DA00B934',@TBL_TC,@T_DTZ, N'priv_created_on',    5,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'D7114F05-D4F9-5B4C-A520-2A196012211F',@TBL_TC,@T_DTZ, N'priv_modified_on',   6,0,0,0,N'SYSUTCDATETIME()',NULL);
GO


-- ============================================================================
-- 7. Object Tree Registration — Indexes
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_indexes] ([ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
-- system_objects_components
(N'B036FE5D-81BD-5538-9FDD-96C1F15AE271', N'UQ_system_objects_components_name', N'pub_name', 1),
-- system_objects_component_tree
(N'8E6C9B81-98A7-596F-BC74-FFDE264D7763', N'IX_soct_parent',    N'ref_parent_guid',    0),
(N'8E6C9B81-98A7-596F-BC74-FFDE264D7763', N'IX_soct_component', N'ref_component_guid', 0),
-- system_objects_routes
(N'2C7AE44B-FE79-5B59-B848-21992A15C2B8', N'UQ_system_objects_routes_path', N'pub_path',              1),
(N'2C7AE44B-FE79-5B59-B848-21992A15C2B8', N'IX_sor_parent',               N'ref_parent_route_guid', 0),
(N'2C7AE44B-FE79-5B59-B848-21992A15C2B8', N'IX_sor_root_node',            N'ref_root_node_guid',    0),
-- system_objects_type_controls
(N'8FC3FA36-26DC-5513-A06D-035BFCD7DDFD', N'UQ_sotc_type_component', N'ref_type_guid,ref_component_guid', 1);
GO


-- ============================================================================
-- 8. Object Tree Registration — FK Constraints
-- ============================================================================

-- Type GUIDs for referenced PKs
DECLARE @COL_TYPES_PK   UNIQUEIDENTIFIER = N'ACC8E8B1-F5E5-5D93-B814-B8FF571DE287'; -- system_objects_types.key_guid
DECLARE @COL_ROLES_PK   UNIQUEIDENTIFIER = N'AA276608-C963-592B-87BF-0B2C99A44148'; -- system_auth_roles.key_guid

DECLARE @TBL_TYPES2     UNIQUEIDENTIFIER = N'73377644-3E86-5FE6-B982-0B224749C358'; -- system_objects_types
DECLARE @TBL_ROLES2     UNIQUEIDENTIFIER = N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B'; -- system_auth_roles
DECLARE @TBL_COMP2      UNIQUEIDENTIFIER = N'B036FE5D-81BD-5538-9FDD-96C1F15AE271'; -- system_objects_components
DECLARE @TBL_TREE2      UNIQUEIDENTIFIER = N'8E6C9B81-98A7-596F-BC74-FFDE264D7763'; -- system_objects_component_tree
DECLARE @TBL_ROUTE2     UNIQUEIDENTIFIER = N'2C7AE44B-FE79-5B59-B848-21992A15C2B8'; -- system_objects_routes
DECLARE @TBL_TC2        UNIQUEIDENTIFIER = N'8FC3FA36-26DC-5513-A06D-035BFCD7DDFD'; -- system_objects_type_controls

-- PK column GUIDs for referenced tables
DECLARE @COL_COMP_PK    UNIQUEIDENTIFIER = N'AAB3F365-5A33-54E2-8D23-35FA657A306E'; -- system_objects_components.key_guid
DECLARE @COL_TREE_PK    UNIQUEIDENTIFIER = N'8167528D-23A5-5C05-B8F4-C7DA0C3E0EDB'; -- system_objects_component_tree.key_guid
DECLARE @COL_ROUTE_PK   UNIQUEIDENTIFIER = N'822FFFA2-1B2F-5A61-9091-824D94D9817E'; -- system_objects_routes.key_guid

INSERT INTO [dbo].[system_objects_database_constraints] ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
-- system_objects_components.ref_default_type_guid → system_objects_types.key_guid
(@TBL_COMP2,  N'03760408-7CDE-564C-9129-4515BE08E392', @TBL_TYPES2, @COL_TYPES_PK),

-- system_objects_component_tree.ref_parent_guid → system_objects_component_tree.key_guid (self-ref)
(@TBL_TREE2,  N'6AF58809-88E4-5ECA-8E20-DE6615DEFEF4', @TBL_TREE2,  @COL_TREE_PK),
-- system_objects_component_tree.ref_component_guid → system_objects_components.key_guid
(@TBL_TREE2,  N'741861B8-7E1D-5868-AF62-9AD4514B4FA1', @TBL_COMP2,  @COL_COMP_PK),
-- system_objects_component_tree.ref_type_guid → system_objects_types.key_guid
(@TBL_TREE2,  N'A802C113-072F-5E9C-AB6D-D23F97CD5E28', @TBL_TYPES2, @COL_TYPES_PK),

-- system_objects_routes.ref_root_node_guid → system_objects_component_tree.key_guid
(@TBL_ROUTE2, N'F016772E-5615-5EB4-B28C-D0DACC6702FB', @TBL_TREE2,  @COL_TREE_PK),
-- system_objects_routes.ref_parent_route_guid → system_objects_routes.key_guid (self-ref)
(@TBL_ROUTE2, N'D0EF96FB-FB47-575E-ACA7-803628D04424', @TBL_ROUTE2, @COL_ROUTE_PK),
-- system_objects_routes.ref_required_role_guid → system_auth_roles.key_guid
(@TBL_ROUTE2, N'FD2F5359-237B-57F8-882D-3E4A19CDB707', @TBL_ROLES2, @COL_ROLES_PK),

-- system_objects_type_controls.ref_type_guid → system_objects_types.key_guid
(@TBL_TC2,    N'6D71F07B-4B89-5BBE-A61E-7C48DEA4F0BC', @TBL_TYPES2, @COL_TYPES_PK),
-- system_objects_type_controls.ref_component_guid → system_objects_components.key_guid
(@TBL_TC2,    N'FFCA15F5-C7EB-5DE7-AC04-893A5ABB91C7', @TBL_COMP2,  @COL_COMP_PK);
GO


-- ============================================================================
-- 9. Object Tree Registration — DECIMAL_28_12 type in tables registry
--    (The type row was inserted above but its table is already registered.
--     No additional table registration needed, just verify.)
-- ============================================================================


-- ============================================================================
-- 10. Verification
-- ============================================================================

SELECT 'system_objects_types' AS [table],               COUNT(*) AS [rows] FROM [dbo].[system_objects_types];
SELECT 'system_objects_database_tables' AS [table],     COUNT(*) AS [rows] FROM [dbo].[system_objects_database_tables];
SELECT 'system_objects_database_columns' AS [table],    COUNT(*) AS [rows] FROM [dbo].[system_objects_database_columns];
SELECT 'system_objects_database_indexes' AS [table],    COUNT(*) AS [rows] FROM [dbo].[system_objects_database_indexes];
SELECT 'system_objects_database_constraints' AS [table],COUNT(*) AS [rows] FROM [dbo].[system_objects_database_constraints];
SELECT 'system_objects_components' AS [table],          COUNT(*) AS [rows] FROM [dbo].[system_objects_components];
SELECT 'system_objects_component_tree' AS [table],      COUNT(*) AS [rows] FROM [dbo].[system_objects_component_tree];
SELECT 'system_objects_routes' AS [table],              COUNT(*) AS [rows] FROM [dbo].[system_objects_routes];
SELECT 'system_objects_type_controls' AS [table],       COUNT(*) AS [rows] FROM [dbo].[system_objects_type_controls];

-- Verify new tables are self-described
SELECT t.[pub_name] AS [table], COUNT(c.[key_guid]) AS [columns]
FROM [dbo].[system_objects_database_tables] t
LEFT JOIN [dbo].[system_objects_database_columns] c ON c.[ref_table_guid] = t.[key_guid]
WHERE t.[pub_name] IN (
  'system_objects_components',
  'system_objects_component_tree',
  'system_objects_routes',
  'system_objects_type_controls'
)
GROUP BY t.[pub_name]
ORDER BY t.[pub_name];

-- Verify DECIMAL_28_12 exists
SELECT [pub_name], [pub_mssql_type], [pub_typescript_type]
FROM [dbo].[system_objects_types]
WHERE [pub_name] = N'DECIMAL_28_12';
