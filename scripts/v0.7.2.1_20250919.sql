CREATE VIEW vw_content_personas AS
SELECT
  ap.recid AS persona_recid,
  ap.element_name AS persona_name,
  ap.element_prompt AS persona_prompt,
  ap.element_tokens AS token_allowance,
  ap.models_recid,
  am.element_name AS model_name,
  ap.element_created_on,
  ap.element_modified_on
FROM dbo.assistant_personas AS ap
JOIN dbo.assistant_models AS am ON am.recid = ap.models_recid;

CREATE VIEW vw_content_conversations AS
SELECT
  ac.recid,
  ac.personas_recid,
  ap.element_name AS persona_name,
  ac.models_recid,
  am.element_name AS model_name,
  ac.element_guild_id,
  ac.element_channel_id,
  ac.element_user_id,
  ac.element_input,
  ac.element_output,
  ac.element_tokens,
  ac.element_created_on
FROM dbo.assistant_conversations AS ac
JOIN dbo.assistant_personas AS ap ON ap.recid = ac.personas_recid
JOIN dbo.assistant_models AS am ON am.recid = ac.models_recid;

CREATE VIEW vw_content_user_roles AS
SELECT
  au.element_guid AS user_guid,
  au.element_display AS display_name,
  ISNULL(ur.element_roles, 0) AS role_mask
FROM dbo.account_users AS au
LEFT JOIN dbo.users_roles AS ur ON ur.users_guid = au.element_guid;

CREATE VIEW vw_content_public_user_profiles AS
SELECT
  au.element_guid AS user_guid,
  au.element_display AS display_name,
  au.element_email AS email,
  au.element_optin AS email_opt_in,
  up.element_base64 AS profile_image_base64
FROM dbo.account_users AS au
LEFT JOIN dbo.users_profileimg AS up ON up.users_guid = au.element_guid;

CREATE VIEW vw_content_public_user_files AS
SELECT
  usc.recid,
  usc.users_guid AS user_guid,
  usc.element_path,
  usc.element_filename,
  usc.element_url,
  usc.element_public,
  usc.element_deleted,
  usc.element_reported,
  usc.element_created_on,
  usc.element_modified_on,
  usc.moderation_recid,
  st.element_mimetype AS content_type,
  st.element_displaytype AS content_display_type
FROM dbo.users_storage_cache AS usc
JOIN dbo.storage_types AS st ON st.recid = usc.types_recid;
