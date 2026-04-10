-- ============================================================================
-- TheOracleRPC v0.12.1.0 — Object Tree Reflection System
-- Date: 2026-04-09
-- Purpose:
--   Self-describing object tree. Every PK is a deterministic UUID5
--   from the DECAFBAD namespace. No IDENTITY columns.
--
--   UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   Types:   uuid5(NS, 'type:{pub_name}')
--   Tables:  uuid5(NS, 'table:{pub_name}')
--   Columns: uuid5(NS, 'column:{table_name}.{column_name}')
--
--   Column prefixes: key_ / pub_ / priv_ / ref_ / ext_
--     key_  — primary key
--     pub_  — functional/public data
--     priv_ — bookkeeping/audit
--     ref_  — foreign key references
--     ext_  — extensions (future)
-- ============================================================================

-- ============================================================================
-- system_objects_types
-- ============================================================================

CREATE TABLE [dbo].[system_objects_types] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(64)      NOT NULL,
  [pub_mssql_type]        NVARCHAR(128)     NOT NULL,
  [pub_postgresql_type]   NVARCHAR(128)     NULL,
  [pub_mysql_type]        NVARCHAR(128)     NULL,
  [pub_python_type]       NVARCHAR(128)     NOT NULL,
  [pub_typescript_type]   NVARCHAR(128)     NOT NULL,
  [pub_json_type]         NVARCHAR(64)      NOT NULL,
  [pub_odbc_type_code]    INT               NULL,
  [pub_max_length]        INT               NULL,
  [pub_notes]             NVARCHAR(512)     NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sot_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sot_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_types]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_system_objects_types_name] UNIQUE ([pub_name])
);
GO

-- ============================================================================
-- system_objects_database_tables
-- ============================================================================

CREATE TABLE [dbo].[system_objects_database_tables] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(128)     NOT NULL,
  [pub_schema]            NVARCHAR(64)      NOT NULL CONSTRAINT [DF_sodt_schema] DEFAULT N'dbo',
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodt_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodt_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_database_tables]             PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_system_objects_database_tables_schema_name] UNIQUE ([pub_schema], [pub_name])
);
GO

-- ============================================================================
-- system_objects_database_columns
-- ============================================================================

CREATE TABLE [dbo].[system_objects_database_columns] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sodc_guid] DEFAULT NEWID(),
  [ref_table_guid]        UNIQUEIDENTIFIER  NOT NULL,
  [ref_type_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(128)     NOT NULL,
  [pub_ordinal]           INT               NOT NULL,
  [pub_is_nullable]       BIT               NOT NULL CONSTRAINT [DF_sodc_nullable]  DEFAULT 0,
  [pub_is_primary_key]    BIT               NOT NULL CONSTRAINT [DF_sodc_pk]        DEFAULT 0,
  [pub_is_identity]       BIT               NOT NULL CONSTRAINT [DF_sodc_identity]  DEFAULT 0,
  [pub_default]           NVARCHAR(512)     NULL,
  [pub_max_length]        INT               NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodc_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodc_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_database_columns] PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sodc_table] FOREIGN KEY ([ref_table_guid]) REFERENCES [dbo].[system_objects_database_tables] ([key_guid]),
  CONSTRAINT [FK_sodc_type]  FOREIGN KEY ([ref_type_guid])  REFERENCES [dbo].[system_objects_types] ([key_guid])
);
GO

CREATE INDEX [IX_sodc_table_guid] ON [dbo].[system_objects_database_columns] ([ref_table_guid]);
GO

-- ============================================================================
-- system_objects_database_indexes
-- ============================================================================

CREATE TABLE [dbo].[system_objects_database_indexes] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sodi_guid] DEFAULT NEWID(),
  [ref_table_guid]        UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(256)     NOT NULL,
  [pub_columns]           NVARCHAR(1024)    NOT NULL,
  [pub_is_unique]         BIT               NOT NULL CONSTRAINT [DF_sodi_unique] DEFAULT 0,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodi_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodi_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_database_indexes] PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sodi_table] FOREIGN KEY ([ref_table_guid]) REFERENCES [dbo].[system_objects_database_tables] ([key_guid])
);
GO

