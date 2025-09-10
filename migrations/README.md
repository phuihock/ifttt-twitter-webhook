# Database Migrations

This directory contains database migration scripts to upgrade the schema and clean up existing data.

## Migration Scripts

### 001_add_unique_constraint.sql

This migration script:

1. Detects and removes existing duplicate tweets, keeping only the one with the smallest ID
2. Adds a UNIQUE constraint on the combination of `user_name`, `link_to_tweet`, and `text` columns
3. Creates indexes for better query performance

### apply_migration.py

Python script to apply the database migration.

## Applying Migrations

To apply the migration, run:

```bash
python migrations/apply_migration.py
```

This script will:
1. Check if the database exists
2. Check if the migration is needed
3. Apply the migration if needed
4. Report the number of duplicates removed

## How It Works

The migration uses SQLite's transaction support to ensure data integrity:

1. It begins a transaction
2. Removes duplicates by keeping only the row with the smallest ID for each unique combination
3. Creates a new table with the UNIQUE constraint
4. Copies data from the old table to the new table
5. Drops the old table
6. Renames the new table to the original name
7. Commits the transaction

## Benefits

1. **Prevents Race Conditions**: The UNIQUE constraint prevents duplicate tweets even with concurrent requests
2. **Data Cleanup**: Automatically removes existing duplicates
3. **Performance**: Adds indexes for faster queries
4. **Reliability**: Uses database transactions to ensure data integrity