-- ============================================================================
-- Backfill: Column registrations for ALL v0.12.5.0 tables
-- These tables were registered in system_objects_database_tables but their
-- columns were never seeded into system_objects_database_columns.
--
-- Tables backfilled:
--   system_objects_modules          (already done if previous backfill ran)
--   system_objects_module_methods   (already done if previous backfill ran)
--   system_objects_rpc_domains
--   system_objects_rpc_subdomains
--   system_objects_rpc_functions
--   system_objects_rpc_models
--   system_objects_rpc_model_fields
--   system_objects_pages
--   system_objects_page_data_bindings
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Formula: uuid5(NS, 'column:{table_name}.{column_name}')
--
-- Run BEFORE v0.12.7.0 Phase 5c (FK constraints).
-- Safe to re-run — uses NOT EXISTS guard on the first table to skip if
-- already applied.
-- ============================================================================

-- Skip if modules columns already exist (previous backfill ran)
IF NOT EXISTS (
  SELECT 1 FROM [dbo].[system_objects_database_columns]
  WHERE [key_guid] = N'F9B4AE84-8D66-5E23-842B-9BB7D1D8E25E'
)
BEGIN

DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

-- Table GUIDs (from v0.12.5.0 table registrations)
DECLARE @TBL_MOD   UNIQUEIDENTIFIER = N'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA';
DECLARE @TBL_MM    UNIQUEIDENTIFIER = N'65E5E8F3-7EFF-57F7-B4F9-087C191B7B5E';

-- system_objects_modules columns
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'F9B4AE84-8D66-5E23-842B-9BB7D1D8E25E',@TBL_MOD,@T_UUID,N'key_guid',         1,0,1,0,NULL,               NULL),
(N'B51936B8-818E-54A7-8CAA-3D1FA3CEFF36',@TBL_MOD,@T_STR, N'pub_name',         2,0,0,0,NULL,               128),
(N'585A90D3-4132-5419-AAFB-04589F413DDF',@TBL_MOD,@T_STR, N'pub_state_attr',   3,0,0,0,NULL,               128),
(N'748916AE-5237-5C7D-B9A1-6B118CA62FCF',@TBL_MOD,@T_STR, N'pub_module_path',  4,0,0,0,NULL,               256),
(N'82DE35C3-4DF7-51F0-A505-D20EAD0F1DE8',@TBL_MOD,@T_STR, N'pub_description',  5,1,0,0,NULL,               512),
(N'2088C8DF-B11F-5EF9-A541-AF125FCBAC44',@TBL_MOD,@T_BOOL,N'pub_is_active',    6,0,0,0,N'1',              NULL),
(N'8C74E518-C3FE-5B61-9AD1-95A6D84594DF',@TBL_MOD,@T_DTZ, N'priv_created_on',  7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'5BB47144-A4BF-599B-8918-49CD3F8D8DEF',@TBL_MOD,@T_DTZ, N'priv_modified_on', 8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_module_methods columns
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'ED50C297-C91B-5C0A-992A-5734664A4646',@TBL_MM,@T_UUID,N'key_guid',                1,0,1,0,NULL,               NULL),
(N'77490CE6-5F1F-5759-B230-EE7E03311769',@TBL_MM,@T_UUID,N'ref_module_guid',         2,0,0,0,NULL,               NULL),
(N'B1A92C54-53CC-5FBB-BE4A-A8E016B78847',@TBL_MM,@T_STR, N'pub_name',                3,0,0,0,NULL,               128),
(N'DF614E01-0EB8-5FD0-A505-B2E2978699DB',@TBL_MM,@T_STR, N'pub_description',         4,1,0,0,NULL,               512),
(N'51E0A588-0165-5F74-B26B-924EA7693C0D',@TBL_MM,@T_UUID,N'ref_request_model_guid',  5,1,0,0,NULL,               NULL),
(N'4C46FF1A-1DC1-5DB9-8703-7E63D5822AA0',@TBL_MM,@T_UUID,N'ref_response_model_guid', 6,1,0,0,NULL,               NULL),
(N'958F3326-6610-56FF-871A-F52225B6CDD0',@TBL_MM,@T_BOOL,N'pub_is_active',           7,0,0,0,N'1',              NULL),
(N'2199B2A7-7E28-5627-8B30-E8A532461F17',@TBL_MM,@T_DTZ, N'priv_created_on',         8,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'B95AE4B1-5A58-5FB5-B0D9-0A7850F96C92',@TBL_MM,@T_DTZ, N'priv_modified_on',        9,0,0,0,N'SYSUTCDATETIME()',NULL);

END
GO

-- Remaining tables — always safe to run (deterministic GUIDs, UNIQUE constraint catches dupes)

DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