-- ============================================================================
-- system_objects_database_constraints
-- ============================================================================

CREATE TABLE [dbo].[system_objects_database_constraints] (
  [key_guid]                      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sodcon_guid] DEFAULT NEWID(),
  [ref_table_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [ref_column_guid]               UNIQUEIDENTIFIER  NOT NULL,
  [ref_referenced_table_guid]     UNIQUEIDENTIFIER  NOT NULL,
  [ref_referenced_column_guid]    UNIQUEIDENTIFIER  NOT NULL,
  [priv_created_on]               DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodcon_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]              DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sodcon_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_database_constraints]  PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sodcon_table]      FOREIGN KEY ([ref_table_guid])              REFERENCES [dbo].[system_objects_database_tables] ([key_guid]),
  CONSTRAINT [FK_sodcon_column]     FOREIGN KEY ([ref_column_guid])             REFERENCES [dbo].[system_objects_database_columns] ([key_guid]),
  CONSTRAINT [FK_sodcon_ref_table]  FOREIGN KEY ([ref_referenced_table_guid])   REFERENCES [dbo].[system_objects_database_tables] ([key_guid]),
  CONSTRAINT [FK_sodcon_ref_column] FOREIGN KEY ([ref_referenced_column_guid])  REFERENCES [dbo].[system_objects_database_columns] ([key_guid])
);
GO

-- ============================================================================
-- SEED: Types — uuid5(NS, 'type:{name}')
-- ============================================================================

INSERT INTO [dbo].[system_objects_types] ([key_guid],[pub_name],[pub_mssql_type],[pub_postgresql_type],[pub_mysql_type],[pub_python_type],[pub_typescript_type],[pub_json_type],[pub_odbc_type_code],[pub_max_length],[pub_notes]) VALUES
(N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B',N'INT32',         N'int',                 N'integer',      N'int',                  N'int',  N'number', N'integer',4,   4,   N'Standard 32-bit signed integer.'),
(N'362EB7D6-8ECF-58FA-9416-D4822410DF9F',N'INT64',         N'bigint',              N'bigint',       N'bigint',               N'int',  N'number', N'integer',-5,  8,   N'64-bit signed integer.'),
(N'E0556F4C-ECA5-5475-B6C1-F60706632F06',N'INT64_IDENTITY',N'bigint identity(1,1)',N'bigserial',    N'bigint auto_increment',N'int',  N'number', N'integer',-5,  8,   N'Auto-incrementing 64-bit integer.'),
(N'4D2EB10B-363E-5AF4-826A-9294146244E4',N'UUID',          N'uniqueidentifier',    N'uuid',         N'char(36)',             N'str',  N'string', N'string', -11, 16,  N'128-bit UUID / GUID.'),
(N'12B2F03B-E315-50A5-B631-E6B1EB961A17',N'BOOL',          N'bit',                 N'boolean',      N'tinyint(1)',           N'bool', N'boolean',N'boolean',-7,  1,   N'Boolean flag.'),
(N'70F890D3-5AB5-5250-860E-4F7F9624190C',N'DATETIME_TZ',   N'datetimeoffset(7)',    N'timestamptz',  N'datetime(6)',          N'str',  N'string', N'string', -155,NULL,N'Timestamp with timezone offset.'),
(N'0093B404-1EEE-563D-9135-4B9E7EECA7A2',N'STRING',        N'nvarchar',            N'varchar',      N'varchar',              N'str',  N'string', N'string', -9,  NULL,N'Variable-length Unicode string.'),
(N'DCA18974-D648-5DFF-AEFB-122C081145AA',N'TEXT',           N'nvarchar(max)',        N'text',         N'longtext',             N'str',  N'string', N'string', -10, NULL,N'Unlimited-length Unicode text.'),
(N'6F99D39D-EE59-56D4-A966-B0707DF806D9',N'INT8',          N'tinyint',             N'smallint',     N'tinyint',              N'int',  N'number', N'integer',-6,  1,   N'8-bit unsigned integer (0-255).'),
(N'EA9D3720-732F-5D6B-8EB1-DD8ECC6F67F6',N'DATE',          N'date',                N'date',         N'date',                 N'str',  N'string', N'string', 91,  3,   N'Date without time component.'),
(N'A79190A1-FB3B-580C-8A24-445D590715BD',N'DECIMAL_19_5',  N'decimal(19,5)',        N'decimal(19,5)',N'decimal(19,5)',         N'float',N'number', N'number', 3,   NULL,N'Fixed-precision decimal (19,5).');
GO

-- ============================================================================
-- SEED: Tables — uuid5(NS, 'table:{name}')
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_tables] ([key_guid],[pub_name],[pub_schema]) VALUES
(N'73377644-3E86-5FE6-B982-0B224749C358',N'system_objects_types',               N'dbo'),
(N'78D4E217-6810-5A05-8999-ED57016229B6',N'system_objects_database_tables',     N'dbo'),
(N'4241CCF3-A1F8-5A80-86BD-82632E121495',N'system_objects_database_columns',    N'dbo'),
(N'F9CEA0AB-2528-563C-BCE0-0CE60A60882F',N'system_objects_database_indexes',    N'dbo'),
(N'E755A929-5735-5F9F-9FF6-9428B5FEB070',N'system_objects_database_constraints',N'dbo'),
(N'6E74766A-38EA-583C-9E08-4060FB5FDC4B',N'service_auth_providers',             N'dbo'),
(N'DCC79235-8429-5731-AF60-092AF3A2E4B0',N'system_users',                       N'dbo'),
(N'D847D5C3-0D47-5668-9745-E394E6712B39',N'system_user_auth',                   N'dbo');
GO

