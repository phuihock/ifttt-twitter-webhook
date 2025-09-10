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

Or use the shell script:

```bash
./migrate.sh
```

Both scripts will:
1. Check which migrations have not yet been applied
2. Create a backup of the database before applying each migration
3. Apply pending migrations
4. Report the results

## Backup Process

Before applying each migration, a backup of the original database file is automatically created:

- Original file: `data/tweets.db`
- Backup file: `data/tweets_<migration_filename>.db` (e.g., `data/tweets_001_add_unique_constraint.db`)

The backup preserves the exact state of the database before each migration, allowing for easy rollback if needed.

## How It Works

The migration system works as follows:

1. Checks which migrations have not yet been applied
2. For each pending migration:
   - Creates a backup named after the migration file
   - Applies the migration SQL script
3. Uses SQLite's transaction support to ensure data integrity

## Benefits

1. **Prevents Race Conditions**: The UNIQUE constraint prevents duplicate tweets even with concurrent requests
2. **Data Cleanup**: Automatically removes existing duplicates
3. **Performance**: Adds indexes for faster queries
4. **Reliability**: Uses database transactions to ensure data integrity
5. **Safety**: Creates automatic backups before applying changes
6. **Recovery**: Easy rollback through backup files if needed
7. **Dynamic Naming**: Backup files are named after the migration being applied

## Manual Backup Restoration

If you need to restore from a backup:

1. Stop the application
2. Copy the backup file to the original location:
   ```bash
   cp data/tweets_001_add_unique_constraint.db data/tweets.db
   ```
3. Restart the application