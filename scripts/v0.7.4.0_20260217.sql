IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_edt_mappings' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE dbo.system_edt_mappings (
    recid bigint NOT NULL,
    element_name nvarchar(64) NOT NULL,
    element_mssql_type nvarchar(128) NOT NULL,
    element_postgresql_type nvarchar(128) NOT NULL,
    element_mysql_type nvarchar(128) NOT NULL,
    element_python_type nvarchar(64) NOT NULL,
    element_odbc_type_code int NOT NULL,
    element_max_length int NULL,
    element_notes nvarchar(2048) NULL,
    element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    PRIMARY KEY (recid)
  );
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE name = 'UQ_system_edt_mappings_name'
    AND object_id = OBJECT_ID('dbo.system_edt_mappings')
)
BEGIN
  CREATE UNIQUE INDEX UQ_system_edt_mappings_name ON dbo.system_edt_mappings (element_name);
END;

MERGE dbo.system_edt_mappings AS target
USING (
  VALUES
    (1, 'INT32', 'int', 'integer', 'int', 'int', 4, 4, 'Standard 32-bit signed integer.'),
    (2, 'INT64', 'bigint', 'bigint', 'bigint', 'int', -5, 8, 'Standard 64-bit signed integer.'),
    (3, 'INT64_IDENTITY', 'bigint identity(1,1)', 'bigserial', 'bigint auto_increment', 'int', -5, 8, 'Auto-numbering key: MSSQL IDENTITY, PostgreSQL BIGSERIAL, MySQL AUTO_INCREMENT.'),
    (4, 'UUID', 'uniqueidentifier', 'uuid', 'char(36)', 'UUID', -11, 36, 'Prefer native UUID in MSSQL/PostgreSQL; MySQL commonly stores canonical text UUID unless BINARY(16) strategy is enabled.'),
    (5, 'BOOL', 'bit', 'boolean', 'boolean', 'bool', -7, 1, 'MSSQL BIT stores 0/1; PostgreSQL and MySQL BOOLEAN are logical aliases.'),
    (6, 'DATETIME', 'datetime2(7)', 'timestamp', 'datetime(6)', 'datetime', 93, NULL, 'Timezone-naive timestamp. MySQL DATETIME(6) stores no timezone metadata.'),
    (7, 'DATETIME_TZ', 'datetimeoffset(7)', 'timestamptz', 'timestamp', 'datetime', -150, NULL, 'Timezone-aware moment. MSSQL datetimeoffset may surface as ODBC type -150 in metadata and requires explicit handling. MySQL TIMESTAMP normalizes to session/server timezone and has narrower range than MSSQL/PostgreSQL.'),
    (8, 'STRING', 'nvarchar', 'varchar', 'varchar', 'str', -9, NULL, 'Bounded Unicode string. Use element_max_length for concrete column limits.'),
    (9, 'TEXT', 'nvarchar(max)', 'text', 'longtext', 'str', -10, NULL, 'Large/unbounded text payload. Keep collation and indexing behavior provider-specific.'),
    (10, 'STRING_ASCII', 'varchar', 'varchar', 'varchar', 'str', 12, NULL, 'Non-Unicode/ANSI text in MSSQL; collation and Unicode behavior differ from NVARCHAR-backed EDTs.')
) AS source (recid, element_name, element_mssql_type, element_postgresql_type, element_mysql_type, element_python_type, element_odbc_type_code, element_max_length, element_notes)
ON target.element_name = source.element_name
WHEN MATCHED THEN
  UPDATE SET
    recid = source.recid,
    element_mssql_type = source.element_mssql_type,
    element_postgresql_type = source.element_postgresql_type,
    element_mysql_type = source.element_mysql_type,
    element_python_type = source.element_python_type,
    element_odbc_type_code = source.element_odbc_type_code,
    element_max_length = source.element_max_length,
    element_notes = source.element_notes,
    element_modified_on = sysutcdatetime()
WHEN NOT MATCHED BY TARGET THEN
  INSERT (recid, element_name, element_mssql_type, element_postgresql_type, element_mysql_type, element_python_type, element_odbc_type_code, element_max_length, element_notes)
  VALUES (source.recid, source.element_name, source.element_mssql_type, source.element_postgresql_type, source.element_mysql_type, source.element_python_type, source.element_odbc_type_code, source.element_max_length, source.element_notes);
