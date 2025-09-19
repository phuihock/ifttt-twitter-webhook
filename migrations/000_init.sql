-- Initial migration script to create the tweets table with clean schema
-- This is the first migration that will be applied to create a fresh database

-- Add migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS applied_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

BEGIN TRANSACTION;

-- Create tweets table with clean schema
CREATE TABLE tweets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    link_to_tweet TEXT,
    created_at TEXT,
    created_at_parsed TIMESTAMP,
    text TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_name, link_to_tweet, text)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tweets_created_at_parsed ON tweets(created_at_parsed);
CREATE INDEX IF NOT EXISTS idx_tweets_user_name ON tweets(user_name);
CREATE INDEX IF NOT EXISTS idx_tweets_text ON tweets(text);
CREATE INDEX IF NOT EXISTS idx_tweets_link_to_tweet ON tweets(link_to_tweet);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);

COMMIT;