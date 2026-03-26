SET NOCOUNT ON;
GO

IF OBJECT_ID('dbo.service_pages', 'U') IS NOT NULL
BEGIN
  DECLARE @service_pages_tables_recid BIGINT = (
    SELECT recid
    FROM dbo.system_schema_tables
    WHERE element_schema = 'dbo' AND element_name = 'service_pages'
  );

  IF @service_pages_tables_recid IS NOT NULL
  BEGIN
    DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @service_pages_tables_recid;
    DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @service_pages_tables_recid;
    DELETE FROM dbo.system_schema_columns WHERE tables_recid = @service_pages_tables_recid;
    DELETE FROM dbo.system_schema_tables WHERE recid = @service_pages_tables_recid;
  END;

  DROP TABLE dbo.service_pages;
END;
GO

IF OBJECT_ID('dbo.content_pages', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_pages (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_content_pages_guid DEFAULT NEWID(),
    element_slug NVARCHAR(256) NOT NULL,
    element_title NVARCHAR(512) NOT NULL,
    element_page_type NVARCHAR(64) NOT NULL CONSTRAINT DF_content_pages_page_type DEFAULT 'article',
    element_category NVARCHAR(128) NULL,
    element_roles BIGINT NOT NULL CONSTRAINT DF_content_pages_roles DEFAULT 0,
    element_is_active BIT NOT NULL CONSTRAINT DF_content_pages_is_active DEFAULT 1,
    element_is_pinned BIT NOT NULL CONSTRAINT DF_content_pages_is_pinned DEFAULT 0,
    element_sequence INT NOT NULL CONSTRAINT DF_content_pages_sequence DEFAULT 0,
    element_created_by UNIQUEIDENTIFIER NOT NULL,
    element_modified_by UNIQUEIDENTIFIER NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_pages_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_pages_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_pages PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_pages_guid UNIQUE (element_guid),
    CONSTRAINT UQ_content_pages_slug UNIQUE (element_slug),
    CONSTRAINT FK_content_pages_created_by FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid),
    CONSTRAINT FK_content_pages_modified_by FOREIGN KEY (element_modified_by) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_pages') AND name = 'IX_content_pages_page_type')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_pages_page_type
  ON dbo.content_pages (element_page_type, element_is_active);
END;
GO

IF OBJECT_ID('dbo.content_page_versions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_page_versions (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    pages_recid BIGINT NOT NULL,
    element_version INT NOT NULL CONSTRAINT DF_content_page_versions_version DEFAULT 1,
    element_content NVARCHAR(MAX) NOT NULL,
    element_summary NVARCHAR(512) NULL,
    element_created_by UNIQUEIDENTIFIER NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_page_versions_created_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_page_versions PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_page_versions_page_ver UNIQUE (pages_recid, element_version),
    CONSTRAINT FK_content_page_versions_pages FOREIGN KEY (pages_recid) REFERENCES dbo.content_pages (recid),
    CONSTRAINT FK_content_page_versions_created_by FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_page_versions') AND name = 'IX_content_page_versions_pages')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_page_versions_pages
  ON dbo.content_page_versions (pages_recid);
END;
GO

IF OBJECT_ID('dbo.content_posts', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_posts (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_content_posts_guid DEFAULT NEWID(),
    element_title NVARCHAR(256) NULL,
    element_content NVARCHAR(MAX) NOT NULL,
    element_media_url NVARCHAR(1024) NULL,
    element_media_type NVARCHAR(64) NULL,
    element_link_url NVARCHAR(1024) NULL,
    element_link_title NVARCHAR(256) NULL,
    element_link_preview NVARCHAR(512) NULL,
    element_author_guid UNIQUEIDENTIFIER NOT NULL,
    element_is_pinned BIT NOT NULL CONSTRAINT DF_content_posts_is_pinned DEFAULT 0,
    element_is_active BIT NOT NULL CONSTRAINT DF_content_posts_is_active DEFAULT 1,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_posts_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_posts_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_posts PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_posts_guid UNIQUE (element_guid),
    CONSTRAINT FK_content_posts_author FOREIGN KEY (element_author_guid) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_posts') AND name = 'IX_content_posts_created')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_posts_created
  ON dbo.content_posts (element_created_on DESC);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_posts') AND name = 'IX_content_posts_author')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_posts_author
  ON dbo.content_posts (element_author_guid);
END;
GO

IF OBJECT_ID('dbo.content_post_comments', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_post_comments (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    posts_recid BIGINT NOT NULL,
    parent_recid BIGINT NULL,
    element_content NVARCHAR(MAX) NOT NULL,
    element_author_guid UNIQUEIDENTIFIER NOT NULL,
    element_is_active BIT NOT NULL CONSTRAINT DF_content_post_comments_is_active DEFAULT 1,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_post_comments_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_post_comments_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_post_comments PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_content_post_comments_post FOREIGN KEY (posts_recid) REFERENCES dbo.content_posts (recid),
    CONSTRAINT FK_content_post_comments_parent FOREIGN KEY (parent_recid) REFERENCES dbo.content_post_comments (recid),
    CONSTRAINT FK_content_post_comments_author FOREIGN KEY (element_author_guid) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_post_comments') AND name = 'IX_content_post_comments_post')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_post_comments_post
  ON dbo.content_post_comments (posts_recid);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_post_comments') AND name = 'IX_content_post_comments_parent')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_post_comments_parent
  ON dbo.content_post_comments (parent_recid)
  WHERE parent_recid IS NOT NULL;
END;
GO

IF OBJECT_ID('dbo.content_post_reactions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_post_reactions (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    posts_recid BIGINT NOT NULL,
    comments_recid BIGINT NULL,
    element_author_guid UNIQUEIDENTIFIER NOT NULL,
    element_reaction_type NVARCHAR(32) NOT NULL CONSTRAINT DF_content_post_reactions_reaction_type DEFAULT 'like',
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_post_reactions_created_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_post_reactions PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_post_reactions_unique UNIQUE (posts_recid, comments_recid, element_author_guid, element_reaction_type),
    CONSTRAINT FK_content_post_reactions_post FOREIGN KEY (posts_recid) REFERENCES dbo.content_posts (recid),
    CONSTRAINT FK_content_post_reactions_comment FOREIGN KEY (comments_recid) REFERENCES dbo.content_post_comments (recid),
    CONSTRAINT FK_content_post_reactions_author FOREIGN KEY (element_author_guid) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_post_reactions') AND name = 'IX_content_post_reactions_post')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_post_reactions_post
  ON dbo.content_post_reactions (posts_recid);
END;
GO

IF OBJECT_ID('dbo.content_wiki', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_wiki (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_content_wiki_guid DEFAULT NEWID(),
    element_slug NVARCHAR(512) NOT NULL,
    element_title NVARCHAR(512) NOT NULL,
    element_parent_slug NVARCHAR(512) NULL,
    element_route_context NVARCHAR(256) NULL,
    element_roles BIGINT NOT NULL CONSTRAINT DF_content_wiki_roles DEFAULT 0,
    element_is_active BIT NOT NULL CONSTRAINT DF_content_wiki_is_active DEFAULT 1,
    element_sequence INT NOT NULL CONSTRAINT DF_content_wiki_sequence DEFAULT 0,
    element_created_by UNIQUEIDENTIFIER NOT NULL,
    element_modified_by UNIQUEIDENTIFIER NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_wiki_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_wiki_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_wiki PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_wiki_guid UNIQUE (element_guid),
    CONSTRAINT UQ_content_wiki_slug UNIQUE (element_slug),
    CONSTRAINT FK_content_wiki_created_by FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid),
    CONSTRAINT FK_content_wiki_modified_by FOREIGN KEY (element_modified_by) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_wiki') AND name = 'IX_content_wiki_parent')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_wiki_parent
  ON dbo.content_wiki (element_parent_slug);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_wiki') AND name = 'IX_content_wiki_route_context')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_wiki_route_context
  ON dbo.content_wiki (element_route_context)
  WHERE element_route_context IS NOT NULL;
END;
GO

IF OBJECT_ID('dbo.content_wiki_versions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.content_wiki_versions (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    wiki_recid BIGINT NOT NULL,
    element_version INT NOT NULL CONSTRAINT DF_content_wiki_versions_version DEFAULT 1,
    element_content NVARCHAR(MAX) NOT NULL,
    element_edit_summary NVARCHAR(512) NULL,
    element_created_by UNIQUEIDENTIFIER NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_content_wiki_versions_created_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_content_wiki_versions PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_content_wiki_versions_wiki_ver UNIQUE (wiki_recid, element_version),
    CONSTRAINT FK_content_wiki_versions_wiki FOREIGN KEY (wiki_recid) REFERENCES dbo.content_wiki (recid),
    CONSTRAINT FK_content_wiki_versions_created_by FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.content_wiki_versions') AND name = 'IX_content_wiki_versions_wiki')
BEGIN
  CREATE NONCLUSTERED INDEX IX_content_wiki_versions_wiki
  ON dbo.content_wiki_versions (wiki_recid);
END;
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_pages', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_pages' AND element_schema = 'dbo');
GO
DECLARE @t_content_pages BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_pages' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 8, 'element_slug', 3, 0, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 8, 'element_title', 4, 0, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_title');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 8, 'element_page_type', 5, 0, '''article''', 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_page_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 8, 'element_category', 6, 1, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_category');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 2, 'element_roles', 7, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_roles');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 5, 'element_is_active', 8, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 5, 'element_is_pinned', 9, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_is_pinned');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 1, 'element_sequence', 10, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_sequence');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 4, 'element_created_by', 11, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 4, 'element_modified_by', 12, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_modified_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 7, 'element_created_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_pages, 7, 'element_modified_on', 14, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_pages AND element_name = 'element_modified_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_pages', 'recid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_pages' AND t.element_schema = 'dbo'
AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_pages');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_pages_guid', 'element_guid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_pages' AND t.element_schema = 'dbo'
AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_pages_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_pages_slug', 'element_slug', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_pages' AND t.element_schema = 'dbo'
AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_pages_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_pages_page_type', 'element_page_type,element_is_active', 0
FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_pages' AND t.element_schema = 'dbo'
AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_pages_page_type');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_created_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s
CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_pages' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_created_by');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_modified_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s
CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_pages' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_modified_by');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_page_versions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_page_versions' AND element_schema = 'dbo');
GO
DECLARE @t_content_page_versions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_page_versions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 2, 'pages_recid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'pages_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 1, 'element_version', 3, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'element_version');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 9, 'element_content', 4, 0, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'element_content');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 8, 'element_summary', 5, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'element_summary');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 4, 'element_created_by', 6, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_page_versions, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_page_versions AND element_name = 'element_created_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_page_versions', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_page_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_page_versions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_page_versions_page_ver', 'pages_recid,element_version', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_page_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_page_versions_page_ver');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_page_versions_pages', 'pages_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_page_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_page_versions_pages');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'pages_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_page_versions' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_pages' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'pages_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_created_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_page_versions' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_created_by');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_posts', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_posts' AND element_schema = 'dbo');
GO
DECLARE @t_content_posts BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_posts' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_title', 3, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_title');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 9, 'element_content', 4, 0, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_content');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_media_url', 5, 1, NULL, 1024, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_media_url');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_media_type', 6, 1, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_media_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_link_url', 7, 1, NULL, 1024, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_link_url');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_link_title', 8, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_link_title');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 8, 'element_link_preview', 9, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_link_preview');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 4, 'element_author_guid', 10, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_author_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 5, 'element_is_pinned', 11, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_is_pinned');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 5, 'element_is_active', 12, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 7, 'element_created_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_posts, 7, 'element_modified_on', 14, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_posts AND element_name = 'element_modified_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_posts', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_posts' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_posts');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_posts_guid', 'element_guid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_posts' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_posts_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_posts_created', 'element_created_on', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_posts' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_posts_created');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_posts_author', 'element_author_guid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_posts' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_posts_author');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_author_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_posts' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_author_guid');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_post_comments', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_post_comments' AND element_schema = 'dbo');
GO
DECLARE @t_content_post_comments BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_post_comments' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 2, 'posts_recid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'posts_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 2, 'parent_recid', 3, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'parent_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 9, 'element_content', 4, 0, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'element_content');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 4, 'element_author_guid', 5, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'element_author_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 5, 'element_is_active', 6, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_comments, 7, 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_comments AND element_name = 'element_modified_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_post_comments', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_comments' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_post_comments');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_post_comments_post', 'posts_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_comments' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_post_comments_post');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_post_comments_parent', 'parent_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_comments' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_post_comments_parent');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'posts_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_comments' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_posts' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'posts_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'parent_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_comments' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_post_comments' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'parent_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_author_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_comments' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_author_guid');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_post_reactions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_post_reactions' AND element_schema = 'dbo');
GO
DECLARE @t_content_post_reactions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_post_reactions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 2, 'posts_recid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'posts_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 2, 'comments_recid', 3, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'comments_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 4, 'element_author_guid', 4, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'element_author_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 8, 'element_reaction_type', 5, 0, '''like''', 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'element_reaction_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_post_reactions, 7, 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_post_reactions AND element_name = 'element_created_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_post_reactions', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_reactions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_post_reactions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_post_reactions_post', 'posts_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_reactions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_post_reactions_post');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_post_reactions_unique', 'posts_recid,comments_recid,element_author_guid,element_reaction_type', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_post_reactions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_post_reactions_unique');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'posts_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_reactions' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_posts' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'posts_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'comments_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_reactions' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_post_comments' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'comments_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_author_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_post_reactions' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_author_guid');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_wiki', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_wiki' AND element_schema = 'dbo');
GO
DECLARE @t_content_wiki BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_wiki' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 8, 'element_slug', 3, 0, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 8, 'element_title', 4, 0, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_title');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 8, 'element_parent_slug', 5, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_parent_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 8, 'element_route_context', 6, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_route_context');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 2, 'element_roles', 7, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_roles');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 5, 'element_is_active', 8, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 1, 'element_sequence', 9, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_sequence');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 4, 'element_created_by', 10, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 4, 'element_modified_by', 11, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_modified_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki AND element_name = 'element_modified_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_wiki', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_wiki');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_wiki_guid', 'element_guid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_wiki_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_wiki_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_wiki_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_wiki_parent', 'element_parent_slug', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_wiki_parent');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_wiki_route_context', 'element_route_context', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_wiki_route_context');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_created_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_wiki' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_created_by');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_modified_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_wiki' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_modified_by');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'content_wiki_versions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'content_wiki_versions' AND element_schema = 'dbo');
GO
DECLARE @t_content_wiki_versions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'content_wiki_versions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 2, 'wiki_recid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'wiki_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 1, 'element_version', 3, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'element_version');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 9, 'element_content', 4, 0, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'element_content');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 8, 'element_edit_summary', 5, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'element_edit_summary');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 4, 'element_created_by', 6, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_content_wiki_versions, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_content_wiki_versions AND element_name = 'element_created_on');
GO
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_content_wiki_versions', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_content_wiki_versions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_content_wiki_versions_wiki_ver', 'wiki_recid,element_version', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_content_wiki_versions_wiki_ver');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_content_wiki_versions_wiki', 'wiki_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'content_wiki_versions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_content_wiki_versions_wiki');
GO
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'wiki_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_wiki_versions' AND s.element_schema = 'dbo'
  AND r.element_name = 'content_wiki' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'wiki_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_created_by', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'content_wiki_versions' AND s.element_schema = 'dbo'
  AND r.element_name = 'account_users' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_created_by');
GO