-- ============================================================================
-- SEED: Columns — uuid5(NS, 'column:{table}.{column}')
-- All column GUIDs are deterministic.
-- ============================================================================

-- Type GUIDs
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';

-- Table GUIDs
DECLARE @TBL_TYPES       UNIQUEIDENTIFIER = N'73377644-3E86-5FE6-B982-0B224749C358';
DECLARE @TBL_TABLES      UNIQUEIDENTIFIER = N'78D4E217-6810-5A05-8999-ED57016229B6';
DECLARE @TBL_COLUMNS     UNIQUEIDENTIFIER = N'4241CCF3-A1F8-5A80-86BD-82632E121495';
DECLARE @TBL_INDEXES     UNIQUEIDENTIFIER = N'F9CEA0AB-2528-563C-BCE0-0CE60A60882F';
DECLARE @TBL_CONSTRAINTS UNIQUEIDENTIFIER = N'E755A929-5735-5F9F-9FF6-9428B5FEB070';

-- system_objects_types
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'ACC8E8B1-F5E5-5D93-B814-B8FF571DE287',@TBL_TYPES,@T_UUID, N'key_guid',           1, 0,1,0,NULL,              NULL),
(N'8C4FCE6B-7564-545D-95C9-7048B5CAC5B1',@TBL_TYPES,@T_STR,  N'pub_name',           2, 0,0,0,NULL,              64),
(N'BF2D684C-1D12-5EDB-BD0B-2BE563970C77',@TBL_TYPES,@T_STR,  N'pub_mssql_type',     3, 0,0,0,NULL,              128),
(N'52EF0E93-EFF4-5891-974C-105D7FDAD405',@TBL_TYPES,@T_STR,  N'pub_postgresql_type', 4, 1,0,0,NULL,              128),
(N'29918E2A-8FA5-5DC6-B575-06ECBF2585C6',@TBL_TYPES,@T_STR,  N'pub_mysql_type',      5, 1,0,0,NULL,              128),
(N'14F26246-8380-558E-949C-5ED259D3DB14',@TBL_TYPES,@T_STR,  N'pub_python_type',     6, 0,0,0,NULL,              128),
(N'A5D15632-86CA-5BAE-A34B-B7FB39444021',@TBL_TYPES,@T_STR,  N'pub_typescript_type', 7, 0,0,0,NULL,              128),
(N'2F99A5A2-3C11-5D9F-8F32-05F4DD8EF833',@TBL_TYPES,@T_STR,  N'pub_json_type',       8, 0,0,0,NULL,              64),
(N'5643D14F-E188-5CA1-8452-F48055DF01EA',@TBL_TYPES,@T_INT32,N'pub_odbc_type_code',  9, 1,0,0,NULL,              NULL),
(N'D0ED648E-D927-5C74-B433-3EA8918771AB',@TBL_TYPES,@T_INT32,N'pub_max_length',      10,1,0,0,NULL,              NULL),
(N'A643372C-6F78-5525-B930-D07CCE7ED1FB',@TBL_TYPES,@T_STR,  N'pub_notes',           11,1,0,0,NULL,              512),
(N'CBD7A080-8160-5836-ACF7-2C418019AE5E',@TBL_TYPES,@T_DTZ,  N'priv_created_on',     12,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'9640A007-24D7-5C48-A71D-B30E498A217A',@TBL_TYPES,@T_DTZ,  N'priv_modified_on',    13,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_database_tables
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'01ED6065-9D06-569A-9138-557E549B3B13',@TBL_TABLES,@T_UUID,N'key_guid',        1,0,1,0,NULL,              NULL),
(N'C49C8302-F63F-5473-9412-5B508E583039',@TBL_TABLES,@T_STR, N'pub_name',        2,0,0,0,NULL,              128),
(N'78D8662D-4A49-5C0B-A5C2-187BA1B92231',@TBL_TABLES,@T_STR, N'pub_schema',      3,0,0,0,N'''dbo''',        64),
(N'A9AC10DA-541C-5BD0-A5C8-80A8AC945004',@TBL_TABLES,@T_DTZ, N'priv_created_on', 4,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'F28F618B-6000-5F95-8077-5875E4BCA588',@TBL_TABLES,@T_DTZ, N'priv_modified_on',5,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_database_columns (self-referential)
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'1D391E84-82D7-5877-8111-1CA9FB38FEAA',@TBL_COLUMNS,@T_UUID, N'key_guid',          1, 0,1,0,N'NEWID()',          NULL),
(N'1343D2A3-53EB-5AB8-A804-60FA99FDBDD2',@TBL_COLUMNS,@T_UUID, N'ref_table_guid',    2, 0,0,0,NULL,               NULL),
(N'8ACFAD7C-33BC-596D-96D6-670FD44E8764',@TBL_COLUMNS,@T_UUID, N'ref_type_guid',     3, 0,0,0,NULL,               NULL),
(N'661F67AB-C633-5606-950C-031FEA03E421',@TBL_COLUMNS,@T_STR,  N'pub_name',          4, 0,0,0,NULL,               128),
(N'F3AD9E2A-06CA-54DD-AB91-60286E4C8D9D',@TBL_COLUMNS,@T_INT32,N'pub_ordinal',       5, 0,0,0,NULL,               NULL),
(N'C85CB4AA-2563-58E8-BC88-3A6132DC9EBB',@TBL_COLUMNS,@T_BOOL, N'pub_is_nullable',   6, 0,0,0,N'0',              NULL),
(N'172BC960-1331-53ED-99D8-465F5C8F692C',@TBL_COLUMNS,@T_BOOL, N'pub_is_primary_key',7, 0,0,0,N'0',              NULL),
(N'938DF97C-BF91-5670-8153-14730F70841A',@TBL_COLUMNS,@T_BOOL, N'pub_is_identity',   8, 0,0,0,N'0',              NULL),
(N'3DE3EBCD-05A1-5F1D-867F-1449BF87E439',@TBL_COLUMNS,@T_STR,  N'pub_default',       9, 1,0,0,NULL,               512),
(N'EEC29CC3-6A82-5DC2-8373-3DA362488B8E',@TBL_COLUMNS,@T_INT32,N'pub_max_length',    10,1,0,0,NULL,               NULL),
(N'84C19E02-4E60-5E61-9FBD-CDFE0636AC49',@TBL_COLUMNS,@T_DTZ,  N'priv_created_on',   11,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'F8844E16-DDB8-5877-8697-A72F004B33A3',@TBL_COLUMNS,@T_DTZ,  N'priv_modified_on',  12,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_database_indexes
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'D20CA437-5147-5337-BB33-363FF9B8C9EE',@TBL_INDEXES,@T_UUID,N'key_guid',        1,0,1,0,N'NEWID()',          NULL),
(N'EA17370E-FC56-5BF2-8702-D9A25246011D',@TBL_INDEXES,@T_UUID,N'ref_table_guid',  2,0,0,0,NULL,               NULL),
(N'781E1ED2-FAAE-5DF7-9D82-643197717596',@TBL_INDEXES,@T_STR, N'pub_name',        3,0,0,0,NULL,               256),
(N'284C7457-278B-5AD9-84DE-F6250D0F5DA1',@TBL_INDEXES,@T_STR, N'pub_columns',     4,0,0,0,NULL,               1024),
(N'D2AB1631-F0F6-5B0A-83AF-F686E3BCAB15',@TBL_INDEXES,@T_BOOL,N'pub_is_unique',   5,0,0,0,N'0',              NULL),
(N'6C608316-6246-56F5-8900-041971702D38',@TBL_INDEXES,@T_DTZ, N'priv_created_on', 6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'A66EE486-EB24-501A-9685-81DD4B5F8A05',@TBL_INDEXES,@T_DTZ, N'priv_modified_on',7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_database_constraints
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'0A6F3395-7AD4-5839-A21C-C2708196FEA0',@TBL_CONSTRAINTS,@T_UUID,N'key_guid',                  1,0,1,0,N'NEWID()',          NULL),
(N'C0785C3C-AC3F-5DC1-BF46-20C12BAF65F0',@TBL_CONSTRAINTS,@T_UUID,N'ref_table_guid',            2,0,0,0,NULL,               NULL),
(N'0A7C09FA-6A5F-52F3-9FD1-8F3C6E29BC49',@TBL_CONSTRAINTS,@T_UUID,N'ref_column_guid',           3,0,0,0,NULL,               NULL),
(N'83BEB1A9-355B-5B32-A4D7-C4D52BE14DF6',@TBL_CONSTRAINTS,@T_UUID,N'ref_referenced_table_guid', 4,0,0,0,NULL,               NULL),
(N'5D2A0919-3C4D-5EEE-9D75-9410501EB3E7',@TBL_CONSTRAINTS,@T_UUID,N'ref_referenced_column_guid',5,0,0,0,NULL,               NULL),
(N'7D2D6407-F667-5C0A-AF1E-E3F9E330E401',@TBL_CONSTRAINTS,@T_DTZ, N'priv_created_on',           6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'205B575F-5067-56DC-81BD-00D7EE2311A2',@TBL_CONSTRAINTS,@T_DTZ, N'priv_modified_on',          7,0,0,0,N'SYSUTCDATETIME()',NULL);
GO

