# Database Migrations

This directory contains database migration scripts to upgrade the schema and clean up existing data.

## Migration Framework

The migration system is a generic framework that works similarly to SQLAlchemy/Alembic:

1. **Migration Tracking**: Applied migrations are tracked in a database table
2. **Automatic Detection**: System automatically detects which migrations need to be applied
3. **Ordered Execution**: Migrations are applied in filename order (numerical prefix)
4. **Backup Creation**: Each migration creates a backup before being applied
5. **Idempotent**: Safe to run multiple times - only pending migrations are applied

## Migration Scripts

### 001_add_unique_constraint.sql

This migration script:

1. Detects and removes existing duplicate tweets, keeping only the one with the smallest ID
2. Adds a UNIQUE constraint on the combination of `user_name`, `link_to_tweet`, and `text` columns
3. Creates indexes for better query performance

### 002_add_indexes_and_metadata.sql

This migration script:

1. Adds additional indexes for better search performance
2. Adds a metadata column for future extensibility

### apply_migration.py

Python script that implements the generic migration framework.

## Applying Migrations

To apply all pending migrations, run:

```bash
python migrations/apply_migration.py
```

Or use the shell script:

```bash
./migrate.sh
```

The system will:
1. Check which migrations have been applied (using the `applied_migrations` table)
2. Identify pending migrations (those not yet applied)
3. For each pending migration:
   - Create a backup of the database named after the migration
   - Apply the migration
4. Report the results

## Backup Process

Before applying each migration, a backup of the original database file is automatically created:

- Original file: `data/tweets.db`
- Backup file: `data/tweets_<migration_filename_without_extension>.db`
  - Example: Migration `001_add_unique_constraint.sql` creates backup `tweets_001_add_unique_constraint.db`

The backup preserves the exact state of the database before each migration, allowing for easy rollback if needed.

## How It Works

The migration system works as follows:

1. **Initialization**: Creates `applied_migrations` table to track which migrations have been run
2. **Detection**: Compares files in `migrations/` directory with entries in `applied_migrations` table
3. **Execution**: Applies pending migrations in alphabetical order
4. **Tracking**: Records each applied migration in the `applied_migrations` table
5. **Backup**: Creates a backup before each migration is applied

## Adding New Migrations

To add a new migration:

1. Create a new SQL file in the `migrations/` directory
2. Use a numerical prefix to ensure proper ordering (e.g., `003_add_user_table.sql`)
3. Write your migration SQL
4. Run the migration script to apply it

Example migration file (`003_add_user_table.sql`):
```sql
-- Add users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Benefits

1. **Extensible**: Easy to add new migrations
2. **Safe**: Each migration creates a backup
3. **Trackable**: Applied migrations are recorded in the database
4. **Idempotent**: Safe to run multiple times
5. **Ordered**: Migrations are applied in a consistent order
6. **Generic**: Framework can handle any SQL migration
7. **Future-Proof**: Ready for additional migrations

## Manual Backup Restoration

If you need to restore from a backup:

1. Stop the application
2. Copy the backup file to the original location:
   ```bash
   cp data/tweets_001_add_unique_constraint.db data/tweets.db
   ```
3. Restart the application