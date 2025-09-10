#!/usr/bin/env python3
"""
Generic database migration framework.
"""

import os
import sqlite3
import sys
import json
import shutil
import glob
from typing import List, Tuple

class MigrationManager:
    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.migration_table = "applied_migrations"
        
    def init_migration_tracking(self):
        """Initialize the migration tracking table if it doesn't exist."""
        if not os.path.exists(self.db_path):
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create migration tracking table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing migration tracking: {e}")
            
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        if not os.path.exists(self.db_path):
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if migration tracking table exists
            cursor.execute('''SELECT name FROM sqlite_master 
                             WHERE type='table' AND name=?''', (self.migration_table,))
            table_exists = cursor.fetchone()
            
            if not table_exists:
                conn.close()
                return []
                
            cursor.execute(f'SELECT migration_name FROM {self.migration_table} ORDER BY id')
            migrations = [row[0] for row in cursor.fetchall()]
            conn.close()
            return migrations
        except Exception as e:
            print(f"Error getting applied migrations: {e}")
            return []
            
    def get_all_migrations(self) -> List[str]:
        """Get list of all available migrations."""
        try:
            migration_files = sorted(glob.glob(os.path.join(self.migrations_dir, '*.sql')))
            # Extract just the filename without path
            return [os.path.basename(f) for f in migration_files]
        except Exception as e:
            print(f"Error getting migration files: {e}")
            return []
            
    def get_pending_migrations(self) -> List[str]:
        """Get list of migrations that haven't been applied yet."""
        all_migrations = self.get_all_migrations()
        applied_migrations = self.get_applied_migrations()
        return [m for m in all_migrations if m not in applied_migrations]
        
    def create_backup(self, migration_name: str) -> bool:
        """Create a backup of the database file based on migration name."""
        if not os.path.exists(self.db_path):
            print(f"Database file {self.db_path} does not exist. Nothing to backup.")
            return True
            
        try:
            # Extract migration filename without extension
            migration_name_no_ext = os.path.splitext(migration_name)[0]
            # Create backup filename using migration name
            backup_path = f"{self.db_path.rsplit('.', 1)[0]}_{migration_name_no_ext}.db"
                
            print(f"Creating backup of database to {backup_path}...")
            shutil.copy2(self.db_path, backup_path)
            print("Backup created successfully!")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
            
    def mark_migration_applied(self, migration_name: str):
        """Mark a migration as applied in the tracking table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                INSERT OR IGNORE INTO {self.migration_table} (migration_name) 
                VALUES (?)
            ''', (migration_name,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error marking migration as applied: {e}")
            
    def apply_migration(self, migration_name: str) -> bool:
        """Apply a specific migration file."""
        migration_path = os.path.join(self.migrations_dir, migration_name)
        
        if not os.path.exists(migration_path):
            print(f"Migration file {migration_path} does not exist.")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print(f"Applying migration {migration_name}...")
            
            # Read and execute the migration SQL
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
                
            cursor.executescript(migration_sql)
            
            # Mark migration as applied
            self.mark_migration_applied(migration_name)
            
            print("Migration applied successfully!")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error applying migration {migration_name}: {e}")
            return False
            
    def apply_all_pending(self) -> bool:
        """Apply all pending migrations."""
        # Initialize migration tracking
        self.init_migration_tracking()
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            print(f"Database file {self.db_path} does not exist.")
            # This is fine - it will be created when first migration runs
            
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            print("No migrations pending. Database is up to date.")
            return True
            
        print(f"Found {len(pending_migrations)} pending migrations:")
        for migration in pending_migrations:
            print(f"  - {migration}")
            
        # Apply each pending migration
        for migration_name in pending_migrations:
            # Create backup before applying each migration
            if not self.create_backup(migration_name):
                print(f"Failed to create backup for {migration_name}. Aborting migration.")
                return False
            
            if not self.apply_migration(migration_name):
                print(f"Failed to apply migration {migration_name}!")
                return False
            else:
                print(f"Successfully applied migration {migration_name}")
                
        print("All migrations completed successfully!")
        return True

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

def main():
    """Main function to run the migration."""
    config = load_config()
    db_path = config['database']['path']
    
    print(f"Applying database migrations to: {db_path}")
    
    # Create migration manager
    manager = MigrationManager(db_path)
    
    # Apply all pending migrations
    if manager.apply_all_pending():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())