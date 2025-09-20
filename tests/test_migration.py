#!/usr/bin/env python3
"""
Test script to verify migration functionality.
"""

import os
import sqlite3
import sys
import tempfile
import shutil

def test_migration():
    """Test the migration functionality."""
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, 'test.db')
    
    try:
        # Create a test database with duplicates
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create table without unique constraint
        c.execute('''CREATE TABLE tweets
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_name TEXT,
                      link_to_tweet TEXT,
                      created_at TEXT,
                      created_at_parsed TIMESTAMP,
                      text TEXT,
                      received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insert some duplicate tweets
        tweets_data = [
            ('user1', 'link1', '2025-01-01', '2025-01-01 10:00:00', 'text1'),
            ('user1', 'link1', '2025-01-01', '2025-01-01 10:00:00', 'text1'),  # duplicate
            ('user2', 'link2', '2025-01-02', '2025-01-02 11:00:00', 'text2'),
            ('user1', 'link1', '2025-01-01', '2025-01-01 10:00:00', 'text1'),  # duplicate
            ('user3', 'link3', '2025-01-03', '2025-01-03 12:00:00', 'text3'),
        ]
        
        for tweet in tweets_data:
            c.execute('''INSERT INTO tweets 
                         (user_name, link_to_tweet, created_at, created_at_parsed, text)
                         VALUES (?, ?, ?, ?, ?)''', tweet)
        
        conn.commit()
        
        # Count initial tweets
        c.execute('SELECT COUNT(*) FROM tweets')
        initial_count = c.fetchone()[0]
        print(f"Initial tweet count: {initial_count}")
        
        # Close connection
        conn.close()
        
        # Copy migration script to test directory
        migrations_dir = os.path.join(test_dir, 'migrations')
        os.makedirs(migrations_dir)
        migration_script = os.path.join(migrations_dir, '001_add_unique_constraint.sql')
        shutil.copy('migrations/001_add_unique_constraint.sql', migration_script)
        
        # Apply migration
        conn = sqlite3.connect(db_path)
        with open(migration_script, 'r') as f:
            migration_sql = f.read()
            
        conn.executescript(migration_sql)
        conn.commit()
        conn.close()
        
        # Check final count
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM tweets')
        final_count = c.fetchone()[0]
        print(f"Final tweet count: {final_count}")
        
        # Check for duplicates
        c.execute('''SELECT user_name, link_to_tweet, text, COUNT(*) 
                     FROM tweets 
                     GROUP BY user_name, link_to_tweet, text 
                     HAVING COUNT(*) > 1''')
        duplicates = c.fetchall()
        print(f"Duplicates found: {len(duplicates)}")
        
        conn.close()
        
        # Verify results
        if final_count == 3 and len(duplicates) == 0:
            print("Migration test PASSED")
            return True
        else:
            print("Migration test FAILED")
            return False
            
    except Exception as e:
        print(f"Migration test ERROR: {e}")
        return False
    finally:
        # Clean up
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    success = test_migration()
    sys.exit(0 if success else 1)