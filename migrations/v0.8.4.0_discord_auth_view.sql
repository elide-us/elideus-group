SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- v0.8.4.0 Discord Auth View
-- ============================================================================

CREATE VIEW [dbo].[vw_user_discord_security] AS
SELECT
  au.element_guid AS user_guid,
  ur.element_roles AS user_roles,
  ua.element_identifier AS discord_identifier,
  ap.element_name AS provider_name,
  ua.element_linked AS is_linked
FROM dbo.account_users AS au
JOIN dbo.users_roles AS ur ON au.element_guid = ur.users_guid
JOIN dbo.users_auth AS ua ON ua.users_guid = au.element_guid
JOIN dbo.auth_providers AS ap ON ap.recid = ua.providers_recid
WHERE ap.element_name = 'discord'
  AND ua.element_linked = 1;
GO
