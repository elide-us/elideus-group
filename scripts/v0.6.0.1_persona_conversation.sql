CREATE TABLE assistant_personas (
  recid INT IDENTITY(1,1) PRIMARY KEY,
  element_name NVARCHAR(256) NOT NULL,
  element_metadata NVARCHAR(MAX),
  element_created_on DATETIMEOFFSET DEFAULT sysutcdatetime() NOT NULL
);

CREATE TABLE assistant_conversations (
  recid BIGINT IDENTITY(1,1) PRIMARY KEY,
  personas_recid INT NOT NULL,
  element_guild_id NVARCHAR(64),
  element_channel_id NVARCHAR(64),
  element_input NVARCHAR(MAX),
  element_output NVARCHAR(MAX),
  element_created_on DATETIMEOFFSET DEFAULT sysutcdatetime() NOT NULL,
  FOREIGN KEY (personas_recid) REFERENCES assistant_personas(recid)
);

CREATE INDEX IX_assistant_conversations_persona_time
  ON assistant_conversations (personas_recid, element_created_on);
