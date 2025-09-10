#!/usr/bin/env python3
"""
Database migration script to add unique constraint and remove duplicates.
"""

import os
import sqlite3
import sys

def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config/config.json', 'r') as f:
            import json
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "database": {
                "path": "data/tweets.db"
            }
        }

def apply_migration(db_path):
    """Apply the migration to add unique constraint and remove duplicates."""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Nothing to migrate.")
        return True
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the tweets table exists
        cursor.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='tweets' ''')
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Tweets table does not exist. Nothing to migrate.")
            conn.close()
            return True
            
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
                    print("Unique constraint already exists. Migration not needed.")
                    conn.close()
                    return True
                else:
                    # Rollback the test insert
                    conn.rollback()
        except sqlite3.Error:
            pass  # Continue with migration
            
        print("Applying migration to add unique constraint and remove duplicates...")
        
        # Count duplicates before migration
        cursor.execute('''
            SELECT COUNT(*) - COUNT(DISTINCT user_name || link_to_tweet || text) AS duplicate_count
            FROM tweets
        ''')
        duplicate_count = cursor.fetchone()[0]
        print(f"Found {duplicate_count} duplicate tweets to remove.")
        
        # Apply the migration
        with open('migrations/001_add_unique_constraint.sql', 'r') as f:
            migration_sql = f.read()
            
        cursor.executescript(migration_sql)
        
        print("Migration applied successfully!")
        print(f"Removed {duplicate_count} duplicate tweets.")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error applying migration: {e}")
        return False

def main():
    """Main function to run the migration."""
    config = load_config()
    db_path = config['database']['path']
    
    print(f"Applying database migration to: {db_path}")
    
    if apply_migration(db_path):
        print("Migration completed successfully!")
        return 0
    else:
        print("Migration failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())