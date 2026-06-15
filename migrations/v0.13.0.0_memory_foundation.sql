-- ============================================================================
-- elideus-group v0.13.0.0 — Agent Memory Bank Foundation
-- Date: 2026-06-14
-- Purpose:
--   Create the persistent memory-bank schema used by the MCP memory_* tools
--   so an agent (Claude Code) can store and retrieve working context
--   (decisions, invariants, specs, session summaries, snippets) across
--   sessions.  Two tables plus their reflection registrations.
--
-- Tables created:
--   agent_memory_threads  — optional grouping of related entries
--   agent_memory_entries  — the individual memory records (markdown bodies)
--
-- NOTE on timestamp type: the task brief sketched these columns as
--   DATETIME2(7).  This migration uses DATETIMEOFFSET(7) DEFAULT
--   SYSUTCDATETIME() instead, to match the repo-wide convention for priv_*
--   audit columns (every system_*/service_* table uses DATETIMEOFFSET(7)) and
--   because the reflection type registry (system_objects_types) only models
--   DATETIME_TZ / datetimeoffset(7) — there is no DATETIME2 EDT to register
--   against.  This keeps oracle_describe_table accurate.
--
-- Search: v1 uses LIKE-based matching over pub_title / pub_body / pub_tags
--   (see the memory.entries.search query in v0.13.1.0_memory_seed.sql).
--   Upgrade path: add a FULLTEXT CATALOG + INDEX over (pub_title, pub_body,
--   pub_tags) for CONTAINS/FREETEXT ranking, and later a pub_embedding
--   VARBINARY/vector column for local-embedding semantic search.  Neither is
--   built yet — LIKE is intentionally the v1 implementation.
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Column naming:   key_ / pub_ / priv_ / ref_
-- PK strategy:     UNIQUEIDENTIFIER, DEFAULT NEWID() for runtime rows;
--                  reflection registration rows use deterministic UUID5.
-- This migration is additive and idempotent (safe to re-run).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- PHASE 1: Tables
-- ============================================================================

IF OBJECT_ID(N'[dbo].[agent_memory_threads]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_threads] (
    [key_guid]              UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_amt_key_guid]      DEFAULT NEWID(),
    [pub_project]           NVARCHAR(128)     NOT NULL,
    [pub_title]             NVARCHAR(256)     NOT NULL,
    [pub_summary]           NVARCHAR(MAX)     NULL,
    [pub_is_active]         BIT               NOT NULL  CONSTRAINT [DF_amt_is_active]     DEFAULT 1,
    [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_amt_created_on]    DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_amt_modified_on]   DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_threads] PRIMARY KEY CLUSTERED ([key_guid])
  );
END
GO

IF OBJECT_ID(N'[dbo].[agent_memory_entries]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_entries] (
    [key_guid]              UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_ame_key_guid]      DEFAULT NEWID(),
    [ref_thread_guid]       UNIQUEIDENTIFIER  NULL,
    [pub_project]           NVARCHAR(128)     NOT NULL,   -- e.g. 'flicker', 'oracle-unity', 'general'
    [pub_kind]              NVARCHAR(32)      NOT NULL,   -- decision|invariant|spec|note|session_summary|snippet
    [pub_title]             NVARCHAR(256)     NOT NULL,
    [pub_body]              NVARCHAR(MAX)     NOT NULL,   -- markdown
    [pub_tags]              NVARCHAR(512)     NULL,       -- space-delimited tags
    [pub_source]            NVARCHAR(128)     NULL,       -- e.g. 'claude-code' + session id
    [pub_is_active]         BIT               NOT NULL  CONSTRAINT [DF_ame_is_active]     DEFAULT 1,
    [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ame_created_on]    DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ame_modified_on]   DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_entries]    PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_agent_memory_entries_thread] FOREIGN KEY ([ref_thread_guid])
      REFERENCES [dbo].[agent_memory_threads] ([key_guid])
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_entries_project'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  CREATE INDEX [IX_agent_memory_entries_project] ON [dbo].[agent_memory_entries] ([pub_project], [pub_is_active]);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_entries_kind'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  CREATE INDEX [IX_agent_memory_entries_kind] ON [dbo].[agent_memory_entries] ([pub_kind]);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_entries_thread'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  CREATE INDEX [IX_agent_memory_entries_thread] ON [dbo].[agent_memory_entries] ([ref_thread_guid]);
GO


