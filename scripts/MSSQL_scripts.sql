-- SEE MATERIALIZED VIEW --
SELECT * FROM account_users au
JOIN users_sessions us ON au.element_guid = us.users_guid
JOIN users_auth ua ON au.element_guid = ua.users_guid
JOIN users_credits uc ON au.element_guid = uc.users_guid
JOIN users_roles ur ON au.element_guid = ur.users_guid
JOIN users_profileimg up ON au.element_guid = up.users_guid
JOIN auth_providers ap ON au.providers_recid = ap.recid
JOIN sessions_devices sd ON us.element_guid = sd.sessions_guid
JOIN auth_providers apd ON sd.providers_recid = apd.recid


-- DELETE JOINED RECORD --
DELETE FROM sessions_devices WHERE sessions_guid = ''
GO
DELETE FROM users_auth WHERE users_guid = ''
DELETE FROM users_credits WHERE users_guid = ''
DELETE FROM users_roles WHERE users_guid = ''
DELETE FROM users_sessions WHERE users_guid = ''
DELETE FROM users_profileimg WHERE users_guid = ''
GO
DELETE FROM account_users WHERE element_guid = ''


-- SEE RAW DATA --
SELECT * FROM account_users
SELECT * FROM users_auth
SELECT * FROM users_credits
SELECT * FROM users_profileimg
SELECT * FROM users_roles
SELECT * FROM users_sessions
SELECT * FROM sessions_devices


-- FAST  CLEANUP--
TRUNCATE TABLE users_auth
TRUNCATE TABLE users_credits
TRUNCATE TABLE users_roles
TRUNCATE TABLE users_sessions
TRUNCATE TABLE users_profileimg