-- ==========================================================================
-- TheOracleRPC v0.11.9.0 Frontend Pages Registry
-- Date: 2026-04-02
-- Purpose:
--   1. Create frontend_pages table for route-to-component mapping
--   2. Register frontend_pages in system schema reflection tables
--   3. Seed canonical frontend page route data
-- ============================================================================

IF OBJECT_ID(N'dbo.frontend_pages', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[frontend_pages] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_path] NVARCHAR(512) NOT NULL,
    [element_component] NVARCHAR(256) NOT NULL,
    [element_sequence] INT NOT NULL CONSTRAINT [DF_frontend_pages_element_sequence] DEFAULT ((0)),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_frontend_pages_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_frontend_pages_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_frontend_pages] PRIMARY KEY CLUSTERED ([recid] ASC)
  );
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE name = N'UQ_frontend_pages_element_path'
    AND object_id = OBJECT_ID(N'dbo.frontend_pages')
)
BEGIN
  CREATE UNIQUE NONCLUSTERED INDEX [UQ_frontend_pages_element_path]
    ON [dbo].[frontend_pages] ([element_path] ASC);
END;
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'frontend_pages', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM dbo.system_schema_tables
  WHERE element_name = 'frontend_pages' AND element_schema = 'dbo'
);
GO

DECLARE @t_frontend_pages BIGINT = (
  SELECT recid
  FROM dbo.system_schema_tables
  WHERE element_name = 'frontend_pages' AND element_schema = 'dbo'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'recid'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 8, 'element_path', 2, 0, NULL, 512, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'element_path'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 8, 'element_component', 3, 0, NULL, 256, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'element_component'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 1, 'element_sequence', 4, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'element_sequence'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 7, 'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'element_created_on'
);

INSERT INTO dbo.system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_frontend_pages, 7, 'element_modified_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_frontend_pages AND element_name = 'element_modified_on'
);
GO

DECLARE @t_frontend_pages BIGINT = (
  SELECT recid
  FROM dbo.system_schema_tables
  WHERE element_name = 'frontend_pages' AND element_schema = 'dbo'
);

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_frontend_pages, 'PK_frontend_pages', 'recid', 1
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_indexes WHERE tables_recid = @t_frontend_pages AND element_name = 'PK_frontend_pages'
);

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_frontend_pages, 'UQ_frontend_pages_element_path', 'element_path', 1
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_indexes WHERE tables_recid = @t_frontend_pages AND element_name = 'UQ_frontend_pages_element_path'
);
GO

INSERT INTO dbo.frontend_pages (element_path, element_component, element_sequence)
SELECT src.element_path, src.element_component, src.element_sequence
FROM (VALUES
  ('/', 'Home', 10),
  ('/gallery', 'Gallery', 20),
  ('/loginpage', 'LoginPage', 30),
  ('/userpage', 'UserPage', 40),
  ('/products', 'ProductsPage', 50),
  ('/file-manager', 'FileManager', 60),
  ('/account-users', 'AccountUsersPage', 100),
  ('/account-users/:guid', 'AccountUserPanel', 110),
  ('/account-roles', 'AccountRolesPage', 120),
  ('/finance-acct', 'finance/FinanceAccountantPage', 200),
  ('/finance-appr', 'finance/FinanceManagerPage', 210),
  ('/finance-admin', 'finance/FinanceAdminPage', 220),
  ('/discord-personas', 'DiscordPersonasPage', 300),
  ('/discord-guilds', 'DiscordGuildsPage', 310),
  ('/system-config', 'system/SystemConfigPage', 400),
  ('/system-models', 'system/SystemModelsPage', 410),
  ('/system-conversations', 'system/SystemConversationsPage', 420),
  ('/system-workflows', 'system/SystemWorkflowsPage', 430),
  ('/service-routes', 'service/ServiceRoutesPage', 500),
  ('/service-pages', 'service/ServicePagesPage', 510),
  ('/service-roles', 'service/ServiceRolesPage', 520),
  ('/service-renewals', 'service/ServiceRenewalsPage', 530),
  ('/service-visualization', 'service/ServiceVisualizationPage', 540),
  ('/service-rpcdispatch', 'service/ServiceRpcDispatchPage', 550),
  ('/service-rpcdispatch-tree', 'service/ServiceRpcDispatchTreePage', 560),
  ('/profile/:guid', 'PublicProfile', 600),
  ('/pages/:slug', 'ContentPage', 700),
  ('/wiki/*', 'WikiPage', 800)
) AS src(element_path, element_component, element_sequence)
WHERE NOT EXISTS (
  SELECT 1
  FROM dbo.frontend_pages fp
  WHERE fp.element_path = src.element_path
);
GO
