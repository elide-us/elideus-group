-- Primary users table
CREATE TABLE account_users (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_guid UNIQUEIDENTIFIER NOT NULL UNIQUE,
    element_rotkey NVARCHAR(MAX) NOT NULL,
    element_rotkey_iat DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    element_rotkey_exp DATETIMEOFFSET NOT NULL,
    element_email NVARCHAR(1024) NOT NULL,
    element_display NVARCHAR(1024) NOT NULL,
    providers_recid INT NULL,
    element_optin BIT NULL DEFAULT 0,
    FOREIGN KEY (providers_recid) REFERENCES auth_providers(recid)
);

-- This table just has keys for provider names (microsoft, discord, google, apple)
CREATE TABLE auth_providers (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_name NVARCHAR(1024) NOT NULL,
    element_display NVARCHAR(1024) NULL
);

-- The Elideus Group social links on the home page
CREATE TABLE frontend_links (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_sequence INT NOT NULL DEFAULT 0,
    element_title NVARCHAR(MAX),
    element_url NVARCHAR(MAX)
);

-- The React Routes that are used in the NavBar
CREATE TABLE frontend_routes (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_enablement NVARCHAR(1) NOT NULL DEFAULT '0',
    element_roles BIGINT NOT NULL DEFAULT 0,
    element_sequence INT NOT NULL DEFAULT 0,
    element_path NVARCHAR(512) NOT NULL,
    element_name NVARCHAR(256) NOT NULL,
    element_icon NVARCHAR(256) NULL
);

-- System configuration table
CREATE TABLE system_config (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_key NVARCHAR(1024) NULL,
    element_value NVARCHAR(MAX) NULL
);

-- This is the roles table, it has both the deprecated bit mask style and the new enablement mask style security
CREATE TABLE system_roles (
    recid INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    element_mask BIGINT NOT NULL DEFAULT 0,
    element_enablement NVARCHAR(1) NOT NULL DEFAULT '0',
    element_name NVARCHAR(1024) NOT NULL,
    element_display NVARCHAR(1024) NULL
);

-- Contains bearer tokens for API access
CREATE TABLE users_apitokens (
    element_guid UNIQUEIDENTIFIER PRIMARY KEY,
    users_guid UNIQUEIDENTIFIER NOT NULL,
    element_token NVARCHAR(MAX) NOT NULL,
    element_token_iat DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    element_token_exp DATETIMEOFFSET NOT NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid),
    UNIQUE (users_guid)
);

-- Contains the unique identifiers supplied by the OAuth provider
CREATE TABLE users_auth (
    recid INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    users_guid UNIQUEIDENTIFIER NOT NULL,
    providers_recid INT NOT NULL,
    element_identifier UNIQUEIDENTIFIER NOT NULL UNIQUE,
    FOREIGN KEY (providers_recid) REFERENCES auth_providers(recid),
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

-- This is to include also a FK to task_guid in system_tasks
CREATE TABLE users_credits (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_credits INT NOT NULL,
    element_reserve INT NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

-- Future role unicode mask system
CREATE TABLE users_enablements (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_enablements NVARCHAR(MAX) NOT NULL DEFAULT '0',
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

-- Contains the profile image in base64 supplied by the OAuth provider
CREATE TABLE users_profileimg (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_base64 NVARCHAR(MAX) NOT NULL,
    providers_recid INT NOT NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid),
    FOREIGN KEY (providers_recid) REFERENCES auth_providers(recid)
);

-- Current role bit mask system, DEPRECATED
CREATE TABLE users_roles (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_roles BIGINT NOT NULL DEFAULT 0,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

-- Tracks active user sessions
CREATE TABLE users_sessions (
    element_guid UNIQUEIDENTIFIER PRIMARY KEY,
    users_guid UNIQUEIDENTIFIER NOT NULL,
    element_created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

-- Tracks device tokens associated with sessions
CREATE TABLE sessions_devices (
    element_guid UNIQUEIDENTIFIER PRIMARY KEY,
    sessions_guid UNIQUEIDENTIFIER NOT NULL,
    element_token NVARCHAR(MAX) NOT NULL,
    element_token_iat DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    element_token_exp DATETIMEOFFSET NOT NULL,
    element_device_fingerprint NVARCHAR(512) NULL,
    element_user_agent NVARCHAR(1024) NULL,
    element_ip_last_seen NVARCHAR(64) NULL,
    element_revoked_at DATETIMEOFFSET NULL,
    FOREIGN KEY (sessions_guid) REFERENCES users_sessions(element_guid),
    UNIQUE (sessions_guid)
);

