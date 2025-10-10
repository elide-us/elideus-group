-- Proposal: track Discord guilds the bot has joined.
CREATE TABLE discord_guilds (
  recid bigint NOT NULL,
  element_guild_id nvarchar(32) NOT NULL,
  element_name nvarchar(256) NOT NULL,
  element_joined_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
  element_member_count int,
  element_owner_id nvarchar(32),
  element_region nvarchar(128),
  element_left_on datetimeoffset,
  element_notes nvarchar(1024),
  PRIMARY KEY (recid)
);
CREATE UNIQUE INDEX UQ_discord_guilds_element_guild_id ON discord_guilds (element_guild_id);
