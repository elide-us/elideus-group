CREATE TABLE discord_guilds (
  recid bigint IDENTITY(1,1) NOT NULL,
  element_guild_id nvarchar(64) NOT NULL,
  element_name nvarchar(256) NOT NULL,
  element_joined_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
  element_member_count int,
  element_owner_id nvarchar(64),
  element_region nvarchar(128),
  element_left_on datetimeoffset,
  element_notes nvarchar(MAX),
  PRIMARY KEY (recid)
);
GO
CREATE UNIQUE INDEX UQ__discord_guilds__guild_id ON discord_guilds (element_guild_id);
GO
