CREATE TABLE IF NOT EXISTS auth_provider (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  guid UUID PRIMARY KEY,
  microsoft_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  username TEXT NOT NULL,
  backup_email TEXT,
  credits INT DEFAULT 0,
  default_provider INTEGER REFERENCES auth_provider(id),
  security INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS routes (
  id SERIAL PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  icon TEXT,
  security INT NOT NULL DEFAULT 0,
  sequence INT NOT NULL DEFAULT 0
);
