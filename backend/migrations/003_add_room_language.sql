-- Migration: Add language field to rooms table
-- Date: 2026-01-02
-- Description: Add language column to support multi-language games

-- Add language column with default value 'zh'
ALTER TABLE rooms ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'zh';

-- Verify the column was added successfully
SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms';
