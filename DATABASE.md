# Database Overview

## Simple User Schema

The below statement illustrates a simple JOIN statement to get the entire view of a standard user, this will incude
their user account GUID as the unique internal identifier for the user, details about their selected authentication 
provider, their credits, security roles, and session/device details and tokens.

SELECT * FROM account_users au
JOIN users_sessions us ON au.element_guid = us.users_guid
JOIN users_auth ua ON au.element_guid = ua.users_guid
JOIN users_credits uc ON au.element_guid = uc.users_guid
JOIN users_roles ur ON au.element_guid = ur.users_guid
JOIN users_profileimg up ON au.element_guid = up.users_guid
JOIN auth_providers ap ON au.providers_recid = ap.recid
JOIN sessions_devices sd ON us.element_guid = sd.sessions_guid

The above materialized view would result in a row that looks like this:

recid	element_guid	element_rotkey	element_rotkey_iat	element_rotkey_exp	element_email	element_display	providers_recid	element_optin	element_guid	users_guid	element_created_at	recid	users_guid	providers_recid	element_identifier	users_guid	element_credits	element_reserve	users_guid	element_roles	users_guid	element_base64	providers_recid	recid	element_name	element_display	element_guid	sessions_guid	element_token	element_token_iat	element_token_exp	element_device_fingerprint	element_user_agent	element_ip_last_seen	element_revoked_at


2	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	<ROTATION TOKEN>	2025-08-17 18:08:54.2495610 +00:00	2025-11-15 18:08:54.2494240 +00:00	aaron@elideus.net	Aaron Stackpole	1	0	8FAE009D-3592-4721-A887-9E034B1F60FA	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	2025-08-17 18:08:53.5314685 +00:00	1	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	1	00000000-0000-0000-12ea-852a20ad51ae	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	4999890	NULL	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	8935141660703064191	92ACBA93-E0B9-4D41-A7B4-6A0418DB4B47	BASE64ENCODEDIMG	1	1	microsoft	Microsoft	31E0EC77-00B2-4BD3-A21E-735D1F1A6567	8FAE009D-3592-4721-A887-9E034B1F60FA	<BEARER TOKEN>	2025-08-17 18:08:53.6252199 +00:00	2025-08-17 18:23:54.4412460 +00:00	NULL	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0	127.0.0.1	NULL

The following views simplify this table structure:

```
CREATE VIEW vw_account_user_profile AS
SELECT
    au.element_guid         AS user_guid,
    au.element_email        AS email,
    au.element_display      AS display_name,
    ap.element_name         AS provider_name,
    ap.element_display      AS provider_display,
    up.element_base64       AS profile_image_base64,
    au.element_optin        AS opt_in,
    uc.element_credits      AS credits
FROM account_users AS au
JOIN auth_providers AS ap ON au.providers_recid = ap.recid
JOIN users_profileimg AS up ON au.element_guid = up.users_guid
JOIN users_credits AS uc ON au.element_guid = uc.users_guid;

CREATE VIEW vw_account_user_security AS
SELECT
    au.element_guid             AS user_guid,
    au.element_rotkey,
    au.element_rotkey_iat,
    au.element_rotkey_exp,
    us.element_guid             AS session_guid,
    sd.element_guid             AS device_guid,
    sd.element_token,
    sd.element_token_iat,
    sd.element_token_exp,
    sd.element_revoked_at,
    sd.element_device_fingerprint,
    sd.element_user_agent,
    sd.element_ip_last_seen
FROM account_users AS au
JOIN users_sessions AS us ON au.element_guid = us.users_guid
JOIN sessions_devices AS sd ON us.element_guid = sd.sessions_guid;
```

