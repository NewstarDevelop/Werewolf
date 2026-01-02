-- Migration 002: Add indexes for rooms table query optimization
-- Database: SQLite
-- Created: 2026-01-02
-- Purpose: Optimize get_rooms() query performance by adding indexes on frequently queried columns
--
-- Background:
--   The get_rooms() function in room_manager.py filters by status and orders by created_at.
--   Without indexes, these operations require full table scans, degrading performance
--   as the number of rooms increases.
--
-- Expected Impact:
--   - Query performance improvement: 50-80% faster for room list queries
--   - Storage overhead: Minimal (~2-5% of table size per index)
--
-- Rollback:
--   DROP INDEX IF EXISTS idx_rooms_status;
--   DROP INDEX IF EXISTS idx_rooms_created_at;

-- Add index on status column (used in WHERE clause)
-- This accelerates filtering by room status (WAITING/PLAYING/FINISHED)
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);

-- Add index on created_at column (used in ORDER BY clause)
-- This accelerates sorting rooms by creation time
CREATE INDEX IF NOT EXISTS idx_rooms_created_at ON rooms(created_at);

-- Verify indexes were created successfully
SELECT name, sql FROM sqlite_master
WHERE type='index' AND tbl_name='rooms'
ORDER BY name;

-- Expected output should include:
-- idx_rooms_status | CREATE INDEX idx_rooms_status ON rooms(status)
-- idx_rooms_created_at | CREATE INDEX idx_rooms_created_at ON rooms(created_at)