-- ============================================================================
-- PHASE 2: Reflection registration (so the oracle_* tools can see the tables)
--   Reads come from system_objects_database_tables / _columns / _indexes /
--   _constraints, joined to system_objects_types for the mssql type name.
--   Re-runnable: child rows deleted (FK-safe order) then re-inserted.
-- ============================================================================

-- Reflection type GUIDs (system_objects_types)
DECLARE @T_UUID UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4'; -- uniqueidentifier
DECLARE @T_STR  UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2'; -- nvarchar
DECLARE @T_TEXT UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA'; -- nvarchar(max)
DECLARE @T_BOOL UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17'; -- bit
DECLARE @T_DTZ  UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C'; -- datetimeoffset(7)

-- Table GUIDs (UUID5: 'table:<name>')
DECLARE @TBL_THREADS UNIQUEIDENTIFIER = N'0FF5BCFE-65CF-5414-8CDB-1CA7DA4E570F'; -- agent_memory_threads
DECLARE @TBL_ENTRIES UNIQUEIDENTIFIER = N'07B0D4B9-4D3B-569E-926D-551035A6357B'; -- agent_memory_entries

-- Column GUIDs we cross-reference for the FK constraint
DECLARE @COL_THREADS_PK    UNIQUEIDENTIFIER = N'7B8D5C47-AA6E-5EF8-9041-A13CF5A39DDF'; -- agent_memory_threads.key_guid
DECLARE @COL_ENTRIES_THREAD UNIQUEIDENTIFIER = N'EB1C1A9B-804A-52D7-8088-335DF7B0253A'; -- agent_memory_entries.ref_thread_guid

-- Idempotent cleanup (FK-safe order: constraints -> indexes -> columns -> tables)
DELETE FROM [dbo].[system_objects_database_constraints] WHERE [ref_table_guid] IN (@TBL_THREADS, @TBL_ENTRIES);
DELETE FROM [dbo].[system_objects_database_indexes]     WHERE [ref_table_guid] IN (@TBL_THREADS, @TBL_ENTRIES);
DELETE FROM [dbo].[system_objects_database_columns]     WHERE [ref_table_guid] IN (@TBL_THREADS, @TBL_ENTRIES);
DELETE FROM [dbo].[system_objects_database_tables]      WHERE [key_guid]       IN (@TBL_THREADS, @TBL_ENTRIES);

-- 2a: tables
INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(@TBL_THREADS, N'agent_memory_threads', N'dbo'),
(@TBL_ENTRIES, N'agent_memory_entries', N'dbo');

