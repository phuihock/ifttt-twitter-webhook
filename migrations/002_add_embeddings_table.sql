-- Migration script to add embeddings table for semantic search
-- This script should be run on existing databases to upgrade them

-- Add migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS applied_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    tweet_id INTEGER PRIMARY KEY,
    embedding BLOB,
    FOREIGN KEY (tweet_id) REFERENCES tweets (id) ON DELETE CASCADE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_tweet_id ON embeddings(tweet_id);