DECLARE @TBL_RD    UNIQUEIDENTIFIER = N'D963B65C-E10E-5E04-9E30-D2220D368998'; -- rpc_domains
DECLARE @TBL_RSD   UNIQUEIDENTIFIER = N'DAFD98E7-9E2C-55AC-B2DC-64525EDDEF1A'; -- rpc_subdomains
DECLARE @TBL_RF    UNIQUEIDENTIFIER = N'2FC9F843-AD1A-5042-8BEF-4B176B46CD9E'; -- rpc_functions
DECLARE @TBL_RM    UNIQUEIDENTIFIER = N'1F64750F-DCE9-5AC1-93FE-362AF3A96B94'; -- rpc_models
DECLARE @TBL_RMF   UNIQUEIDENTIFIER = N'435807CF-4798-560C-BA94-64DB94B8F259'; -- rpc_model_fields
DECLARE @TBL_PG    UNIQUEIDENTIFIER = N'43C62BE6-0611-52E7-87A2-362240EB61C0'; -- pages
DECLARE @TBL_PDB   UNIQUEIDENTIFIER = N'5AB53AB1-B603-558C-9A6B-AC06651C8BDC'; -- page_data_bindings

-- system_objects_rpc_domains
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'008D408D-E6B3-579E-A1ED-26981A3D817A',@TBL_RD,@T_UUID,N'key_guid',              1,0,1,0,NULL,               NULL),
(N'4717B4A4-D4ED-5C4C-B885-627AED2224CC',@TBL_RD,@T_STR, N'pub_name',              2,0,0,0,NULL,               64),
(N'95F4EDE2-F6CA-533F-874F-E8F6238E2378',@TBL_RD,@T_STR, N'pub_description',       3,1,0,0,NULL,               512),
(N'982941CB-34A4-513F-9241-309881983261',@TBL_RD,@T_UUID,N'ref_required_role_guid', 4,1,0,0,NULL,               NULL),
(N'C4245DFB-E570-5848-BAD4-CB2E30794D0D',@TBL_RD,@T_BOOL,N'pub_is_active',          5,0,0,0,N'1',              NULL),
(N'738B9568-4A77-5FDD-BD8B-D1CBB72A03A0',@TBL_RD,@T_DTZ, N'priv_created_on',       6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'B4770DF7-1559-5FAC-8150-B0622B1D9CDB',@TBL_RD,@T_DTZ, N'priv_modified_on',      7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_rpc_subdomains
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'AAC8D86B-A2D0-53AB-99A1-4A3576ED96D5',@TBL_RSD,@T_UUID,N'key_guid',                       1,0,1,0,NULL,               NULL),
(N'394327CA-DE90-5083-A735-B0D44B42C4E3',@TBL_RSD,@T_STR, N'pub_name',                       2,0,0,0,NULL,               64),
(N'7E257D81-D797-59BA-B5FA-74383395ABBB',@TBL_RSD,@T_STR, N'pub_description',                3,1,0,0,NULL,               512),
(N'0E544F63-B824-5B35-A8AD-6DD6D0A44134',@TBL_RSD,@T_UUID,N'ref_domain_guid',                4,0,0,0,NULL,               NULL),
(N'B715FE82-50D2-52E1-A0F5-03C485A42047',@TBL_RSD,@T_UUID,N'ref_required_entitlement_guid',  5,1,0,0,NULL,               NULL),
(N'4282252A-7AD4-5C20-815B-C15B5A0A5BEB',@TBL_RSD,@T_BOOL,N'pub_is_active',                  6,0,0,0,N'1',              NULL),
(N'28DE63EA-51B0-5D12-B312-D6FAE6D45E59',@TBL_RSD,@T_DTZ, N'priv_created_on',                7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'1597A8EC-7144-59EE-8EBD-6D4881AB428C',@TBL_RSD,@T_DTZ, N'priv_modified_on',               8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_rpc_functions
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'837D0DF7-A622-514D-828B-AF5CFB460FA7',@TBL_RF,@T_UUID, N'key_guid',                       1, 0,1,0,NULL,               NULL),
(N'FA899A09-CC5E-5FAE-A31E-4BF936C9B9F9',@TBL_RF,@T_STR,  N'pub_name',                       2, 0,0,0,NULL,               128),
(N'246049CE-D315-5FE2-80EB-633C3419D2EF',@TBL_RF,@T_INT32,N'pub_version',                    3, 0,0,0,N'1',              NULL),
(N'509FFE8D-B49D-5188-B0EA-BD49F3BFB318',@TBL_RF,@T_STR,  N'pub_description',                4, 1,0,0,NULL,               512),
(N'9FEF8F95-9630-55C3-BDA3-7CBC0902D114',@TBL_RF,@T_UUID, N'ref_subdomain_guid',             5, 0,0,0,NULL,               NULL),
(N'EBDF3E3E-7512-5B58-91C7-81E74F56EBA4',@TBL_RF,@T_UUID, N'ref_method_guid',                6, 0,0,0,NULL,               NULL),
(N'E07D15D9-161F-5218-9155-F797510E44FF',@TBL_RF,@T_UUID, N'ref_required_role_guid',         7, 1,0,0,NULL,               NULL),
(N'2FF9E5FA-1652-59FE-83FE-E55FE928003F',@TBL_RF,@T_UUID, N'ref_required_entitlement_guid',  8, 1,0,0,NULL,               NULL),
(N'A0ED61C2-6FD3-53AB-B0DE-A276A077F509',@TBL_RF,@T_BOOL, N'pub_is_active',                  9, 0,0,0,N'1',              NULL),
(N'3C599732-4C7A-52BC-9423-4E7B4D20C996',@TBL_RF,@T_DTZ,  N'priv_created_on',                10,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'52F88E22-FD51-5269-9437-5A1C0334D72A',@TBL_RF,@T_DTZ,  N'priv_modified_on',               11,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_rpc_models
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'222FC915-87DA-59DF-858E-C359360B01E7',@TBL_RM,@T_UUID, N'key_guid',              1,0,1,0,NULL,               NULL),
(N'43DC2A79-E8C1-5B38-B92B-1326F50955C7',@TBL_RM,@T_STR,  N'pub_name',              2,0,0,0,NULL,               128),
(N'5BCB496C-84CC-5AE8-8A3B-BAFE4F54683D',@TBL_RM,@T_STR,  N'pub_description',       3,1,0,0,NULL,               512),
(N'69529E6F-CA05-59AA-AC7A-FD29E43A48E0',@TBL_RM,@T_INT32,N'pub_version',           4,0,0,0,N'1',              NULL),
(N'3F68E31D-3AFF-5A67-92F5-D9D78AB8D7B3',@TBL_RM,@T_UUID, N'ref_parent_model_guid', 5,1,0,0,NULL,               NULL),
(N'285296C4-9472-5BC0-8A4F-16CA7CEEC314',@TBL_RM,@T_DTZ,  N'priv_created_on',       6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'0295B0C8-17BB-5E30-A7B1-A37439A9899A',@TBL_RM,@T_DTZ,  N'priv_modified_on',      7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_rpc_model_fields
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'C1301800-E236-5F3D-AB97-A8DE63B38E91',@TBL_RMF,@T_UUID, N'key_guid',              1, 0,1,0,NULL,               NULL),
(N'1862F66C-A4F4-5943-92EB-397DA9259DA3',@TBL_RMF,@T_UUID, N'ref_model_guid',        2, 0,0,0,NULL,               NULL),
(N'279F47CB-9D42-5249-88C5-FA023E54A287',@TBL_RMF,@T_STR,  N'pub_name',              3, 0,0,0,NULL,               128),
(N'66F8F191-FF04-52E5-B600-3FC834CF88DA',@TBL_RMF,@T_INT32,N'pub_ordinal',           4, 0,0,0,N'0',              NULL),
(N'480623FC-08CD-5ECA-B514-458918DBE95B',@TBL_RMF,@T_UUID, N'ref_type_guid',         5, 1,0,0,NULL,               NULL),
(N'B80E548D-A040-5F0E-9CB2-F6036B362D06',@TBL_RMF,@T_UUID, N'ref_nested_model_guid', 6, 1,0,0,NULL,               NULL),
(N'0CB5AF29-E6AD-5240-996D-A5FF63E3D9F6',@TBL_RMF,@T_BOOL, N'pub_is_nullable',       7, 0,0,0,N'0',              NULL),
(N'EAE712D6-9EDC-51E8-824C-B4FF1449BB58',@TBL_RMF,@T_BOOL, N'pub_is_list',           8, 0,0,0,N'0',              NULL),
(N'2EBC5278-0F66-5C31-B4E5-6F5AC5687EB0',@TBL_RMF,@T_STR,  N'pub_default_value',     9, 1,0,0,NULL,               256),
(N'E0EF8458-D197-5476-A82E-F4B3C843393A',@TBL_RMF,@T_INT32,N'pub_max_length',        10,1,0,0,NULL,               NULL),
(N'67693873-6250-59C7-A888-BF537081F1DF',@TBL_RMF,@T_STR,  N'pub_description',       11,1,0,0,NULL,               512),
(N'F1AF833F-088F-5662-A3E4-651A9BCAEBB4',@TBL_RMF,@T_DTZ,  N'priv_created_on',       12,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'3F479B12-87B1-58AE-B2E2-94D182885E95',@TBL_RMF,@T_DTZ,  N'priv_modified_on',      13,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_pages
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'EF15112E-20A2-5A76-8203-CE309CFF1BC1',@TBL_PG,@T_UUID,N'key_guid',                       1, 0,1,0,NULL,               NULL),
(N'41EAF41C-CCCD-50BF-852C-64A0CCB75882',@TBL_PG,@T_STR, N'pub_slug',                       2, 0,0,0,NULL,               256),
(N'1F48451A-CA3B-56CF-9178-976DF089AC8D',@TBL_PG,@T_STR, N'pub_title',                      3, 1,0,0,NULL,               256),
(N'6262D14F-61DA-5394-B78F-14ABE2B886A9',@TBL_PG,@T_STR, N'pub_description',                4, 1,0,0,NULL,               512),
(N'C77F1819-BF7E-58D0-B82D-FA1580AED575',@TBL_PG,@T_STR, N'pub_icon',                       5, 1,0,0,NULL,               64),
(N'8B4AC04E-97A7-5C05-8979-AF89F0D911D3',@TBL_PG,@T_UUID,N'ref_root_component_guid',        6, 1,0,0,NULL,               NULL),
(N'23198DA1-D362-5DD7-B865-24AAA6D27E11',@TBL_PG,@T_UUID,N'ref_required_role_guid',         7, 1,0,0,NULL,               NULL),
(N'76C8B9EF-53DC-5C5A-88F3-74DBC7E3C479',@TBL_PG,@T_UUID,N'ref_required_entitlement_guid',  8, 1,0,0,NULL,               NULL),
(N'D80BBAF2-B7B8-5E07-A020-BABE17024335',@TBL_PG,@T_DTZ, N'priv_created_on',                9, 0,0,0,N'SYSUTCDATETIME()',NULL),
(N'68227A24-6A9B-51DA-9ECE-D8C3AFA53C21',@TBL_PG,@T_DTZ, N'priv_modified_on',               10,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_page_data_bindings
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'428B242D-3006-511F-825F-1DD182D465FC',@TBL_PDB,@T_UUID,N'key_guid',                 1, 0,1,0,NULL,               NULL),
(N'E98E4740-A3AF-5E9A-882F-E58F95CC1EDB',@TBL_PDB,@T_UUID,N'ref_page_guid',            2, 0,0,0,NULL,               NULL),
(N'EC7912EF-0A8C-59FA-9C8C-A775CF585192',@TBL_PDB,@T_UUID,N'ref_component_node_guid',  3, 0,0,0,NULL,               NULL),
(N'534BB2CB-55D6-5D6D-B67F-24EBAA29F157',@TBL_PDB,@T_UUID,N'ref_column_guid',          4, 1,0,0,NULL,               NULL),
(N'F1BD6F1D-FC4F-5AEB-B13F-EA0AAEC0DD26',@TBL_PDB,@T_STR, N'pub_source_type',          5, 0,0,0,N'column',         32),
(N'3728C4C3-5DDA-5EB6-B4AC-FE091B952431',@TBL_PDB,@T_STR, N'pub_literal_value',        6, 1,0,0,NULL,               1024),
(N'4F462BC5-62DA-55B0-BE21-75D4C442F822',@TBL_PDB,@T_STR, N'pub_config_key',           7, 1,0,0,NULL,               256),
(N'D0DD13E4-D1C6-5F1E-A527-DFB819363BCA',@TBL_PDB,@T_STR, N'pub_alias',                8, 1,0,0,NULL,               128),
(N'9758A995-3D07-55E1-B0BB-1CABA3EDBE1D',@TBL_PDB,@T_DTZ, N'priv_created_on',          9, 0,0,0,N'SYSUTCDATETIME()',NULL),
(N'31F7DDE6-A952-597B-9C63-FF3B47BBB1EC',@TBL_PDB,@T_DTZ, N'priv_modified_on',         10,0,0,0,N'SYSUTCDATETIME()',NULL);
GO

-- Verification
SELECT t.[pub_name], COUNT(c.[key_guid]) AS [columns]
FROM [dbo].[system_objects_database_tables] t
JOIN [dbo].[system_objects_database_columns] c ON c.[ref_table_guid] = t.[key_guid]
WHERE t.[pub_name] IN (
  'system_objects_modules', 'system_objects_module_methods',
  'system_objects_rpc_domains', 'system_objects_rpc_subdomains',
  'system_objects_rpc_functions', 'system_objects_rpc_models',
  'system_objects_rpc_model_fields', 'system_objects_pages',
  'system_objects_page_data_bindings'
)
GROUP BY t.[pub_name]
ORDER BY t.[pub_name];