#!/usr/bin/env python3
"""
Script to restore tweets from CSV file to SQLite database.
This can be used to reinitialize the database from a backup.
"""

import sqlite3
import csv
import os
import sys
import json
from datetime import datetime

def load_config():
    """Load configuration from config.json file."""
    try:
        with open("config/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "database": {
                "path": "data/tweets.db"
            }
        }

def restore_tweets_from_csv(csv_path, db_path):
    """Restore tweets from CSV file to SQLite database."""
    try:
        # Check if CSV file exists
        if not os.path.exists(csv_path):
            print(f"CSV file {csv_path} does not exist.")
            return False
            
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                link_to_tweet TEXT,
                created_at TEXT,
                created_at_parsed TIMESTAMP,
                text TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_name, link_to_tweet, text)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created_at_parsed ON tweets(created_at_parsed)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_user_name ON tweets(user_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_text ON tweets(text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_link_to_tweet ON tweets(link_to_tweet)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at)")
        
        count = 0
        
        # Read from CSV
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header
            next(reader, None)
            
            # Insert data
            for row in reader:
                if len(row) >= 4:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO tweets 
                            (created_at, user_name, text, link_to_tweet)
                            VALUES (?, ?, ?, ?)
                        """, (row[0], row[1], row[2], row[3]))
                        count += 1
                    except sqlite3.IntegrityError:
                        # Skip duplicates
                        pass
                        
        conn.commit()
        conn.close()
        
        print(f"Successfully restored {count} tweets from {csv_path} to {db_path}")
        return True
        
    except Exception as e:
        print(f"Error restoring tweets from CSV: {e}")
        return False

def main():
    """Main function to run the restore script."""
    # Load configuration
    config = load_config()
    db_path = config['database']['path']
    
    # Default CSV path
    csv_path = "data/tweets_dump.csv"
    
    # Allow command line override
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    
    print(f"Restoring tweets from {csv_path} to {db_path}")
    
    if restore_tweets_from_csv(csv_path, db_path):
        print("Restore completed successfully!")
        return 0
    else:
        print("Restore failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())