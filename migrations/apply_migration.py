#!/usr/bin/env python3
"""
Database migration script to add unique constraint and remove duplicates.
"""

import os
import sqlite3
import sys
import json
import shutil
import glob

def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "database": {
                "path": "data/tweets.db"
            }
        }

def create_backup(db_path, migration_file):
    """Create a backup of the database file based on migration filename."""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Nothing to backup.")
        return True
        
    try:
        # Extract migration filename without path and extension
        migration_name = os.path.splitext(os.path.basename(migration_file))[0]
        # Create backup filename using migration name
        backup_path = f"{db_path.rsplit('.', 1)[0]}_{migration_name}.db"
            
        print(f"Creating backup of database to {backup_path}...")
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully!")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def get_pending_migrations(db_path):
    """Get list of migration files that have not been applied yet."""
    # For now, we'll check if the unique constraint exists to determine if migration is needed
    # In a more sophisticated system, we would track applied migrations in a separate table
    
    if not os.path.exists(db_path):
        # If database doesn't exist, all migrations are pending
        migration_files = sorted(glob.glob('migrations/*.sql'))
        return migration_files
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the tweets table exists
        cursor.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='tweets' ''')
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # If table doesn't exist, all migrations are pending
            migration_files = sorted(glob.glob('migrations/*.sql'))
            conn.close()
            return migration_files
            
        # Check if unique constraint already exists
        cursor.execute('''PRAGMA table_info(tweets)''')
        columns = [column[1] for column in cursor.fetchall()]
        
        # Check if we have the new schema (unique constraint)
        # We'll check if we have the unique constraint by trying to insert a duplicate
        try:
            # Try to create a test duplicate (this will fail if constraint exists)
            cursor.execute("SELECT user_name, link_to_tweet, text FROM tweets LIMIT 1")
            row = cursor.fetchone()
            if row:
                user_name, link_to_tweet, text = row
                # Try inserting the same row again
                cursor.execute('''INSERT OR IGNORE INTO tweets 
                                 (user_name, link_to_tweet, created_at, text) 
                                 VALUES (?, ?, ?, ?)''',
                              (user_name, link_to_tweet, "test", text))
                if cursor.rowcount == 0:
                    # Unique constraint exists, no migrations needed
                    conn.close()
                    return []
                else:
                    # Rollback the test insert
                    conn.rollback()
        except sqlite3.Error:
            pass  # Continue with migration
            
        conn.close()
        
        # If we get here, the migration is needed
        migration_files = sorted(glob.glob('migrations/*.sql'))
        return migration_files
        
    except Exception as e:
        print(f"Error checking migration status: {e}")
        # Default to all migrations if we can't determine status
        return sorted(glob.glob('migrations/*.sql'))

def apply_migration(db_path, migration_file):
    """Apply a specific migration file."""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Nothing to migrate.")
        return True
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Applying migration {migration_file}...")
        
        # Apply the migration
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
            
        cursor.executescript(migration_sql)
        
        print("Migration applied successfully!")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error applying migration {migration_file}: {e}")
        return False

def main():
    """Main function to run the migration."""
    config = load_config()
    db_path = config['database']['path']
    
    print(f"Checking database migration status for: {db_path}")
    
    # Get pending migrations
    pending_migrations = get_pending_migrations(db_path)
    
    if not pending_migrations:
        print("No migrations pending. Database is up to date.")
        return 0
    
    print(f"Found {len(pending_migrations)} pending migrations:")
    for migration in pending_migrations:
        print(f"  - {migration}")
    
    # Apply each pending migration
    for migration_file in pending_migrations:
        # Create backup before applying each migration
        if not create_backup(db_path, migration_file):
            print(f"Failed to create backup for {migration_file}. Aborting migration.")
            return 1
        
        if not apply_migration(db_path, migration_file):
            print(f"Failed to apply migration {migration_file}!")
            return 1
        else:
            print(f"Successfully applied migration {migration_file}")
    
    print("All migrations completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())