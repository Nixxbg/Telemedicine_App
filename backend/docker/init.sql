-- Initial database setup for telemedicine application
-- This file is executed when the PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database if it doesn't exist (though docker-compose should handle this)
-- The database is created by the POSTGRES_DB environment variable

-- Set up any initial data or configurations here
-- For now, we'll keep it minimal and let Alembic handle schema creation
