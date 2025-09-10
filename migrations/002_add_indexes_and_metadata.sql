-- Migration script to add additional indexes for better performance
-- This is an example of a second migration that would run after the first one

BEGIN TRANSACTION;

-- Add additional indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_tweets_link_to_tweet ON tweets(link_to_tweet);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);

-- Add a new column for tweet metadata if it doesn't exist
ALTER TABLE tweets ADD COLUMN metadata TEXT;

COMMIT;