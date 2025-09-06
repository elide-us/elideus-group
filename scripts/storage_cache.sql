/****** Object:  Table [dbo].[storage_types] ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[storage_types](
  [recid] [int] IDENTITY(1,1) NOT NULL,
  [element_mimetype] [varchar](128) NOT NULL,
  [element_displaytype] [varchar](64) NOT NULL,
PRIMARY KEY CLUSTERED ([recid] ASC),
UNIQUE NONCLUSTERED ([element_mimetype] ASC)
);
GO

INSERT INTO [dbo].[storage_types] (element_mimetype, element_displaytype) VALUES
('application/octet-stream', 'Binary'),
('text/plain',               'Text'),
('text/markdown',            'Text'),
('application/json',         'Data'),
('application/pdf',          'Document'),
('image/png',                'Image'),
('image/jpeg',               'Image'),
('image/gif',                'Image'),
('image/webp',               'Image'),
('video/mp4',                'Video'),
('video/webm',               'Video'),
('audio/mpeg',               'Audio'),
('audio/wav',                'Audio'),
('audio/ogg',                'Audio'),
('audio/flac',               'Audio');
GO

/****** Object:  Table [dbo].[users_storage_cache] ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[users_storage_cache](
  [recid] [bigint] IDENTITY(1,1) NOT NULL,
  [users_guid] [uniqueidentifier] NOT NULL,
  [types_recid] [int] NOT NULL,
  [element_path] [nvarchar](512) NOT NULL,
  [element_filename] [nvarchar](255) NOT NULL,
  [element_public] [bit] NOT NULL CONSTRAINT DF_users_storage_cache_public DEFAULT ((0)),
  [element_created_on] [datetime2](3) NOT NULL CONSTRAINT DF_users_storage_cache_created DEFAULT (sysutcdatetime()),
  [element_modified_on] [datetime2](3) NULL,
  [element_deleted] [bit] NOT NULL CONSTRAINT DF_users_storage_cache_deleted DEFAULT ((0)),
  CONSTRAINT [PK_users_storage_cache] PRIMARY KEY CLUSTERED ([recid] ASC),
  CONSTRAINT [UQ_users_storage_cache] UNIQUE NONCLUSTERED ([users_guid] ASC, [element_path] ASC, [element_filename] ASC),
  CONSTRAINT [FK_users_storage_cache_users] FOREIGN KEY([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]),
  CONSTRAINT [FK_users_storage_types] FOREIGN KEY([types_recid]) REFERENCES [dbo].[storage_types] ([recid])
);
GO
