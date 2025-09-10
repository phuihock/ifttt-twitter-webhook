-- Migration script to add unique constraint and remove duplicates
-- This script should be run on existing databases to upgrade them

-- Add migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS applied_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

BEGIN TRANSACTION;

-- Step 1: Detect and remove existing duplicates, keeping only the one with the smallest id
DELETE FROM tweets 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM tweets 
    GROUP BY user_name, link_to_tweet, text
);

-- Step 2: Create new table with unique constraint
CREATE TABLE tweets_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    link_to_tweet TEXT,
    created_at TEXT,
    created_at_parsed TIMESTAMP,
    text TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_name, link_to_tweet, text)
);

-- Step 3: Copy data from old table to new table
INSERT INTO tweets_new 
    (id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at)
SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at
FROM tweets;

-- Step 4: Drop old table
DROP TABLE tweets;

-- Step 5: Rename new table to original name
ALTER TABLE tweets_new RENAME TO tweets;

-- Step 6: Add index for better performance on searches
CREATE INDEX IF NOT EXISTS idx_tweets_created_at_parsed ON tweets(created_at_parsed);
CREATE INDEX IF NOT EXISTS idx_tweets_user_name ON tweets(user_name);
CREATE INDEX IF NOT EXISTS idx_tweets_text ON tweets(text);

COMMIT;