-- 2b: agent_memory_threads columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'7B8D5C47-AA6E-5EF8-9041-A13CF5A39DDF',@TBL_THREADS,@T_UUID,N'key_guid',         1,0,1,0,N'NEWID()',          NULL),
(N'7F873C7E-94F4-5BB2-96B2-F2B8A5A672B0',@TBL_THREADS,@T_STR, N'pub_project',      2,0,0,0,NULL,               128),
(N'9ED235E7-5EEE-55FF-AD9D-6D364DA7E07E',@TBL_THREADS,@T_STR, N'pub_title',        3,0,0,0,NULL,               256),
(N'0E58F422-2E2B-5847-A303-3D69B7E37929',@TBL_THREADS,@T_TEXT,N'pub_summary',      4,1,0,0,NULL,               NULL),
(N'D50A9430-EB35-59C3-8901-CA9131A3C248',@TBL_THREADS,@T_BOOL,N'pub_is_active',    5,0,0,0,N'1',              NULL),
(N'BF120D58-4C66-51C2-86B5-7D67876D684B',@TBL_THREADS,@T_DTZ, N'priv_created_on',  6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'E180659A-8769-5D46-BC84-19E9ABF44A19',@TBL_THREADS,@T_DTZ, N'priv_modified_on', 7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- 2c: agent_memory_entries columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'13814960-BD02-5C7A-8FF7-2F49762C33B0',@TBL_ENTRIES,@T_UUID,N'key_guid',         1, 0,1,0,N'NEWID()',          NULL),
(N'EB1C1A9B-804A-52D7-8088-335DF7B0253A',@TBL_ENTRIES,@T_UUID,N'ref_thread_guid',  2, 1,0,0,NULL,               NULL),
(N'D325C874-B5BB-599C-AC8F-C9BD3E2D869F',@TBL_ENTRIES,@T_STR, N'pub_project',      3, 0,0,0,NULL,               128),
(N'9F1DB71C-51AD-533C-9B03-C7EA0D6F58C3',@TBL_ENTRIES,@T_STR, N'pub_kind',         4, 0,0,0,NULL,               32),
(N'9F14B04D-CF07-5460-A8E2-F8D6C100B4A7',@TBL_ENTRIES,@T_STR, N'pub_title',        5, 0,0,0,NULL,               256),
(N'3E8B7441-F24F-50AA-B2AE-447FD0DA2493',@TBL_ENTRIES,@T_TEXT,N'pub_body',         6, 0,0,0,NULL,               NULL),
(N'36B4A528-2CE5-5554-8C48-4788F717340D',@TBL_ENTRIES,@T_STR, N'pub_tags',         7, 1,0,0,NULL,               512),
(N'0F24D277-15B9-5E43-B41F-460AABD10D19',@TBL_ENTRIES,@T_STR, N'pub_source',       8, 1,0,0,NULL,               128),
(N'B39EA588-4DC6-55B8-9B17-FDB783B352CC',@TBL_ENTRIES,@T_BOOL,N'pub_is_active',    9, 0,0,0,N'1',              NULL),
(N'28979925-9170-5330-94B2-E7EAC9201B8B',@TBL_ENTRIES,@T_DTZ, N'priv_created_on',  10,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'89A94F84-7508-597B-BF41-A98B8BB79917',@TBL_ENTRIES,@T_DTZ, N'priv_modified_on', 11,0,0,0,N'SYSUTCDATETIME()',NULL);

-- 2d: agent_memory_entries indexes
INSERT INTO [dbo].[system_objects_database_indexes] ([key_guid],[ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'9149D106-03BE-526F-88C6-16AB5ED57120',@TBL_ENTRIES,N'IX_agent_memory_entries_project',N'pub_project,pub_is_active',0),
(N'33FE5B55-4EA4-5F41-A820-1D29A43C001A',@TBL_ENTRIES,N'IX_agent_memory_entries_kind',   N'pub_kind',                0),
(N'828AD68B-085E-5BF7-AC06-407D4EB61A8F',@TBL_ENTRIES,N'IX_agent_memory_entries_thread', N'ref_thread_guid',         0);

-- 2e: foreign key  agent_memory_entries.ref_thread_guid -> agent_memory_threads.key_guid
INSERT INTO [dbo].[system_objects_database_constraints] ([key_guid],[ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
(N'B1A524BE-ADC3-504E-A849-CFF55C0AB11D', @TBL_ENTRIES, @COL_ENTRIES_THREAD, @TBL_THREADS, @COL_THREADS_PK);
GO


-- ============================================================================
-- PHASE 3: Verification
-- ============================================================================

SELECT 'agent_memory_threads' AS [table], COUNT(*) AS [rows] FROM [dbo].[agent_memory_threads];
SELECT 'agent_memory_entries' AS [table], COUNT(*) AS [rows] FROM [dbo].[agent_memory_entries];

-- Reflection registration (should list both tables and all columns)
SELECT t.pub_schema, t.pub_name AS [table], c.pub_ordinal, c.pub_name AS [column],
       ty.pub_mssql_type, c.pub_is_nullable, c.pub_is_primary_key
FROM system_objects_database_tables t
JOIN system_objects_database_columns c ON c.ref_table_guid = t.key_guid
JOIN system_objects_types ty ON ty.key_guid = c.ref_type_guid
WHERE t.pub_name IN (N'agent_memory_threads', N'agent_memory_entries')
ORDER BY t.pub_name, c.pub_ordinal;
