-- Initialize Quenty Database
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if not exists (already handled by POSTGRES_DB)
-- CREATE DATABASE IF NOT EXISTS quenty_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types for enums
DO $$ BEGIN
    CREATE TYPE customer_type AS ENUM ('pequeño', 'mediano', 'grande');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE order_status AS ENUM ('pending', 'quoted', 'confirmed', 'with_guide', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE service_type AS ENUM ('national', 'international');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guide_status AS ENUM ('generated', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'returned', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can prepare some basic ones

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Set timezone
SET timezone = 'America/Bogota';