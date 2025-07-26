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
    required_roles BIGINT NOT NULL DEFAULT 0,
    element_sequence INT NOT NULL DEFAULT 0,
    element_path NVARCHAR(MAX) NOT NULL,
    element_name NVARCHAR(MAX) NOT NULL,
    element_icon NVARCHAR(MAX) NULL
);

-- System configuration table
CREATE TABLE system_config (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_key NVARCHAR(MAX) NULL,
    element_value NVARCHAR(MAX) NULL
);

-- This table just has keys for provider names (microsoft, discord, google, apple)
CREATE TABLE auth_providers (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_name NVARCHAR(MAX) NOT NULL,
    element_display NVARCHAR(MAX) NULL
);

-- Primary users table
CREATE TABLE account_users (
    recid INT IDENTITY(1,1) PRIMARY KEY,
    element_guid UNIQUEIDENTIFIER NOT NULL UNIQUE,
    element_email NVARCHAR(MAX) NOT NULL,
    element_display NVARCHAR(MAX) NOT NULL,
    element_auth_provider INT NULL,
    element_optin BIT NULL DEFAULT 0,
    FOREIGN KEY (element_auth_provider) REFERENCES auth_providers(recid)
);

CREATE TABLE users_profileimg (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_base64 NVARCHAR(MAX) NOT NULL,
    element_provider INT NOT NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid),
    FOREIGN KEY (element_provider) REFERENCES auth_providers(recid)
);


CREATE TABLE system_roles (
    recid INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    element_mask BIGINT NOT NULL DEFAULT 0,
    element_name NVARCHAR(MAX) NOT NULL,
    element_display NVARCHAR(MAX) NULL
);

CREATE TABLE users_credits (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_credits INT NOT NULL,
    element_action NVARCHAR(MAX) NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

CREATE TABLE users_roles (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_roles BIGINT NOT NULL DEFAULT 0,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

CREATE TABLE users_enablements (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_enablements BIGINT NOT NULL DEFAULT 0,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid)
);

CREATE TABLE users_auth (
    users_guid UNIQUEIDENTIFIER PRIMARY KEY,
    element_provider INT NOT NULL,
    element_identifier NVARCHAR(MAX) NOT NULL,
    FOREIGN KEY (element_provider) REFERENCES auth_providers(recid)
);

CREATE TABLE users_sessions (
    element_guid UNIQUEIDENTIFIER PRIMARY KEY,
    users_guid UNIQUEIDENTIFIER NOT NULL,
    element_bearer_token NVARCHAR(MAX) NOT NULL,
    element_rotation_token NVARCHAR(MAX) NOT NULL,
    element_created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    element_expires_at DATETIMEOFFSET NOT NULL,
    FOREIGN KEY (users_guid) REFERENCES account_users(element_guid),
    UNIQUE (users_guid, element_guid)
);