-- ============================================================================
-- SEED: Self-describing indexes
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_indexes] ([ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'73377644-3E86-5FE6-B982-0B224749C358',N'UQ_system_objects_types_name',                 N'pub_name',            1),
(N'78D4E217-6810-5A05-8999-ED57016229B6',N'UQ_system_objects_database_tables_schema_name',N'pub_schema,pub_name', 1),
(N'4241CCF3-A1F8-5A80-86BD-82632E121495',N'IX_sodc_table_guid',                           N'ref_table_guid',      0);
GO

-- ============================================================================
-- SEED: Self-describing FK constraints
-- All four columns are GUID references to tables and columns tables.
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_constraints] ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
-- columns.ref_table_guid → tables.key_guid
(N'4241CCF3-A1F8-5A80-86BD-82632E121495', N'1343D2A3-53EB-5AB8-A804-60FA99FDBDD2', N'78D4E217-6810-5A05-8999-ED57016229B6', N'01ED6065-9D06-569A-9138-557E549B3B13'),
-- columns.ref_type_guid → types.key_guid
(N'4241CCF3-A1F8-5A80-86BD-82632E121495', N'8ACFAD7C-33BC-596D-96D6-670FD44E8764', N'73377644-3E86-5FE6-B982-0B224749C358', N'ACC8E8B1-F5E5-5D93-B814-B8FF571DE287'),
-- indexes.ref_table_guid → tables.key_guid
(N'F9CEA0AB-2528-563C-BCE0-0CE60A60882F', N'EA17370E-FC56-5BF2-8702-D9A25246011D', N'78D4E217-6810-5A05-8999-ED57016229B6', N'01ED6065-9D06-569A-9138-557E549B3B13'),
-- constraints.ref_table_guid → tables.key_guid
(N'E755A929-5735-5F9F-9FF6-9428B5FEB070', N'C0785C3C-AC3F-5DC1-BF46-20C12BAF65F0', N'78D4E217-6810-5A05-8999-ED57016229B6', N'01ED6065-9D06-569A-9138-557E549B3B13'),
-- constraints.ref_column_guid → columns.key_guid
(N'E755A929-5735-5F9F-9FF6-9428B5FEB070', N'0A7C09FA-6A5F-52F3-9FD1-8F3C6E29BC49', N'4241CCF3-A1F8-5A80-86BD-82632E121495', N'1D391E84-82D7-5877-8111-1CA9FB38FEAA'),
-- constraints.ref_referenced_table_guid → tables.key_guid
(N'E755A929-5735-5F9F-9FF6-9428B5FEB070', N'83BEB1A9-355B-5B32-A4D7-C4D52BE14DF6', N'78D4E217-6810-5A05-8999-ED57016229B6', N'01ED6065-9D06-569A-9138-557E549B3B13'),
-- constraints.ref_referenced_column_guid → columns.key_guid
(N'E755A929-5735-5F9F-9FF6-9428B5FEB070', N'5D2A0919-3C4D-5EEE-9D75-9410501EB3E7', N'4241CCF3-A1F8-5A80-86BD-82632E121495', N'1D391E84-82D7-5877-8111-1CA9FB38FEAA');
GO

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'system_objects_types' AS [table],               COUNT(*) AS [rows] FROM [dbo].[system_objects_types];
SELECT 'system_objects_database_tables' AS [table],     COUNT(*) AS [rows] FROM [dbo].[system_objects_database_tables];
SELECT 'system_objects_database_columns' AS [table],    COUNT(*) AS [rows] FROM [dbo].[system_objects_database_columns];
SELECT 'system_objects_database_indexes' AS [table],    COUNT(*) AS [rows] FROM [dbo].[system_objects_database_indexes];
SELECT 'system_objects_database_constraints' AS [table],COUNT(*) AS [rows] FROM [dbo].[system_objects_database_constraints];

