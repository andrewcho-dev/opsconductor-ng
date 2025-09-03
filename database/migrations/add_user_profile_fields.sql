-- Migration: Add optional profile fields to users table
-- Date: 2024-01-XX
-- Description: Add first_name, last_name, telephone, and title columns to users table

-- Add the new columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS telephone TEXT,
ADD COLUMN IF NOT EXISTS title TEXT;

-- Create indexes for the new fields (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(first_name, last_name);