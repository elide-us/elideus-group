SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

CREATE TABLE [dbo].[account_api_tokens] (
  [element_token] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
  [users_recid] BIGINT NOT NULL,
  [element_label] NVARCHAR(256) NOT NULL,
  [element_roles] BIGINT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_expires_on] datetimeoffset(7) NULL,
  CONSTRAINT [PK_account_api_tokens] PRIMARY KEY ([element_token]),
  CONSTRAINT [FK_account_api_tokens_users] FOREIGN KEY ([users_recid])
    REFERENCES [dbo].[account_users] ([recid])
);