-- Self-description: columns table describes itself
SELECT c.[pub_name] AS [column], t.[pub_name] AS [type], c.[pub_ordinal] AS [ord],
       c.[pub_is_primary_key] AS [pk], c.[pub_is_nullable] AS [null], c.[pub_max_length] AS [len]
FROM [dbo].[system_objects_database_columns] c
JOIN [dbo].[system_objects_types] t ON t.[key_guid] = c.[ref_type_guid]
WHERE c.[ref_table_guid] = N'4241CCF3-A1F8-5A80-86BD-82632E121495'
ORDER BY c.[pub_ordinal];

-- FK constraint proof: show all self-described constraints with resolved names
SELECT
  t1.[pub_name] AS [from_table],
  c1.[pub_name] AS [from_column],
  t2.[pub_name] AS [to_table],
  c2.[pub_name] AS [to_column]
FROM [dbo].[system_objects_database_constraints] con
JOIN [dbo].[system_objects_database_tables]  t1 ON t1.[key_guid] = con.[ref_table_guid]
JOIN [dbo].[system_objects_database_columns] c1 ON c1.[key_guid] = con.[ref_column_guid]
JOIN [dbo].[system_objects_database_tables]  t2 ON t2.[key_guid] = con.[ref_referenced_table_guid]
JOIN [dbo].[system_objects_database_columns] c2 ON c2.[key_guid] = con.[ref_referenced_column_guid];